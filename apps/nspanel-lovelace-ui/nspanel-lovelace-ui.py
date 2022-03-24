import asyncio
import logging
import sys
import traceback
import uuid

import hassapi as hass

from luibackend.config import LuiBackendConfig
from luibackend.controller import LuiController
from luibackend.mqttListener import LuiMqttListener


LOGGER = logging.getLogger(__name__)


class AppDaemonLoggingHandler(logging.Handler):
    def __init__(self, app):
        super().__init__()
        self._app = app

    def emit(self, record):
        message = record.getMessage()
        if record.exc_info:
            message += '\nTraceback (most recent call last):\n'
            message += '\n'.join(traceback.format_tb(record.exc_info[2]))
            message += f'{record.exc_info[0].__name__}: {record.exc_info[1]}'
        self._app.log(message, level=record.levelname)


class NsPanelLovelaceUIManager(hass.Hass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._redirect_logging()

    def _redirect_logging(self):
        # Add a handler for the logging module that will convert the
        # calls to AppDaemon's logger with the self instance, so that
        # we can simply use logging in the rest of the application
        rlogger = logging.getLogger()
        rlogger.handlers = [
            h for h in rlogger.handlers
            if type(h).__name__ != AppDaemonLoggingHandler.__name__
        ]
        rlogger.addHandler(AppDaemonLoggingHandler(self))

        # We want to grab all the logs, AppDaemon will
        # then care about filtering those we asked for
        rlogger.setLevel(logging.DEBUG)



    def initialize(self):
        LOGGER.info('Starting')
        mqtt_api = self._mqtt_api = self.get_plugin_api("MQTT")
        cfg = self._cfg = LuiBackendConfig(self.args["config"])
        
        topic_send = cfg.get("panelSendTopic")
        def send_mqtt_msg(msg):
            LOGGER.info(f"Sending MQTT Message: {msg}")
            mqtt_api.mqtt_publish(topic_send, msg)

        controller = LuiController(self, cfg, send_mqtt_msg)

        topic_recv = cfg.get("panelRecvTopic")
        mqtt_listener = LuiMqttListener(mqtt_api, topic_recv, controller)

        



        LOGGER.info('Started')



