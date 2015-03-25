# -*- coding: utf-8 -*-

from time import time
import logging
from basesensor import BaseSensor
from module.hub.sensordata import SensorData
import spidev


logging.basicConfig(level=logging.DEBUG)


class Sensor(BaseSensor):

    def __init__(self, sensor_id, sensor_desc, sensor_config):
        super(Sensor, self).__init__("tlc1549", sensor_id, sensor_desc, sensor_config)
        self.spi = spidev.SpiDev()

    def initialize(self):
        self.spi.open(0, 0)
        self.is_initialized = True
        logging.debug("[Sensor.initialize] initialized " + str(self) + " sensor_id=" + self.sensor_id + " config=" + str(self.sensor_config))
        logging.debug("spi open")

    def get_data(self):
        logging.debug("XXX " + str(self.is_initialized))
        raw_value = 0.0
        if self.is_initialized:
            raw_value = self.read_spi_value()
        else:
            raw_value = -1.0
        logging.debug("[Sensor.get_data] returning " + str(raw_value) + " sensorid=" + self.sensor_id)
        return SensorData(self.sensor_id, self.sensor_type, raw_value, "", time())

    def get_json_dumps_data(self):
        json_str = self.get_data().get_json_dumps()
        logging.debug("[Sensor.get_json_dumps_data] returning " + json_str)
        return json_str

    def close(self):
        self.spi.close()
        self.is_initialized = False
        logging.debug("[Sensor.close] closed " + str(self) + " sensorid=" + self.sensor_id)

    def read_spi_value(self):
        data = self.spi.readbytes(2)
        data_value = ((data[0] & 0b11111111) << 2) + ((data[1] & 0b11000000) >> 6)
        return float(data_value)
