# -*- coding: utf8 -*-

"""
本Python模块包含传感器数据类。

* SensorData: 封装从传感器获取的数据。
"""

__author__ = "tgmerge"


class SensorData(object):
    """
    SensorData对象是一份传感器数据。
    """

    def __init__(self, sensor_id=None, sensor_type=None, raw_value=None, hub_id=None, timestamp=None):
        """
        :param str sensor_id:   源传感器的ID。
        :param str sensor_type: 源传感器的种类(type值)。
        :param float raw_value: 原始数据的值。
        :param str hub_id:      该份数据传递到的Hub。暂时没有作用。
        :param float timestamp: 产生该数据的时间戳。
        """

        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.raw_value = raw_value
        self.hub_id = hub_id
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
            "hub_id": self.hub_id,
            "timestamp": self.timestamp
        })