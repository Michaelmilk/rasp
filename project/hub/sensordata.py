# -*- coding: utf8 -*-

import logging

logging.basicConfig(level=logging.DEBUG)


class SensorData(object):
    """
    Data from sensor.
    """

    def __init__(self, sensor_id=None, sensor_type=None, raw_value=None, hub_id=None, timestamp=None):
        """
        Parameter/Object fields
        -----------------------
        :type sensor_id: str
        ID of source sensor.

        :type sensor_type: str
        Type of source sensor.

        :type raw_value: float
        Raw value from source sensor.

        :type hub_id: str
        Reserved field, ID of Hub this SensorData is passing to.

        :type timestamp: float
        Check time of the sensor.
        """

        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.raw_value = raw_value
        self.hub_id = hub_id
        self.timestamp = timestamp

    def get_readable_value(self):
        """
        Return a readable version of raw value in this object.
        May be overridden in sensor specified implements.

        Return
        ------
        :rtype: str
        readable version of raw value of this data object
        """
        return "Raw value: " + str(self.raw_value)

    def get_json_dumps(self):
        """
        Return a json string represents this SensorData object.

        Returns
        -------
        :rtype: str
        json dump of a dict.
        """
        from json import dumps
        return dumps({
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "raw_value": self.raw_value,
            "hub_id": self.hub_id,
            "timestamp": self.timestamp,
            "readable_value": self.get_readable_value()
        })
