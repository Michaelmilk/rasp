# -*- coding: utf8 -*-

"""本Python模块是系统中Hub的主要功能部分。"""

__author__ = "tgmerge"


import logging
from importlib import import_module
from pinic.hub.monitorthread import MonitorThread
from pinic.hub.hubserver import HubServer
from pinic.hub.hubconfig import HubConfig

logging.basicConfig(level=logging.DEBUG)


class Hub(object):
    """Hub对象包含一个HubServer，能更新配置，并依据新配置载入传感器驱动模块并开启监视线程。"""

    def __init__(self, hub_config):
        """
        :param HubConfig hub_config: 最初配置
        """

        logging.debug("[Hub.__init__] hub_config=" + str(hub_config))

        self.old_config = None                              # Save old config when loading new one.
        """ :type: HubConfig """                            # Will be rolled back in case that new one failed to load.

        self.config = None                                  # Current hub config.
        """ :type: HubConfig """

        self.threads = []                                   # Running monitor threads(MonitorThread)
        """ :type: list of MonitorThread """

        self.apply_config(hub_config)

        self.hub_server = HubServer(self)                   # A bottle HTTP server. Receive config from gateway.

    def apply_config(self, hub_config, load_old_config=False):
        """
        更新这个Hub的配置。

        如果开启新的传感器监视线程时发生了异常，将回滚到旧的配置。

        如果这个回滚操作也发生了异常，将什么也不做并抛出它。

        :param HubConfig hub_config: 要载入的新配置
        :param bool load_old_config: 调用时无需设置。在载入失败时防止无限回滚使用。
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
                sensor_module = import_module("pinic.sensor.sensor_" + sensor_config["type"])

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
        """初始化Hub。包括清除配置、关闭所有传感器和它们的监视线程。"""
        logging.debug("[Hub.reset] resetting, sensor thread count: " + str(len(self.threads)))

        # stop all sensors & their monitor threads
        for thread in self.threads:
            thread.stop()
            logging.debug("[Hub.reset] MonitorThread" + str(thread) + " stopped. sensor_id=" + thread.sensor.sensor_id)

        self.threads = []
        self.config = None

    def restart_whole_server(self):
        """停止整个解释器进程，调用一些脚本重启整个程序，以改变如服务器端口一类的配置。"""
        # TODO do something
        logging.warn("[Hub.reload_whole_server] not implemented yet!")
        pass


def run_hub():
    """
    运行Hub。请使用runhub.py调用。

    :rtype: Hub
    """
    from hubconfig import parse_from_file
    default_config = parse_from_file("config/hub.conf")            # Default config filename
    return Hub(default_config)                                     # Creating Hub starts HubServer as well