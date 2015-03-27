# -*- coding: utf8 -*-

import logging
from gevent import monkey
from gevent.lock import BoundedSemaphore
from bottle import Bottle, request, HTTPResponse
from module.exception import ServerError
from module.hub.hubconfig import parse_from_string as parse_hub_config_from_string


monkey.patch_all()
logging.basicConfig(level=logging.DEBUG)


class HubServer(object):
    def __init__(self, hub):
        """
        :type hub: module.hub.hub.Hub
        """
        self.hub = hub

        self.hub_lock = BoundedSemaphore(1)  # Lock of the Hub instance
        """ :type: BoundedSemaphore """

        self.bottle = Bottle()
        """ :type: Bottle """

        self.route()
        logging.debug("[HubServer.__init__] initialized, host=" + self.hub.config.hub_host + " port=" + str(self.hub.config.hub_port))
        self.bottle.run(host=self.hub.config.hub_host, port=self.hub.config.hub_port, server="gevent")

    def route(self):
        self.bottle.route("/hub/hubconfig/<hub_id>", method="POST", callback=self.http_post_hub_config)
        self.bottle.route("/hub/hubconfig/<hub_id>", method="GET", callback=self.http_get_hub_config)

    def http_post_hub_config(self, hub_id):
        """
        Handle POST hub/hubconfig/(hub_id)
        :type hub_id: basestring
        """
        self.hub_lock.acquire()
        try:
            response = self.update_hub_config(hub_id, request.body.read())
        except ServerError as e:
            from json import dumps
            response = HTTPResponse(status=500, body=dumps({
                "status": 500,
                "error": "Error on http_post_hub_config.",
                "exception": str(e)
            }))
        self.hub_lock.release()
        return response

    def http_get_hub_config(self, hub_id):
        """
        Handle GET hub/hubconfig/(hub_id)
        :type hub_id: basestring
        """
        self.hub_lock.acquire()
        try:
            response = self.get_hub_config(hub_id)
        except ServerError as e:
            from json import dumps
            response = HTTPResponse(status=500, body=dumps({
                "status": 500,
                "error": "Error on http_get_hub_config.",
                "exception": str(e)
            }))
        self.hub_lock.release()
        return response

    def update_hub_config(self, hub_id, post_data):
        """
        :type hub_id: basestring
        """

        # 1. Check hub_id
        if (self.hub is None) or (hub_id != self.hub.config.hub_id):
            raise ServerError("Cannot find hub with hub_id='%s'." % hub_id)

        # 2. Try to parse incoming config string
        try:
            hub_config = parse_hub_config_from_string(post_data)
        except ValueError as e:
            raise ServerError("Exception on parsing json, no change applied to hub.", e)

        # 3. Try to apply new config
        try:
            self.hub.apply_config(hub_config)
        except Exception as e:
            raise ServerError("CAUTION. Exception on applying config.", e)

        # 4. Success, return HTTP 200
        return

    def get_hub_config(self, hub_id):
        """
        :type hub_id: basestring
        """

        # 1. Check hub_id
        if (self.hub is None) or (hub_id != self.hub.config.hub_id):
            raise ServerError("Cannot find hub with hub_id='%s'." % hub_id)

        # 2. Success, return HTTP 200 with config json
        return self.hub.config.get_json_string()
