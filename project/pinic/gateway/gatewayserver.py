# -*- coding: utf8 -*-

"""本Python模块含有Gateway的Web服务器部分。"""

__author__ = "tgmerge"


from gevent import monkey
monkey.patch_all()
import pycurl
import logging
from gevent.lock import BoundedSemaphore
from bottle import Bottle, request, HTTPResponse
from pinic.exception import ServerError
from pinic.gateway.gatewayconfig import parse_from_string as parse_gateway_config_from_string
from pinic.sensor.sensordata import parse_from_string as parse_sensordata_from_string

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
        """
        处理POST /gateway/hubconfig/<gateway_id>/<hub_id>。
        如果失败，返回HTTP 500。如果成功，返回HTTP 200。

        :param basestring gateway_id: URL中的(gateway_id)部分
        :param basestring hub_id: URL中的(hub_id)部分
        """
        self.gateway_lock.acquire()
        try:
            response = self.send_hub_config(gateway_id, hub_id, request.body.read())
        except ServerError as e:
            from json import dumps
            response = HTTPResponse(status=500, body=dumps({
                "status": 500,
                "error": "Error on http_post_hub_config.",
                "exception": str(e)
            }))
        self.gateway_lock.release()
        return response

    def http_get_hub_config(self, gateway_id, hub_id):
        pass  # todo

    def http_post_sensor_data(self):
        """
        处理POST gateway/sensordata。
        如果成功，返回HTTP 200。如果失败，返回HTTP 500。
        """
        # TODO 加锁可以更细致一点
        self.gateway_lock.acquire()
        try:
            self.send_sensor_data(request.body.read())
            response = None
        except ServerError as e:
            from json import dumps
            response = HTTPResponse(status=500, body=dumps({
                "status": 500,
                "error": "Error on http_post_sensor_data.",
                "exception": str(e)
            }))
        self.gateway_lock.release()
        return response

    # ==================== Functional methods

    def send_hub_config(self, gateway_id, hub_id, post_data):
        """
        向Hub转发更新配置的请求。被http_post_hub_config调用，
        发出请求后，HTTP响应的内容将被原样转发回DataServer。
        如果失败，抛出ServerError异常。

        :param basestring gateway_id: URL中的(gateway_id)部分，将被检查。
        :param basestring hub_id: URL中的(hub_id)部分，将在当前Gateway的已知Hub中查找。
        :param basestring post_data: POST的内容，不处理并原样转发
        :rtype str
        返回从Hub收到的，对配置请求的响应。
        """
        # 1. Check gateway_id

        # 2. Find hub_id

        # 3. Send http request and wait for response
        # todo may block whole server?

        # 4. Return that http response
        return ""

    def send_sensor_data(self, post_data):
        """
        向DataServer转发传感器数据SensorData，被http_post_sensor_data调用。
        如果发送失败，抛出ServerError异常。

        :param basestring post_data: POST内容，将被解析成SensorData。
        """

        # 1. Try to parse incoming sensor data string
        try:
            sensor_data = parse_sensordata_from_string(post_data)
        except ValueError as e:
            raise ServerError("Exception on parsing SensorData.", e)

        # 2. Send the SensorData to DataServer, using method provided by gateway:
        # TODO may block the whole server? some test, maybe use async method.
        try:
            self.gateway.filter_and_send_sensor_data(sensor_data)
        except (TypeError, ServerError) as e:
            raise ServerError("Exception on sending sensor data.", e)

        # 3. Success, return 200
        return

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
