# -*- coding: utf8 -*-

"""本Python模块含有Hub配置类，和从文件、字符串解析Hub配置对象的方法。"""

__author__ = "tgmerge"


import logging

logging.basicConfig(level=logging.DEBUG)


class HubConfig(object):
    """
    封装Hub的配置。配置项参见config/hub.conf。

    任何情况下不应该使用HubConfig()方法创建HubConfig对象，
    而应该使用parse_from_string()和parse_from_file()从字符串和文件解析HubConfig。
    """

    def __init__(self, config_dict):
        """
        :param dict config_dict: 初始化用字典
        """

        self.gateway_addr = config_dict["gateway_addr"]
        """ :type: basestring """

        self.gateway_port = config_dict["gateway_port"]
        """ :type: int """

        self.hub_id = config_dict["hub_id"]
        """ :type: basestring """

        self.hub_desc = config_dict["hub_desc"]
        """ :type: basestring """

        self.hub_host = config_dict["hub_host"]
        """ :type: basestring """

        self.hub_port = config_dict["hub_port"]
        """ :type: int """

        self.sensors = config_dict["sensors"]
        """ :type: list of dict"""

    def get_json_string(self):
        """
        获取代表本配置对象的Json字符串。

        :rtype: str
        """
        from json import dumps

        return dumps({
            "gateway_addr": self.gateway_addr,
            "gateway_port": self.gateway_port,
            "hub_id": self.hub_id,
            "hub_desc": self.hub_desc,
            "hub_host": self.hub_host,
            "hub_port": self.hub_port,
            "sensors": self.sensors
        })


def parse_from_string(config_json):
    """
    从Json字符串解析HubConfig，返回解析后的HubConfig对象。

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
        ("gateway_addr", basestring),
        ("gateway_port", int),
        ("hub_id", basestring),
        ("hub_desc", basestring),
        ("hub_host", basestring),
        ("hub_port", int),
        ("sensors", list)
    ]

    for (key, keyType) in valid_config_items:
        if key not in config:
            raise ValueError("key '%s' is not in config_json" % key)
        if not isinstance(config[key], keyType):
            raise ValueError("key '%s' is not '%s' instance" % (key, str(keyType)))

    logging.debug("[parse_from_string] Hub config item checked")

    # Check second level items in "sensors" dict
    valid_sensor_config_items = [
        ("type", basestring),
        ("id", basestring),
        ("desc", basestring),
        ("interval", float),
        ("config", dict)
    ]

    for sensor_config in config["sensors"]:
        for (key, keyType) in valid_sensor_config_items:
            if key not in sensor_config:
                raise ValueError("key '%s' is not in 'sensors' list in config_json" % key)
            if not isinstance(sensor_config[key], keyType):
                raise ValueError("key '%s' is not '%s' instance in 'sensors' list" % (key, str(keyType)))

    logging.debug("[parse_from_string] Sensor config item checked")

    # Return a HubConfig object
    hub_config = HubConfig(config)
    logging.debug("[parse_from_string] returning HubConfig " + str(hub_config) + " addr=" + config["gateway_addr"])
    return hub_config


def parse_from_file(file_name):
    """
    从文本文件解析HubConfig，返回解析后的HubConfig对象。

    :param str file_name: 文件名

    :rtype: HubConfig
    """

    json_file = open(file_name)
    json_str = json_file.read()
    return parse_from_string(json_str)
