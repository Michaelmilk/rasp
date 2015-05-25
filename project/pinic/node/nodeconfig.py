# -*- coding: utf8 -*-

"""
本Python模块包含Node的配置部分。
NodeConfig配置类用于解析和封装Node的配置。
另外，还包含从文件和字符串解析Node配置的方法。
文件或字符串中，Node的配置以JSON存储。

配置示例
========

::

    {
        "node_host":"localhost",             # Node自身的服务主机，如果需要让网络中任何主机均可访问，应设置为0.0.0.0
        "node_port":9001,                    # Node的服务端口
        "node_id":"TEST-NODE-1",             # Node的ID，需要在网络中唯一
        "node_desc":"Test node.",            # Node的描述文本
        "server_addr":"127.0.0.1",           # 要连接到的Server的IP地址
        "server_port":9002,                  # 要连接到的Server的端口
        "sensors":[                          # 本机连接到Node的传感器列表
            {
                "sensor_type":"stub",            # 传感器的设备类型
                "sensor_id":"TEST-SENSOR-1",     # 传感器的ID，建议在网络中唯一
                "sensor_desc":"Test sensor.",    # 传感器描述文字
                "sensor_config": {}              # 传感器初始化配置，可留空（设置为{}）。
            }
        ],
        "filters":[                           # 传感数据过滤规则列表
            {
                "apply_on_sensor_type":"none",     # 在特定类型传感器上使用。设为"*"则包含任意传感器。
                "apply_on_sensor_id":"none",       # 在特定ID的传感器上使用。设为"*"则包含任意传感器。
                "comparing_method":"greater_than", # 可为"greater_than"和"less_than"。符合的数据被抛弃。
                "threshold":100                    # 阈值。例如，"greater_than" 100，则大于100的数据被抛弃。
            }
        ]
    }

"""

__author__ = "tgmerge"


# 设置日志等级
import logging
logging.basicConfig(level=logging.DEBUG)


class NodeConfig(object):
    """
    NodeConfig类封装Node的配置信息。
    任何情况下不应该使用NodeConfig()方法创建NodeConfig对象，
    而应该使用parse_from_string()和parse_from_file()从字符串和文件解析配置并获取本类的实例。
    """

    # 用于在Json解析中，检查配置的第一级键值是否有误
    first_level_check = [
        ("node_host", basestring),
        ("node_port", int),
        ("node_id", basestring),
        ("node_desc", basestring),
        ("server_addr", basestring),
        ("server_port", int),
        ("sensors", list),
        ("filters", list)
    ]

    # 用于在Json解析中，检查配置的第二级键值是否有误
    second_level_item = [
        "sensors",
        "filters"
    ]

    # 用于在Json解析中，检查配置的第二级键值是否有误
    second_level_checks = {
        "sensors": [
            ("sensor_type", basestring),
            ("sensor_id", basestring),
            ("sensor_desc", basestring),
            ("sensor_config", dict),
        ],
        "filters": [
            ("apply_on_sensor_type", basestring),
            ("apply_on_sensor_id", basestring),
            ("comparing_method", basestring),
            ("threshold", int)
        ]
    }

    def __init__(self, config_dict):
        """
        :param dict config_dict: 初始化用字典。用字典的对应键设置本NodeConfig对象的各个成员变量。
        """

        self.node_host = config_dict["node_host"]  # 以下均为配置Json中的的同名键

        self.node_port = config_dict["node_port"]

        self.node_id = config_dict["node_id"]

        self.node_desc = config_dict["node_desc"]

        self.server_addr = config_dict["server_addr"]

        self.server_port = config_dict["server_port"]

        self.sensors = config_dict["sensors"]

        self.filters = config_dict["filters"]

    def get_json_string(self):
        """
        返回一个字符串，是本配置对象的Json数据。

        :rtype: str
        """
        from json import dumps

        return dumps({
            "node_host": self.node_host,
            "node_port": self.node_port,
            "node_id": self.node_id,
            "node_desc": self.node_desc,
            "server_addr": self.server_addr,
            "server_port": self.server_port,
            "sensors": self.sensors,
            "filters": self.filters
        })


def parse_from_string(config_json):
    """
    从Json字符串解析NodeConfig，返回解析后的NodeConfig对象。
    如果解析中发现缺失的键，或值的类型错误，将抛出ValueError异常，并包含缺失和错误的信息。

    :param str config_json: 需要解析的Json字符串
    :rtype: NodeConfig
    """

    logging.debug("[parse_from_string] parsing" + config_json[:20])

    # 将Json字符串解析为字典
    from json import loads
    try:
        config = loads(config_json)
    except ValueError as e:
        raise e

    # 检查第一级变量
    for (key, val_type) in NodeConfig.first_level_check:
        if key not in config:
            raise ValueError("key '%s' is not in config json." % key)
        if not isinstance(config[key], val_type):
            raise ValueError("value of key '%s' is not a '%s' instance." % (key, str(val_type)))

    logging.debug("[parse_from_string] first level item checked")

    # 检查第二级变量
    for parent_key in NodeConfig.second_level_item:
        second_level_check = NodeConfig.second_level_checks[parent_key]
        for dict_to_check in config[parent_key]:
            for (key, val_type) in second_level_check:
                if key not in dict_to_check:
                    raise ValueError("key '%s' is not in '%s' list in config json" % (key, parent_key))
                if not isinstance(dict_to_check[key], val_type):
                    raise ValueError("key '%s' is not '%s' instance in '%s' list" % (key, str(val_type), parent_key))

    logging.debug("[parse_from_string] second level item checked")

    # 返回解析后的对象
    return NodeConfig(config)


def parse_from_file(file_name):
    """
    从文本文件解析NodeConfig，返回解析后的NodeConfig对象。
    如果解析中发现缺失的键，或值的类型错误，将抛出ValueError异常，并包含缺失和错误的信息。

    :param str file_name: 要解析文件的文件路径
    :rtype: NodeConfig
    """

    json_file = open(file_name)
    json_str = json_file.read()
    return parse_from_string(json_str)
