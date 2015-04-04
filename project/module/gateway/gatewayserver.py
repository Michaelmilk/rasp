# -*- coding: utf8 -*-

import logging
from gevent import monkey
from gevent.lock import BoundedSemaphore
from bottle import Bottle, request, HTTPResponse
from module.exception import ServerError
from module.gateway.gatewayconfig import parse_from_string as parse_gateway_from_string

monkey.patch_all()
logging.basicConfig(level=logging.DEBUG)


class GatewayServer(object):
    def __init__(self, gateway):
        """
        :type gateway: module.gateway.gateway.Gateway
        """
        self.gateway = gateway

        self.gateway_lock = BoundedSemaphore(1)  # Lock of the Gateway instance
        """ :type: BoundedSemaphore """

        self.bottle = Bottle()
        """ :type: Bottle """

        self.route()
        logging.debug("[GatewayServer.__init__] initialized, host=" + self.host + " port=" + str(self.port))
        self.bottle.run(host=self.gateway.config.gateway_host, port=self.gateway.config.gateway_port, server="gevent")

    def route(self):
        self.bottle.route("/gateway/gatewayconfig/<gateway_id>", method="POST", callback=self.post_gateway_config)
        self.bottle.route("/gateway/hubconfig/<gateway_id>/<hub_id>", method="POST", callback=self.post_hub_config)

        self.bottle.route("/gateway/gatewayconfig/<gateway_id>", method="GET", callback=self.get_gateway_config)
        self.bottle.route("/gateway/hubconfig/<gateway_id>/<hub_id>", method="GET", callback=self.get_hub_config)

        self.bottle.route("/gateway/sensordata", method="POST", callback=self.post_sensor_data)

    def post_gateway_config(self, gateway_id):
        if (self.gateway is None) or (gateway_id != self.gateway.config.gateway_id):
            # gateway_id is not corrent, return HTTP 500
            from json import dumps
            error_str = dumps({
                "status": 500,
                "error": "Cannot find gateway with gateway_id='%s'." % gateway_id
            })
            return HTTPResponse(status=500, body=error_str)

        try:
            post_data = request.body.read()
            gateway_config = gatewayconfig.parse_from_string(post_data)
        except ValueError as e:
            # parsing error, return HTTP 500
            from json import dumps
            error_str = dumps({
                "status": 500,
                "error": "Exception on parsing json, no change applid to gateway.",
                "exception": str(e)
            })
            logging.info("[GatewayServer.post_gateway_config] exception on parsing json, do nothing. e=" + str(e))
            return HTTPResponse(status=500, body=error_str)

        try:
            self.gateway.apply_config(gateway_config)
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

    def post_hub_config(self, gateway_id, hub_id):
        pass  # todo

    def get_gateway_config(self, gateway_id):
        if (self.gateway is None) or (gateway_id != self.gateway.config.gateway_id):
            # hub_id is not correct, return HTTP 500
            from json import dumps
            error_str = dumps({
                "status": 500,
                "error": "Cannot find gateway with gateway_id='%s'." % gateway_id
            })
            return HTTPResponse(status=500, body=error_str)

        return self.gateway.config.get_json_string()

    def get_hub_config(self, gateway_id, hub_id):
        pass  # todo

    def post_sensor_data(self):
        pass  # todo
