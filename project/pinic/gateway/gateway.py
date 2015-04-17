# -*- coding: utf8 -*-

"""本Python模块是系统中Gateway的主要功能部分。"""

__author__ = "tgmerge"


import logging
import pycurl

from gatewayserver import GatewayServer
from pinic.gateway.gatewayconfig import GatewayConfig
from pinic.sensor.sensordata import SensorData
from pinic.exception import ServerError


logging.basicConfig(level=logging.DEBUG)


class Gateway(object):
    """Gateway对象包含一个GatewayServer，能更新配置，向上转发传感器数据，向下转发对Hub配置的操作。"""

    def __init__(self, gateway_config):
        """
        :param GatewayConfig gateway_config: 最初配置
        """

        logging.debug("[Gateway.__init__] gateway_config=" + str(gateway_config))

        self.old_config = None
        """ :type: GatewayConfig """

        self.config = None
        """ :type: GatewayConfig """

        self.apply_config(gateway_config)

        self.gateway_server = GatewayServer(self)

        self.curl = pycurl.Curl()

    def apply_config(self, gateway_config, load_old_config=False):
        """
        更新这个Gateway的配置。

        :param GatewayConfig gateway_config: 要载入的新配置
        :param bool load_old_config: 调用时无需设置。在载入失败时防止无限回滚使用。
        """
        logging.debug("[Gateway.apple_config] gateway_config=" + str(gateway_config) + "load_old_config=" + str(load_old_config))

        # 1. Some type check
        if not isinstance(gateway_config, GatewayConfig):
            raise TypeError("%s is not a GatewayConfig instance" % str(gateway_config))

        # 2. Replace config field
        self.old_config = self.config

        # 3. If new config has a different "gateway_host" or "gateway_port" from old one,
        # TODO run a shell script to start whole program using new config, because bottle cannot stop itself
        if (self.old_config is not None) and ((gateway_config.gateway_port != self.old_config.gateway_port) or (gateway_config.gateway_host != self.old_config.gateway_host)):
            self.restart_whole_server()

        # 3. Reset server. Actually does nothing...
        self.reset()

        # 4. Start new... Wait, does nothing
        self.config = gateway_config

    def reset(self):
        """初始化Hub。尚不需要进行多余的操作。"""
        pass

    def restart_whole_server(self):
        """停止整个解释器进程，调用一些脚本重启整个程序，以改变如服务器端口一类的配置。"""
        # TODO do something
        logging.warn("[Gateway.reload_whole_server] not implemented yet!")
        pass

    def filter_and_send_sensor_data(self, sensor_data):
        """
        使用配置中的规则过滤下层Hub传来的传感器数据。
        如果数据被过滤规则阻拦，则丢弃它。
        否则发送给上层的DataServer。

        :param SensorData sensor_data: 要处理的传感器数据
        """
        # 1. Some type check
        if not isinstance(sensor_data, SensorData):
            raise TypeError("sensor_data: %s is not a SensorData instance" % str(sensor_data))

        is_dropped = False

        # 2. Check value
        for data_filter in self.config.filters:
            # Check "apply_on_sensor_type"
            if (data_filter["apply_on_sensor_type"] != "*") and (data_filter["apply_on_sensor_type"] != sensor_data.sensor_type):
                continue

            # Check "apply_on_sensor_id"
            if (data_filter["apply_on_sensor_id"] != "*") and (data_filter["apply_on_sensor_id"] != sensor_data.sensor_id):
                continue

            # Check method and threshold
            if (data_filter["comparing_method"] == "greater_than") and (sensor_data.raw_value > data_filter["threshold"]):
                is_dropped = True
                break
            if (data_filter["comparing_method"] == "less_than") and (sensor_data.raw_value < data_filter["threshold"]):
                is_dropped = True
                break

        # 3. If not dropped, send request
        if not is_dropped:
            # Send http request to dataserver
            request_url = str("http://%s:%d/dataserver/sensordata" % (self.config.dataserver_addr, self.config.dataserver_port))

            self.curl.setopt(pycurl.URL, request_url)
            self.curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            self.curl.setopt(pycurl.TIMEOUT, 30)
            self.curl.setopt(pycurl.POSTFIELDS, sensor_data.get_json_dumps())

            try:
                self.curl.perform()
            except Exception as e:
                logging.exception("[Gateway.filter_and_send_sensor_data] exception:" + str(e))
                raise ServerError("Error on sending sensor data to data server.", e)

    def find_hub_by_id(self, hub_id):
        """
        根据传入的hub_id在已知的hub中查找，返回(hub_addr, hub_port)。
        如果找不到，抛出异常

        :rtype (str, int)
        """
        result = [hub for hub in self.config.hubs if hub_id == hub["hub_id"]]
        if len(result) == 0:
            raise ServerError("[find_hub_by_id]: Cannot find hub with id=%s." % hub_id)
        elif len(result) > 1:
            raise ServerError("[find_hub_by_id]: Found multiple hub with id=%s. Do nothing." % hub_id)
        else:
            return result[0]["hub_addr"], result[0]["hub_port"]

    def get_dataserver_info(self):
        """
        返回dataserver的配置。返回(dataserver_addr, dataserver_port)。

        :rtype (str, int)
        """
        return self.config.dataserver_addr, self.config.dataserver_port


def run_gateway():
    """
    运行Gateway。请使用rungateway.py调用。

    :rtype: Gateway
    """
    from gatewayconfig import parse_from_file
    default_config = parse_from_file("config/gateway.conf")
    return Gateway(default_config)