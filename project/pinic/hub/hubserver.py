# -*- coding: utf8 -*-

"""本Python模块含有Hub的Web服务器部分。"""

__author__ = "tgmerge"


from gevent import monkey
monkey.patch_all()
import logging
from gevent.lock import BoundedSemaphore
from bottle import Bottle, request, HTTPResponse
from pinic.exception import ServerError
from pinic.hub.hubconfig import parse_from_string as parse_hub_config_from_string

logging.basicConfig(level=logging.DEBUG)


class HubServer(object):
    """
    Hub的Web服务器。
    使用bottle作为Web服务器，用gevent作为HTTP服务器。
    """

    def __init__(self, hub):
        """
        :param module.hub.hub.Hub hub: 包含这个HubServer的Hub。
        """

        self.hub = hub
        self.hub_lock = BoundedSemaphore(1)  # Lock of the Hub instance
        self.bottle = Bottle()
        self.route()
        logging.debug("[HubServer.__init__] initialized, host=" + self.hub.config.hub_host + " port=" + str(self.hub.config.hub_port))
        self.bottle.run(host=self.hub.config.hub_host, port=self.hub.config.hub_port, server="gevent")

    def route(self):
        """配置URL路由。"""

        self.bottle.route("/hub/hubconfig/<hub_id>", method="POST", callback=self.http_post_hub_config)
        self.bottle.route("/hub/hubconfig/<hub_id>", method="GET", callback=self.http_get_hub_config)

    def http_post_hub_config(self, hub_id):
        """
        处理POST hub/hubconfig/(hub_id)。
        如果处理失败，返回HTTP 500。如果成功，返回HTTP 200。

        :param basestring hub_id: URL中的(hub_id)部分
        """
        self.hub_lock.acquire()
        try:
            self.update_hub_config(hub_id, request.body.read())
            response = self.get_hub_config(hub_id)
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
        处理GET hub/hubconfig/(hub_id)。
        如果处理失败，返回HTTP 500。如果成功，返回HTTP 200。

        :param basestring hub_id: URL中的(hub_id)部分
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
        更新Hub的配置，被http_post_hub_config调用。
        如果更新失败，抛出ServerError异常。

        :param basestring hub_id: URL中的(hub_id)部分。需要被检查。
        :param basestring post_data: POST的内容，将被解析成HubConfig。
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
            raise ServerError("CAUTION. Exception on applying config to hub.", e)

        # 4. Success, return HTTP 200
        return

    def get_hub_config(self, hub_id):
        """
        获取Hub的当前配置，被http_get_hub_config调用。
        如果获取失败，抛出ServerError异常。

        :param basestring hub_id: URL中的(hub_id)部分，需要被检查。
        """
        # 1. Check hub_id
        if (self.hub is None) or (hub_id != self.hub.config.hub_id):
            raise ServerError("Cannot find hub with hub_id='%s'." % hub_id)

        # 2. Success, return HTTP 200 with config json
        return self.hub.config.get_json_string()
