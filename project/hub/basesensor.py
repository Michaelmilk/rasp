# -*- coding: utf8 -*-

from sensordata import SensorData
import logging

logging.basicConfig(level=logging.DEBUG)


class BaseSensor(object):
    """
    Sensor.
    SHOULD BE INHERITED as specific sensor driver.
    """

    def __init__(self, sensor_type=None, sensor_id=None, sensor_desc=None, last_data=None, is_initialized=False):
        """
        Parameter
        ---------
        :type sensor_type: str
        :type sensor_id: str
        :type sensor_desc: str
        :type last_data: SensorData
        :type is_initialized: bool
        """
        self.sensor_type = sensor_type
        self.sensor_id = sensor_id
        self.sensor_desc = sensor_desc
        self.last_data = last_data
        self.is_initialized = is_initialized

    def initialize(self, config=None):
        """
        Initialize the sensor device.
        SHOULD BE OVERRIDED.

        Parameter
        ---------
        config: device specific config for initialization
        """
        self.is_initialized = True
        logging.debug("[BaseSensor.initialize] initialized " + str(self))

    def get_data(self):
        """
        Get data from sensor, build and return a SensorData object.
        SHOULD BE OVERRIDED.

        Return
        ------
        :rtype: SensorData
        new-fetched sensor data.
        """
        if not self.is_initialized:
            raise Exception("Sensor(type=%s, id=%s, desc=%s) is not initialized." % (self.sensor_type, self.sensor_id, self.sensor_desc))

        from sensordata import SensorData
        self.last_data = SensorData(sensor_type="Base sensor class: fake data", raw_value=0)
        logging.debug("[BaseSensor.get_data] returning raw=" + str(self.last_data.raw_value) + " sensorid=" + self.sensor_id);
        return self.last_data

    def get_json_dumps_data(self):
        """
        Get data from sensor, call its getJsonDump() method and return that return value.
        SHOULD BE OVERRIDED.

        Return
        ------
        :rtype: str
        new-fetched sensor data, json string format
        """
        return self.get_data().get_json_dumps()

    def close(self):
        """
        Safely close the sensor(e.g. close GPIO)
        SHOULD BE OVERRIDED.
        """
        self.is_initialized = False
        logging.debug("[BaseSensor.close] closed " + str(self))