# -*- coding: utf8 -*-

import logging

logging.basicConfig(level=logging.DEBUG)


class GatewayConfig(object):

    def __init__(self, json_str, config_dict):
        """
        :type json_str: basestring
        :type config_dict: dict
        See gateway.conf.md file.
        """

        self.json_str = json_str
        """ :type: basestring """

        self.dataserver_addr = config_dict["dataserver_addr"]
        """ :type: basestring """

        self.dataserver_port = config_dict["dataserver_port"]
        """ :type: int """

        self.gateway_id = config_dict["gateway_id"]
        """ :type: basestring """

        self.gateway_desc = config_dict["gateway_desc"]
        """ :type: basestring """

        self.gateway_host = config_dict["gateway_host"]
        """ :type: basestring """

        self.gateway_port = config_dict["gateway_port"]
        """ :type: int """

        self.hubs = config_dict["hubs"]
        """ :type: list of dict """

        self.filters = config_dict["filters"]
        """ :type: list of dict """

    def get_json_string(self):
        """
        Return parsed json string of this config

        Return
        ---------
        :rtype: str
        """
        return self.json_str


def parse_from_string(config_json):
    """
    Return a GatewayConfig, which is parsed from string

    Parameter
    ---------
    :type config_json: str
    a json string containing config

    Return
    ------
    :rtype: GatewayConfig
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
        ("dataserver_addr", basestring),
        ("dataserver_port", int),
        ("gateway_id", basestring),
        ("gateway_desc", basestring),
        ("gateway_host", basestring),
        ("gateway_port", int),
        ("hubs", list),
        ("filters", list)
    ]

    for (key, keyType) in valid_config_items:
        if key not in config:
            raise ValueError("key %s is not in config_json" % key)
        if not isinstance(config[key], keyType):
            raise ValueError("key %s is not '%s' instance" % (key, str(keyType)))

    logging.debug("[parse_from_string] Gateway config item checked")

    # Check second level items in "hubs" dict
    valid_hub_config_items = [
        ("hub_id", basestring),
        ("hub_desc", basestring),
        ("hub_addr", basestring),
        ("hub_port", int)
    ]

    for hub_config in config["hubs"]:
        for (key, keyType) in valid_hub_config_items:
            if key not in hub_config:
                raise ValueError("key '%s' is not in 'hubs' list in config_json" % key)
            if not isinstance(hub_config[key], keyType):
                raise ValueError("key '%s' is not '%s' instance in 'hubs' list" % (key, str(keyType)))

    logging.debug("[parse_from_string] Hub config item checked")

    # Check second level items in "filters" dict
    valid_filter_config_items = [
        ("apply_on_sensor_type", basestring),
        ("apply_on_sensor_id", basestring),
        ("comparing_method", basestring),
        ("threshold", float)
    ]

    for hub_config in config["filters"]:
        for (key, keyType) in valid_filter_config_items:
            if key not in hub_config:
                raise ValueError("key '%s' is not in 'filters' list in config_json" % key)
            if not isinstance(hub_config[key], keyType):
                raise ValueError("key '%s' is not '%s' instance in 'filters' list" % (key, str(keyType)))

    logging.debug("[parse_from_string] Filter config item checked")

    # Return a GatewayConfig object
    gateway_config = GatewayConfig(config_json, config)
    logging.debug("[parse_from_string] returning GatewayConfig " + str(gateway_config) + " addr=" + config["gateway_host"])
    return gateway_config


def parse_from_file(file_name):
    """
    Return a HubConfig, parsed from content of a text file.
    JSON.

    Parameter
    ---------
    :type file_name: str

    Return
    ------
    :rtype: GatewayConfig
    """

    json_file = open(file_name)
    json_str = json_file.read()
    return parse_from_string(json_str)
