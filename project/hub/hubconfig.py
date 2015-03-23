# -*- coding: utf8 -*-
import logging

logging.basicConfig(level=logging.DEBUG)


class HubConfig(object):
    """
    Config of a Hub.

    Config item
    -----------
    see hub.conf.md file
    see parse_from_file() and parse_from_string()
    """

    def __init__(self, gateway_addr, gateway_port, hub_host, hub_port, sensors):
        """
        :type gateway_addr: basestring

        :type gateway_port: int

        :type hub_host: basestring

        :type hub_port: int

        :type sensors: list of dict
        List of sensor config. See hub.conf.md file.
        """
        self.gateway_addr = gateway_addr
        """ :type: basestring """

        self.gateway_port = gateway_port
        """ :type: int """

        self.hub_host = hub_host
        """ :type: basestring """

        self.hub_port = hub_port
        """ :type: int """

        self.sensors = sensors
        """ :type: list of dict"""


def parse_from_string(config_json):
    """
    Return a HubConfig, which is parsed from string

    Parameter
    ---------
    :type config_json: str
    a json string containing config

    Return
    ------
    :rtype: HubConfig
    object parsed from json.
    """

    logging.debug("[parse_from_string] parsing" + config_json[:20])

    # Parse json string to a dict
    from json import loads
    try:
        config = loads(config_json)
    except ValueError as e:
        raise e

    # Check first level items
    valid_config_items = [
        ("gateway_addr", basestring),
        ("gateway_port", int),
        ("hub_host", basestring),
        ("hub_port", int),
        ("sensors", list)
    ]

    for (key, keyType) in valid_config_items:
        if key not in config:
            raise ValueError("key '%s' is not in config_json" % key)
        if not isinstance(config[key], keyType):
            raise ValueError("key '%s' is not '%s' instance" % (key, str(keyType)))

    logging.debug("[parse_from_string] Hub config item checked")

    # Check second level items in "sensors" dict
    valid_sensor_config_items = [
        ("type", basestring),
        ("id", basestring),
        ("desc", basestring),
        ("interval", float)
    ]

    for sensor_config in config["sensors"]:
        for (key, keyType) in valid_sensor_config_items:
            if key not in sensor_config:
                raise ValueError("key '%s' is not in 'sensors' list in config_json" % key)
            if not isinstance(sensor_config[key], keyType):
                raise ValueError("key '%s' is not '%s' instance in 'sensors' list" % (key, str(keyType)))

    logging.debug("[parse_from_string] Sensor config item checked")

    # Return a HubConfig object
    hub_config = HubConfig(config["gateway_addr"], config["gateway_port"], config["hub_host"], config["hub_port"], config["sensors"])
    logging.debug("[parse_from_string] returning HubConfig " + str(hub_config) + " addr=" + config["gateway_addr"])
    return hub_config


def parse_from_file(file_name):
    """
    Return a HubConfig, parsed from content of a text file.
    JSON.

    Parameter
    ---------
    :type file_name: str

    Return
    ------
    :rtype: HubConfig
    """

    json_file = open(file_name)
    json_str = json_file.read()
    return parse_from_string(json_str)
