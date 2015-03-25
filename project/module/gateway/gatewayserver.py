# -*- coding: utf8 -*-

from bottle import Bottle, request, HTTPResponse
from gevent import monkey
import logging

logging.basicConfig(level=logging.DEBUG)

# Make gevent usable
monkey.patch_all()


class GatewayServer(object):
    def __init__(self, gateway, host, port):
        """
        :type gateway: gateway.Gateway
        :type host: str
        :type port: int
        """
        self.gateway = gateway
        """ :type: gateway.Gateway """

        self.bottle = Bottle()
        """ :type: Bottle """

        self.host = host
        """ :type: str """

        self.port = port
        """ :type: int """

        self.route()
        logging.debug("[GatewayServer.__init__] initialized, host=" + self.host + " port=" + str(self.port))
        self.bottle.run(host=self.host, port=self.port, server="gevent")

    def route(self):
        self.bottle.route("/gateway/gatewayconfig/<gateway_id>", method="POST", callback=self.post_gateway_config)
        self.bottle.route("/gateway/hubconfig/<hub_id>", method="POST", callback=self.post_hub_config)
        self.bottle.route("/gateway/gatewayconfig/<gateway_id>", method="GET", callback=self.get_gateway_config)
        self.bottle.route("/gateway/hubconfig/<hub_id>", method="GET", callback=self.get_hub_config)

        self.bottle.route("/gateway/sensordata", method="POST", callback=self.post_sensor_data)

    def post_gateway_config(self, gateway_id):
        pass  # todo

    def post_hub_config(self, hub_id):
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

    def get_hub_config(self, hub_id):
        pass  # todo

    def post_sensor_data(self):
        pass  # todo
