# -*- coding: utf8 -*-

import logging
from importlib import import_module
from module.hub.monitorthread import MonitorThread
from module.hub.hubserver import HubServer
from module.hub.hubconfig import HubConfig

logging.basicConfig(level=logging.DEBUG)


class Hub(object):
    """
    Hub.
    """

    def __init__(self, hub_config):
        """
        Hub has a HubServer in it.
        This method will run HubServer using params in hub_config directly.
        :type hub_config:HubConfig
        """

        logging.debug("[Hub.__init__] hub_config=" + str(hub_config))

        self.old_config = None                              # Save old config when loading new one.
        """ :type: HubConfig """                            # Will be rolled back in case that new one failed to load.

        self.config = None                                  # Current hub config.
        """ :type: HubConfig """

        self.threads = []                                   # Running monitor threads(MonitorThread)
        """ :type: list of MonitorThread """

        self.apply_config(hub_config)

        self.hub_server = HubServer(self)                   # A bottle HTTP server.
        """ :type: HubServer """                            # Receive config from gateway.

    def apply_config(self, hub_config, load_old_config=False):
        """
        Update config of hub.
        If exception happens in initializing new sensors, old config will be reloaded.
        If exception happens while rolling back to old config, do nothing.

        :type hub_config: HubConfig
        New config to be load

        :type load_old_config: bool
        Should not set when called, used in case failed to load new config to prevent infinite loop.
        """
        logging.debug("[Hub.apply_config] hub_config=" + str(hub_config) + "load_old_config=" + str(load_old_config))

        # 1. Some type check
        if not isinstance(hub_config, HubConfig):
            raise TypeError("%s is not a HubConfig instance" % str(hub_config))

        # 2. Backup config
        self.old_config = self.config

        # 3. If new config has a different "hub_host" or "hub_port" from old one,
        # TODO run a shell script to restart whole program using new config because bottle cannot stop itself
        if (self.old_config is not None) and ((hub_config.hub_port != self.old_config.hub_port) or (hub_config.hub_host != self.old_config.hub_host)):
            self.restart_whole_server()

        # 4. Reset server, stopping sensors and monitor threads
        self.reset()

        # 5. Start new sensor and monitor threads
        try:
            self.config = hub_config
            for sensor_config in self.config.sensors:

                # Import sensor driver module by its type. Rule: module filename is "sensor_[type].py"
                sensor_module = import_module("module.hub.sensor_" + sensor_config["type"])

                # Prepare sensor monitor thread
                sensor = sensor_module.Sensor(sensor_config["id"], sensor_config["desc"], sensor_config["config"])
                thread = MonitorThread(sensor, self.config.gateway_addr, self.config.gateway_port, sensor_config["interval"])

                # Start sensor monitor thread
                thread.start()
                self.threads.append(thread)
                logging.debug("[Hub.apply_config] A sensor and its thread is started. sensorid=" + sensor.sensor_id + " thread=" + str(thread))

        except Exception as e:
            if load_old_config is not None:
                # Rolling back to old config
                logging.warn("[Hub.apply_config] Error occured while loading new config, rolling to old one")
                logging.warn("                   exception = " + str(e))
                rollback_config = self.old_config
                self.reset()
                self.apply_config(rollback_config, True)
            else:
                # Rolling back failed, raise exception
                # TODO consider load default config from .conf file?
                logging.warn("[Hub.apply_config] Error occured while rolling to old one, resetting hub")
                logging.warn("                   exception = " + str(e))
                self.reset()
                raise e

    def reset(self):
        """
        Clear config, clear threads, stop all sensors and monitor threads
        """
        logging.debug("[Hub.reset] resetting, sensor thread count: " + str(len(self.threads)))

        # stop all sensors & their monitor threads
        for thread in self.threads:
            thread.stop()
            logging.debug("[Hub.reset] MonitorThread" + str(thread) + " stopped. sensor_id=" + thread.sensor.sensor_id)

        self.threads = []
        self.config = None

    def restart_whole_server(self):
        """
        Stop current server process, run some script to restart whole program
        """
        # TODO do something
        logging.warn("[Hub.reload_whole_server] not implemented yet!")
        pass


def run_hub():
    """
    :rtype: Hub
    """
    from hubconfig import parse_from_file
    default_config = parse_from_file("config/hub.conf")            # Default config filename
    return Hub(default_config)                                     # Creating Hub starts HubServer as well