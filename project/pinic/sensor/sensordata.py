# -*- coding: utf8 -*-

"""
本Python模块包含传感器数据类SensorData，用于封装从传感器获取的数据。

* 要使用SensorData的值，可以读取它的SensorData的sensor_id、sensor_type、raw_value、timestamp四个成员。

* 要Json化一个SensorData对象，可以使用SensorData.get_json_dumps()方法。

* 要从Json文本解析SensorData对象，可以使用本模块中的parse_from_string(str)方法。
"""

__author__ = "tgmerge"


from json import loads


class SensorData(object):
    """
    SensorData对象是一份传感器数据。
    """

    def __init__(self, sensor_id="", sensor_type="", raw_value=None, timestamp=None):
        """
        :param str sensor_id:   源传感器的ID。
        :param str sensor_type: 源传感器的种类(type值)。
        :param float raw_value: 原始数据的值。
        :param float timestamp: 产生该数据的时间戳。
        """

        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.raw_value = raw_value
        self.timestamp = timestamp

    def get_json_dumps(self):
        """
        返回代表该SensorData数据的JSON。

        :rtype: str
        """
        from json import dumps
        return dumps({
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "raw_value": self.raw_value,
            "timestamp": self.timestamp
        })


def parse_from_string(data_json):
    """
    从Json字符串解析SensorData，返回解析后的SensorData对象。

    :param str data_json: Json字符串

    :rtype: SensorData
    """

    # Load into dict
    data = loads(data_json)

    # Check first level items
    valid_config_items = [
        ("sensor_id", basestring),
        ("sensor_type", basestring),
        ("raw_value", float),
        ("timestamp", float),
    ]

    for (key, keyType) in valid_config_items:
        if key not in data:
            raise ValueError("key %s is not in data_json" % key)
        if not isinstance(data[key], keyType):
            raise ValueError("key %s is not '%s' instance" % (key, str(keyType)))

    # Return new object
    return SensorData(data["sensor_id"], data["sensor_type"], data["raw_value"], data["timestamp"])