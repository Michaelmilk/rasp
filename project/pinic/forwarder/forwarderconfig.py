# -*- coding: utf8 -*-

"""
本Python模块包含Forwarder的配置部分。
ForwarderConfig配置类用于解析和封装Forwarder的配置。
另外，还包含从文件和字符串解析Forwarder配置的方法。
文件或字符串中，Forwarder的配置以JSON存储。

配置示例
========

::

    {
        "forwarder_host": "localhost",            # Forwarder的服务主机，需要让网络中的任何主机访问的话，要设置为0.0.0.0
        "forwarder_port": 9005,                   # Forwarder的服务端口
        "forwarder_id": "TEST-FORWARDER-1",       # Forwarder ID
        "forwarder_desc": "Test forwarder.",      # Forwarder的描述文字
    }

"""

__author__ = "tgmerge"


# 设置日志等级
import logging
logging.basicConfig(level=logging.DEBUG)


class ForwarderConfig(object):
    """
    ForwarderConfig类封装Forwarder的配置信息。
    任何情况下不应该使用ForwarderConfig()方法创建ForwarderConfig对象，
    而应该使用parse_from_string()和parse_from_file()从字符串和文件解析配置并获取本类的实例。
    """

    # 用于在Json解析中，检查配置的第一级键值是否有误
    first_level_check = [
        ("forwarder_host", basestring),
        ("forwarder_port", int),
        ("forwarder_id", basestring),
        ("forwarder_desc", basestring)
    ]

    def __init__(self, config_dict):
        """
        :param dict config_dict: 初始化用字典。用字典的对应键设置本ForwarderConfig对象的各个成员变量。
        """
        self.forwarder_host = config_dict["forwarder_host"]  # 配置的forwarder_host值

        self.forwarder_port = config_dict["forwarder_port"]  # 配置的forwarder_port值

        self.forwarder_id = config_dict["forwarder_id"]  # 配置的forwarder_id值

        self.forwarder_desc = config_dict["forwarder_desc"]  # 配置的forwarder_desc值

    def get_json_string(self):
        """
        返回一个字符串，是本配置对象的Json数据。

        :rtype: str
        """

        from json import dumps
        return dumps({
            "forwarder_host": self.forwarder_host,
            "forwarder_port": self.forwarder_port,
            "forwarder_id": self.forwarder_id,
            "forwarder_desc": self.forwarder_desc
        })


def parse_from_string(config_json):
    """
    从Json字符串解析ForwarderConfig，返回解析后的ForwarderConfig对象。
    如果解析中发现缺失的键，或值的类型错误，将抛出ValueError异常，并包含缺失或错误信息。

    :param str config_json: 需要解析的Json字符串
    :rtype: ForwarderConfig
    """

    logging.debug("[parse_from_string] parsing" + config_json[:20])

    # 将Json字符串解析为字典
    from json import loads
    try:
        config = loads(config_json)
    except ValueError as e:
        raise e

    # 检查第一级变量
    for (key, val_type) in ForwarderConfig.first_level_check:
        if key not in config:
            raise ValueError("key '%s' is not in config json." % key)
        if not isinstance(config[key], val_type):
            raise ValueError("value of key '%s' is not a '%s' instance." % (key, str(val_type)))

    logging.debug("[parse_from_string] first level item checked")

    # 返回解析后的对象
    return ForwarderConfig(config)


def parse_from_file(file_name):
    """
    从文本文件解析ForwarderConfig，返回解析后的ForwarderConfig对象。
    如果解析中发现缺失的键，或值的类型错误，将抛出ValueError异常，并包含缺失或错误的信息。

    :param str file_name: 要解析文件的文件路径
    :rtype: ForwarderConfig
    """

    json_file = open(file_name)
    json_str = json_file.read()
    return parse_from_string(json_str)
