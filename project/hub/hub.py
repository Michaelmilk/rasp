# -*- coding: utf8 -*-

from importlib import import_module
from threading import Thread, Event
from hubserver import HubServer
import pycurl
import hubconfig
import logging


logging.basicConfig(level=logging.DEBUG)


class Hub(object):
    """
    Hub.
    Connect multiple sensors, read initial config from file,
    connect to gateway, receive new config from gateway... etc
    """

    def __init__(self, hub_config):
        """
        This method will run HubServer with hub_config directly

        Parameter
        ---------
        :type hub_config:hubconfig.HubConfig
        """
        logging.debug("[Hub.__init__] hub_config=" + str(hub_config))

        self.old_config = None
        """ :type: hubconfig.HubConfig """

        self.config = None
        """ :type: hubconfig.HubConfig """

        self.thread_sensor_tuples = []
        """ :type: list of (MonitorThread, Sensor) """

        self.apply_config(hub_config)

        self.hub_server = HubServer(self, self.config.hub_host, self.config.hub_port)
        """ :type: HubServer """

    def apply_config(self, hub_config, load_old_config=False):
        """
        Update config of hub.
        1. Stop current server
        2. Close current sensors
        3. Initialize new sensors
        4. Start new server

        If exception happens in initializing new sensors,
        old config will be reloaded.

        Parameter
        ---------
        :type hub_config: hubconfig.HubConfig
        the new config object
        :type load_old_config: bool
        should not set from outer call
        """
        logging.debug("[Hub.apply_config] hub_config=" + str(hub_config) + "load_old_config=" + str(load_old_config))

        # Some check
        if hub_config is None:
            return

        if not isinstance(hub_config, hubconfig.HubConfig):
            raise TypeError("%s is not a HubConfig instance" % str(hub_config))

        # Replace config field
        self.old_config = self.config

        # if new config has a different "hub_host" and "hub_port" to old,
        # todo run some script to reload whole program
        # todo
        if (self.old_config is not None) and ((hub_config.hub_port != self.old_config.hub_port) or (hub_config.hub_host != self.old_config.hub_host)):
            self.restart_whole_server()

        # Reset server
        self.reset()

        # start new sensor monitor threads
        try:
            self.config = hub_config
            for sensor_config in self.config.sensors:
                sensor_module = import_module("sensor_" + sensor_config["type"])
                sensor = sensor_module.Sensor(sensor_config["id"], sensor_config["desc"])
                thread = MonitorThread(sensor, self.config.gateway_addr, self.config.gateway_port, sensor_config["interval"])
                self.thread_sensor_tuples.append((thread, sensor))
                sensor.initialize()
                thread.start()
                logging.debug("[Hub.apply_config] A sensor and its thread is started. sensorid=" + sensor.sensor_id + " thread=" + str(thread))
        except Exception as e:
            if not load_old_config:
                logging.debug("[Hub.apply_config] Error occured while loading new config, rolling to old one")
                self.reset()
                self.config = self.old_config
                self.old_config = None
                self.apply_config(self.old_config, True)
            else:
                logging.debug("[Hub.apply_config] Error occured while rolling to old one, resetting hub")
                self.reset()
                raise e

    def reset(self):
        """
        clear config, clear thread_sensor_tuples,
        stop all sensor threads, close all sensors
        """

        logging.debug("[Hub.reset] resetting")
        logging.debug("[Hub.reset] remaining sensor thread count: " + str(len(self.thread_sensor_tuples)))

        # stop all sensors & their monitor threads
        for (thread, sensor) in self.thread_sensor_tuples:
            thread.stop_event.set()
            sensor.close()
            logging.debug("[Hub.reset] A sensor and its thread is stopped. sensorid=" + sensor.sensor_id + " thread=" + str(thread))

        self.thread_sensor_tuples = []
        self.config = None

    def restart_whole_server(self):
        """
        stop current server process, run some script to restart whole program
        """
        logging.warn("[Hub.reload_whole_server] not implemented yet!")
        pass


class MonitorThread(Thread):
    def __init__(self, sensor, gateway_addr, gateway_port, interval):
        """
        :type sensor: BaseSensor
        :type gateway_addr: str
        :type gateway_port: int
        :type interval float
        """

        Thread.__init__(self)
        self.sensor = sensor
        self.gateway_addr = gateway_addr
        self.gateway_port = gateway_port
        self.interval = interval
        self.stop_event = Event()

    def run(self):
        request_url = "http://%s:%d/gateway/sensordata" % (self.gateway_addr, self.gateway_port)

        curl = pycurl.Curl()
        curl.setopt(curl.URL, request_url)

        while not self.stop_event.wait(self.interval):
            try:
                curl.setopt(curl.POSTFIELDS, self.sensor.get_json_dumps_data())
                curl.perform()
            except Exception as e:
                logging.exception("[MonitorThread.run] exception:" + str(e))

    def stop(self):
        self._stop.set()


if __name__ == "__main__":
    default_config = hubconfig.parse_from_file("hub.conf")
    hub = Hub(default_config)