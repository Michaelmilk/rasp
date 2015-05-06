__author__ = 'tgmerge'

import netifaces


def get_default_iface_mac():
    gateways = netifaces.gateways()
    default_iface = gateways['default'][netifaces.AF_INET][1]
    mac = netifaces.ifaddresses(default_iface)[netifaces.AF_LINK][0]['addr']
    return mac


if __name__ == "__main__":
    print get_default_iface_mac()