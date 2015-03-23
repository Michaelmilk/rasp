# -*- coding: utf8 -*-

from bottle import Bottle, request
from datetime import datetime
import hubconfig
import logging

logging.basicConfig(level=logging.DEBUG)



class HubServer(object):
    def __init__(self, hub, host, port):
        """
        :type hub: hub.Hub
        :type host: str
        :type port: int
        """
        self.hub = hub
        self.bottle = Bottle()
        self.host = "0.0.0.0"
        self.port = "8080"
        self.route()
        logging.debug("[HubApp.__init__] initialized, host=" + self.host + " port=" + self.port)
        self.bottle.run(host=self.host, port=self.port)

    def route(self):
        self.bottle.route("/hub/log", method="POST", callback=self.hub_log)
        self.bottle.route("/hub/config", method="POST", callback=self.hub_config)

    def hub_log(self):
        post_data = request.body.read()
        print "[/LOG]", str(datetime.now()), post_data

    def hub_config(self):
        post_data = request.body.read()
        try:
            hub_config = hubconfig.parse_from_string(post_data)
        except ValueError as e:
            logging.info("[HubApp._hub_config] exception on parsing json, do nothing. e=" + str(e))
            return
        self.hub.apply_config(hub_config)
