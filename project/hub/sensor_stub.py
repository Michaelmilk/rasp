# -*- coding: utf-8 -*-

from basesensor import BaseSensor
from sensordata import SensorData
from time import time
import logging

logging.basicConfig(level=logging.DEBUG)


class Sensor(BaseSensor):

    def __init__(self, sensor_id, sensor_desc, sensor_config):
        super(Sensor, self).__init__("Stub", sensor_id, sensor_desc, sensor_config)
        self.count = 0

    def initialize(self):
        self.is_initialized = True
        logging.debug("[sensor_stub.Sensor.initialize] initialized " + str(self) + " sensor_id=" + self.sensor_id + " config=" + str(self.sensor_config))

    def get_data(self):
        self.count += 1
        raw_value = float(self.count)
        logging.debug("[Sensor.get_data] returning " + str(raw_value) + " sensorid=" + self.sensor_id)
        return SensorData(self.sensor_id, self.sensor_type, raw_value, "", time())

    def get_json_dumps_data(self):
        json_str = self.get_data().get_json_dumps()
        logging.debug("[Sensor.get_json_dumps_data] returning " + json_str)
        return json_str

    def close(self):
        self.is_initialized = False
        logging.debug("[Sensor.close] closed " + str(self) + " sensorid=" + self.sensor_id)
