# -*- coding: utf8 -*-

import logging
from threading import Thread, Event
import pycurl
from module.hub.basesensor import BaseSensor

logging.basicConfig(level=logging.DEBUG)


class MonitorThread(Thread):
    def __init__(self, sensor, gateway_addr, gateway_port, interval):
        """
        :type sensor: BaseSensor
        :type gateway_addr: str
        :type gateway_port: int
        :type interval: float
        """

        Thread.__init__(self)
        self.sensor = sensor
        """ :type: BaseSensor """

        self.gateway_addr = gateway_addr
        """ :type: str """

        self.gateway_port = gateway_port
        """ :type: int """

        self.interval = interval
        """ :type: float """

        self.stop_event = Event()

    def run(self):
        request_url = str("http://%s:%d/gateway/sensordata" % (self.gateway_addr, self.gateway_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)

        self.sensor.initialize()

        while not self.stop_event.wait(self.interval):
            try:
                curl.setopt(pycurl.POSTFIELDS, self.sensor.get_json_dumps_data())
                curl.perform()
            except Exception as e:
                logging.exception("[MonitorThread.run] exception:" + str(e))

    def stop(self):
        self.sensor.close()
        self.stop_event.set()
