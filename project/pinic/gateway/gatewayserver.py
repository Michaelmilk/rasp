# -*- coding: utf8 -*-

"""本Python模块含有Gateway的Web服务器部分。"""

__author__ = "tgmerge"


from gevent import monkey
monkey.patch_all()
import logging
from gevent.lock import BoundedSemaphore
from bottle import Bottle, request, HTTPResponse
from pinic.exception import ServerError
from pinic.gateway.gatewayconfig import parse_from_string as parse_gateway_config_from_string

logging.basicConfig(level=logging.DEBUG)


class GatewayServer(object):
    """
    Gateway的Web服务器。
    使用bottle作为Web服务器，用gevent作为HTTP服务器。
    """

    def __init__(self, gateway):
        """
        :param module.gateway.gateway.Gateway gateway: 包含这个GatewayServer的Gateway。
        """

        self.gateway = gateway
        self.gateway_lock = BoundedSemaphore(1)  # Lock of the Gateway instance
        self.bottle = Bottle()
        self.route()
        logging.debug("[GatewayServer.__init__] initialized, host=" + self.host + " port=" + str(self.port))
        self.bottle.run(host=self.gateway.config.gateway_host, port=self.gateway.config.gateway_port, server="gevent")

    def route(self):
        """配置URL路由。"""

        self.bottle.route("/gateway/gatewayconfig/<gateway_id>", method="POST", callback=self.http_post_gateway_config)
        self.bottle.route("/gateway/hubconfig/<gateway_id>/<hub_id>", method="POST", callback=self.http_post_hub_config)

        self.bottle.route("/gateway/gatewayconfig/<gateway_id>", method="GET", callback=self.http_get_gateway_config)
        self.bottle.route("/gateway/hubconfig/<gateway_id>/<hub_id>", method="GET", callback=self.http_get_hub_config)

        self.bottle.route("/gateway/sensordata", method="POST", callback=self.http_post_sensor_data)

    # ==================== Request callbacks

    def http_post_gateway_config(self, gateway_id):
        """
        处理POST gateway/gatewayconfig/(gateway_id)。
        如果处理失败，返回HTTP 500。如果成功，返回HTTP 200。

        :param basestring gateway_id: URL中的(gateway_id)部分
        """
        self.gateway_lock.acquire()
        try:
            self.update_gateway_config(gateway_id, request.body.read())
            response = self.get_gateway_config(gateway_id)
        except ServerError as e:
            from json import dumps
            response = HTTPResponse(status=500, body=dumps({
                "status": 500,
                "error": "Error on http_post_gateway_config.",
                "exception": str(e)
            }))
        self.gateway_lock.release()
        return response

    def http_get_gateway_config(self, gateway_id):
        """
        处理GET gateway/gatewayconfig/(gateway_id)。
        如果处理失败，返回HTTP 500。如果成功，返回HTTP 200。

        :param basestring gateway_id: URL中的(gateway_id)部分
        """
        self.gateway_lock.acquire()
        try:
            response = self.get_gateway_config(gateway_id)
        except ServerError as e:
            from json import dumps
            response = HTTPResponse(status=500, body=dumps({
                "status": 500,
                "error": "Error on http_get_gateway_config.",
                "exception": str(e)
            }))
        self.gateway_lock.release()
        return response

    def http_post_hub_config(self, gateway_id, hub_id):
        pass  # todo

    def http_get_hub_config(self, gateway_id, hub_id):
        pass  # todo

    def http_post_sensor_data(self):
        pass  # todo

    # ==================== Functional methods

    def update_gateway_config(self, gateway_id, post_data):
        """
        更新Gateway的配置，被http_post_gateway_config调用。
        如果更新失败，抛出ServerError异常。

        :param basestring gateway_id: URL中的(gateway_id)部分。需要被检查。
        :param basestring post_data: POST的内容，将被解析成GatewayConfig。
        """
        # 1. Check gateway_id
        if (self.gateway is None) or (gateway_id != self.gateway.config.gateway_id):
                raise ServerError("Cannot find gateway with gateway_id='%s'." % gateway_id)

        # 2. Try to parse incoming config string
        try:
            gateway_config = parse_gateway_config_from_string(post_data)
        except ValueError as e:
            raise ServerError("Exception on parsing json, no change applid to gateway.", e)

        # 3. Try to apply new config
        try:
            self.gateway.apply_config(gateway_config)
        except Exception as e:
            raise ServerError("CAUTION. Exception on applying config to gateway.", e)

        # 4. Success, return HTTP 200
        return

    def get_gateway_config(self, gateway_id):
        """
        获取Gateway的当前配置，被http_get_gateway_config调用。
        如果获取失败，抛出ServerError异常。

        :param basestring gateway_id: URL中的(gateway_id)部分，需要被检查。
        """
        # 1. Check gateway_id
        if (self.gateway is None) or (gateway_id != self.gateway.config.gateway_id):
            raise ServerError("Cannot find gateway with gateway_id='%s'." % gateway_id)

        # 2. Success, return HTTP 200 with config json
        return self.gateway.config.get_json_string()
