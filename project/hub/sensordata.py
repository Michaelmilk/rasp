# -*- coding: utf8 -*-

import logging

logging.basicConfig(level=logging.DEBUG)


class SensorData(object):
    """
    Data from sensor.
    """

    def __init__(self, sensor_id=None, sensor_type=None, raw_value=None, hub_id=None, timestamp=None):
        """
        Parameter
        ---------
        :type sensor_id: str
        :type sensor_type: str
        :type raw_value: float
        :type hub_id: str
        :type timestamp: float
        """
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.raw_value = raw_value
        self.hub_id = hub_id
        self.timestamp = timestamp

    def get_readable_value(self):
        """
        Return a readable version of raw value of this data object.
        May be override in sensor specified implements.

        Return
        ------
        :rtype: str
        readable version of raw value of this data object
        """
        return "raw value: " + str(self.raw_value)

    def get_json_dumps(self):
        """
        Return a json string, containing:
        sensor_id, sensor_type, raw_value, readableValue, hub_id, timestamp

        Returns
        -------
        string, json dump of a dict, containing values above
        """
        from json import dumps
        return dumps({"sensor_id": self.sensor_id,
                      "sensor_type": self.sensor_type,
                      "raw_value": self.raw_value,
                      "readable_value": self.get_readable_value(),
                      "hub_id": self.hub_id,
                      "timestamp": self.timestamp})
