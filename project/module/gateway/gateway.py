# -*- coding: utf8 -*-

import logging
import pycurl

from gatewayserver import GatewayServer
from module.gateway import gatewayconfig
from module.hub.sensordata import SensorData


logging.basicConfig(level=logging.DEBUG)


class Gateway(object):
    """
    Gateway.
    Connect multiple hubs,
    read config from file,
    receive value from hubs,
    connect to dataserver,
    receive new config from gateway... etc
    """

    def __init__(self, gateway_config):
        """
        Gateway has a HubServer in instance.
        This method will run GatewayServer using params in gateway_config directly.

        Parameter
        ---------
        :type gateway_config:gatewayconfig.GatewayConfig
        """
        logging.debug("[Gateway.__init__] gateway_config=" + str(gateway_config))

        self.old_config = None
        """ :type: gatewayconfig.GatewayConfig """

        self.config = None
        """ :type: gatewayconfig.GatewayConfig """

        self.apply_config(gateway_config)

        self.gateway_server = GatewayServer(self, self.config.gateway_host, self.config.gateway_port)
        """ :type: GatewayServer """

        self.curl = pycurl.Curl()
        """ :type: pycurl.Curl """

    def apply_config(self, gateway_config, load_old_config=False):
        """
        Update config of gateway.

        Parameter
        ---------
        :type gateway_config: GatewayConfig
        New config to be load

        :type load_old_config: bool
        Should not set when called.
        Used in case that failed to load new config to prevent infinite loop.
        """
        logging.debug("[Gateway.apple_config] gateway_config=" + str(gateway_config) + "load_old_config=" + str(load_old_config))

        # Type check
        if gateway_config is None:
            return

        if not isinstance(gateway_config, gatewayconfig.GatewayConfig):
            raise TypeError("%s is not a GatewayConfig instance" % str(gateway_config))

        # 1. Replace config field
        self.old_config = self.config

        # 2. If new config has a different "gateway_host" or "gateway_port" from old one,
        # TODO run a shell script to start whole program using new config
        # TODO because bottle cannot stop itself
        if (self.old_config is not None) and ((gateway_config.gateway_port != self.old_config.gateway_port) or (gateway_config.gateway_host != self.old_config.gateway_host)):
            self.restart_whole_server()

        # 3. Reset server. Actually does nothing...
        self.reset()

        # 4. Start new... Wait, does nothing
        self.config = gateway_config

    def reset(self):
        """
        Nothing to do.
        """
        pass

    def restart_whole_server(self):
        """
        Stop current server process, run some script to restart whole program
        """
        # TODO do something
        logging.warn("[Gateway.reload_whole_server] not implemented yet!")
        pass

    def filter_and_send_sensor_data(self, sensor_data):
        """
        Filter SensorData using self.filter.
        If SensorData failed to pass any filter applied to it, ignore it.
        Otherwise, send it to DataServer.

        Parameter
        ---------
        :type sensor_data: SensorData
        """

        if not isinstance(sensor_data, SensorData):
            raise TypeError("sensor_data: %s is not a SensorData instance" % str(sensor_data))

        is_dropped = False

        for data_filter in self.config.filters:
            # Check "apply_on_sensor_type"
            if (data_filter["apply_on_sensor_type"] != "*") and (data_filter["apply_on_sensor_type"] != sensor_data.sensor_type):
                continue

            # Check "apply_on_sensor_id"
            if (data_filter["apply_on_sensor_id"] != "*") and (data_filter["apply_on_sensor_id"] != sensor_data.sensor_id):
                continue

            # Check method and threshold
            if (data_filter["comparing_method"] == "greater_than") and (sensor_data.raw_value > data_filter["threshold"]):
                is_dropped = True
                break
            if (data_filter["comparing_method"] == "less_than") and (sensor_data.raw_value < data_filter["threshold"]):
                is_dropped = True
                break

        if not is_dropped:
            # Send http request to dataserver
            request_url = str("http://%s:%d/dataserver/sensordata" % (self.config.dataserver_addr, self.config.dataserver_port))

            self.curl.setopt(pycurl.URL, request_url)
            self.curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            self.curl.setopt(pycurl.TIMEOUT, 30)
            self.curl.setopt(pycurl.POSTFIELDS, sensor_data.get_json_dumps())

            try:
                self.curl.perform()
            except Exception as e:
                logging.exception("[Gateway.filter_and_send_sensor_data] exception:" + str(e))


def run_gateway():
    """
    :rtype: Gateway
    """
    default_config = gatewayconfig.parse_from_file("config/gateway.conf")
    return Gateway(default_config)