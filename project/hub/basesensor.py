# -*- coding: utf8 -*-

from sensordata import SensorData
import logging

logging.basicConfig(level=logging.DEBUG)


class BaseSensor(object):
    """
    Sensor, to be inherited.
    See sensor_stub.py as example.
    """

    def __init__(self, sensor_type, sensor_id, sensor_desc, sensor_config):
        """
        Parameter/Fields
        ----------------
        :type sensor_type: str
        Type of the sensor. Used for importing driver module.

        :type sensor_id: str
        Unique ID of the sensor.

        :type sensor_desc: str
        Description of the sensor.

        :type sensor_config: dict
        Initial config of the sensor
        """
        self.sensor_type = sensor_type
        """ :type: str """

        self.sensor_id = sensor_id
        """ :type: str """

        self.sensor_desc = sensor_desc
        """ :type: str """

        self.sensor_config = sensor_config
        """ :type: dict """

        self.last_data = None            # Last successfully gathered data.
        """ :type: SensorData """

        self.is_initialized = False      # Flag, indicating if the sensor is initialized.
        """ :type: bool"""               # Call initialize() and close() to set this.

    def initialize(self):
        """
        Initialize the sensor device USING self.sensor_config
        SHOULD BE OVERRIDDEN.

        Parameter
        ---------
        :type config: dict
        device specific config for initialization
        """
        self.is_initialized = True

    def get_data(self):
        """
        Read data from sensor, return a SensorData object.
        SHOULD BE OVERRIDDEN.

        Return
        ------
        :rtype: SensorData
        new-fetched sensor data.
        """
        if not self.is_initialized:
            raise Exception("Sensor(type=%s, id=%s, desc=%s) is not initialized." % (self.sensor_type, self.sensor_id, self.sensor_desc))

        self.last_data = SensorData(sensor_type="BaseSensor: fake data", raw_value=0)
        return self.last_data

    def get_json_dumps_data(self):
        """
        Read data from sensor, put it in SensorData object, return its getJsonDump() string.
        SHOULD BE OVERRIDDEN.

        Return
        ------
        :rtype: str
        new-fetched sensor data, json string format
        """
        return self.get_data().get_json_dumps()

    def close(self):
        """
        Safely close the sensor(e.g. close GPIO)
        SHOULD BE OVERRIDDEN.
        """
        self.is_initialized = False
