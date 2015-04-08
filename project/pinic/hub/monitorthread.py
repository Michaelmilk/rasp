# -*- coding: utf8 -*-

"""本Python模块含有Hub的传感器监视和数据发送线程。"""

__author__ = "tgmerge"


import logging
from threading import Thread, Event
import pycurl
from pinic.sensor.basesensor import BaseSensor


logging.basicConfig(level=logging.DEBUG)


class MonitorThread(Thread):
    """传感器监视线程。以固定时间间隔从传感器读取数据，并发送给Gateway。"""

    def __init__(self, sensor, gateway_addr, gateway_port, interval):
        """
        :param BaseSensor sensor: 传感器对象。
        :param str gateway_addr:  Gateway的IP地址。
        :param int gateway_port:  Gateway的端口。
        :param float interval:    传感器读取时间间隔。
        """

        Thread.__init__(self)
        self.sensor = sensor
        self.gateway_addr = gateway_addr
        self.gateway_port = gateway_port
        self.interval = interval
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
