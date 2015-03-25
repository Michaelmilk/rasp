# -*- coding: utf8 -*-

import logging
from bottle import Bottle, request, HTTPResponse
from module.hub import hubconfig


logging.basicConfig(level=logging.DEBUG)


class HubServer(object):
    def __init__(self, hub, host, port):
        """
        :type hub: hub.Hub
        :type host: str
        :type port: int
        """
        self.hub = hub
        """ :type: hub.Hub """

        self.bottle = Bottle()
        """ :type: Bottle """

        self.host = host
        """ :type: str """

        self.port = port
        """ :type: int """

        self.route()
        logging.debug("[HubServer.__init__] initialized, host=" + self.host + " port=" + str(self.port))
        self.bottle.run(host=self.host, port=self.port)

    def route(self):
        self.bottle.route("/hub/hubconfig/<hub_id>", method="POST", callback=self.post_hub_config)
        self.bottle.route("/hub/hubconfig/<hub_id>", method="GET", callback=self.get_hub_config)

    def post_hub_config(self, hub_id):

        if (self.hub is None) or (hub_id != self.hub.config.hub_id):
            # hub_id is not correct, return HTTP 500
            from json import dumps
            error_str = dumps({
                "status": 500,
                "error": "Cannot find hub with hub_id='%s'." % hub_id
            })
            return HTTPResponse(status=500, body=error_str)

        try:
            post_data = request.body.read()
            hub_config = hubconfig.parse_from_string(post_data)
        except ValueError as e:
            # parsing error, return HTTP 500
            from json import dumps
            error_str = dumps({
                "status": 500,
                "error": "Exception on parsing json, no change applied to hub.",
                "exception": str(e)
            })
            logging.info("[HubApp._hub_config] exception on parsing json, do nothing. e=" + str(e))
            return HTTPResponse(status=500, body=error_str)

        try:
            self.hub.apply_config(hub_config)
        except Exception as e:
            # error on applying config, return HTTP 500
            from json import dumps
            error_str = dumps({
                "status": 500,
                "error": "CAUTION. Exception on applying config.",
                "exception": str(e)
            })
            return HTTPResponse(status=500, body=error_str)

        # Success, return HTTP 200
        return

    def get_hub_config(self, hub_id):

        if (self.hub is None) or (hub_id != self.hub.config.hub_id):
            # hub_id is not correct, return HTTP 500
            from json import dumps
            error_str = dumps({
                "status": 500,
                "error": "Cannot find hub with hub_id='%s'." % hub_id
            })
            return HTTPResponse(status=500, body=error_str)

        return self.hub.config.get_json_string()