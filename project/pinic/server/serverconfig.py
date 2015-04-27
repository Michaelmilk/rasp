# -*- coding: utf8 -*-

"""
本Python模块含有Server配置类，用于解析和封装Server的配置。
另外，还包含从文件和字符串解析Server配置的方法。
文件或字符串中，Server的配置以JSON存储。

配置示例
========

::

    {
        "server_host": "localhost",     # Server自身的服务主机，可以是0.0.0.0
        "server_port": 9002,            # Server自身的服务端口
        "server_id": "TEST-SERVER-1",   # Server的ID，需要在网络中唯一
        "server_desc": "Test server.",  # Server的描述文字
        "forwarder_addr": "127.0.0.1",  # 要连接到的Forwarder的IP地址
        "forwarder_port": 9003          # 要连接到的Server的端口
    }

"""

__author__ = "tgmerge"


import logging

logging.basicConfig(level=logging.DEBUG)


class ServerConfig(object):
    """
    封装Server的配置。任何情况下不应该使用ServerConfig()方法创建ServerConfig对象，
    而应该使用parse_from_string()和parse_from_file()从字符串和文件解析。
    """

    first_level_check = [
        ("server_host", basestring),
        ("server_port", int),
        ("server_id", basestring),
        ("server_desc", basestring),
        ("forwarder_addr", basestring),
        ("forwarder_port", int)
    ]
    """ 用于在Json解析中，检查配置的第一级键值是否有误 """

    def __init__(self, config_dict):
        """
        :param dict config_dict: 初始化用字典
        """
        self.server_host = config_dict["server_host"]
        """ :type: basestring """

        self.server_port = config_dict["server_port"]
        """ :type: int """

        self.server_id = config_dict["server_id"]
        """ :type: basestring """

        self.server_desc = config_dict["server_desc"]
        """ :type: basestring """

        self.forwarder_addr = config_dict["forwarder_addr"]
        """ :type: basestring """

        self.forwarder_port = config_dict["forwarder_port"]
        """ :type: int """

    def get_json_string(self):
        """
        获取代表本配置对象的Json字符串。

        :rtype: str
        """
        from json import dumps
        return dumps({
            "server_host": self.server_host,
            "server_port": self.server_port,
            "server_id": self.server_id,
            "server_desc": self.server_desc,
            "forwarder_addr": self.forwarder_addr,
            "forwarder_port": self.forwarder_port
        })


def parse_from_string(config_json):
    """
    从Json字符串解析ServerConfig，返回解析后的NodeConfig对象。
    如果解析中发现缺失的键，或值的类型错误，将抛出ValueError异常，并包含缺失和错误的信息。

    :param str config_json: Json字符串
    :rtype: ServerConfig
    """

    logging.debug("[parse_from_string] parsing" + config_json[:20])

    # Parse json string to a dict
    from json import loads
    try:
        config = loads(config_json)
    except ValueError as e:
        raise e

    # Check first level items
    for (key, val_type) in ServerConfig.first_level_check:
        if key not in config:
            raise ValueError("key '%s' is not in config json." % key)
        if not isinstance(config[key], val_type):
            raise ValueError("value of key '%s' is not a '%s' instance." % (key, str(val_type)))

    logging.debug("[parse_from_string] first level item checked")

    # Return a NodeConfig object
    return ServerConfig(config)


def parse_from_file(file_name):
    """
    从文本文件解析ServerConfig，返回解析后的ServerConfig对象。
    如果解析中发现缺失的键，或值的类型错误，将抛出ValueError异常，并包含缺失和错误的信息。

    :param str file_name: 文件名
    :rtype: ServerConfig
    """

    json_file = open(file_name)
    json_str = json_file.read()
    return parse_from_string(json_str)
