# -*- coding: utf8 -*-

"""本Python模块含有Gateway配置类，和从文件、字符串解析Gateway配置对象的方法。"""

__author__ = "tgmerge"


import logging

logging.basicConfig(level=logging.DEBUG)


class GatewayConfig(object):
    """
    封装Gateway的配置。配置项参见config/gateway.conf。

    任何情况下不应该使用GatewayConfig()方法创建GatewayConfig对象，
    而应该使用parse_from_string()和parse_from_file()从字符串和文件解析GatewayConfig。
    """

    def __init__(self, config_dict):
        """
        :param dict config_dict: 初始化用字典
        """

        self.dataserver_addr = config_dict["dataserver_addr"]
        """ :type: basestring """

        self.dataserver_port = config_dict["dataserver_port"]
        """ :type: int """

        self.gateway_id = config_dict["gateway_id"]
        """ :type: basestring """

        self.gateway_desc = config_dict["gateway_desc"]
        """ :type: basestring """

        self.gateway_host = config_dict["gateway_host"]
        """ :type: basestring """

        self.gateway_port = config_dict["gateway_port"]
        """ :type: int """

        self.hubs = config_dict["hubs"]
        """ :type: list of dict """

        self.filters = config_dict["filters"]
        """ :type: list of dict """

    def get_json_string(self):
        """
        获取代表本配置对象的Json字符串。

        :rtype: str
        """
        from json import dumps

        return dumps({
            "dataserver_addr": self.dataserver_addr,
            "dataserver_port": self.dataserver_port,
            "gateway_id": self.gateway_id,
            "gateway_desc": self.gateway_desc,
            "gateway_host": self.gateway_host,
            "gateway_port": self.gateway_port,
            "hubs": self.hubs,
            "filters": self.filters
        })


def parse_from_string(config_json):
    """
    从Json字符串解析GatewayConfig，返回解析后的GatewayConfig对象。

    :param str config_json: Json字符串

    :rtype: HubConfig
    """

    logging.debug("[parse_from_string] parsing" + config_json[:20])

    # Parse json string to a dict
    from json import loads
    try:
        config = loads(config_json)
    except ValueError as e:
        raise e

    # Check first level items
    valid_config_items = [
        ("dataserver_addr", basestring),
        ("dataserver_port", int),
        ("gateway_id", basestring),
        ("gateway_desc", basestring),
        ("gateway_host", basestring),
        ("gateway_port", int),
        ("hubs", list),
        ("filters", list)
    ]

    for (key, keyType) in valid_config_items:
        if key not in config:
            raise ValueError("key %s is not in config_json" % key)
        if not isinstance(config[key], keyType):
            raise ValueError("key %s is not '%s' instance" % (key, str(keyType)))

    logging.debug("[parse_from_string] Gateway config item checked")

    # Check second level items in "hubs" dict
    valid_hub_config_items = [
        ("hub_id", basestring),
        ("hub_desc", basestring),
        ("hub_addr", basestring),
        ("hub_port", int)
    ]

    for hub_config in config["hubs"]:
        for (key, keyType) in valid_hub_config_items:
            if key not in hub_config:
                raise ValueError("key '%s' is not in 'hubs' list in config_json" % key)
            if not isinstance(hub_config[key], keyType):
                raise ValueError("key '%s' is not '%s' instance in 'hubs' list" % (key, str(keyType)))

    logging.debug("[parse_from_string] Hub config item checked")

    # Check second level items in "filters" dict
    valid_filter_config_items = [
        ("apply_on_sensor_type", basestring),
        ("apply_on_sensor_id", basestring),
        ("comparing_method", basestring),
        ("threshold", float)
    ]

    for hub_config in config["filters"]:
        for (key, keyType) in valid_filter_config_items:
            if key not in hub_config:
                raise ValueError("key '%s' is not in 'filters' list in config_json" % key)
            if not isinstance(hub_config[key], keyType):
                raise ValueError("key '%s' is not '%s' instance in 'filters' list" % (key, str(keyType)))

    logging.debug("[parse_from_string] Filter config item checked")

    # Return a GatewayConfig object
    gateway_config = GatewayConfig(config_json, config)
    logging.debug("[parse_from_string] returning GatewayConfig " + str(gateway_config) + " addr=" + config["gateway_host"])
    return gateway_config


def parse_from_file(file_name):
    """
    从文本文件解析GatewayConfig，返回解析后的GatewayConfig对象。

    :param str file_name: 文件名

    :rtype: GatewayConfig
    """

    json_file = open(file_name)
    json_str = json_file.read()
    return parse_from_string(json_str)
