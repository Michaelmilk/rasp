__author__ = 'tgmerge'

from pinic.forwarder.forwarder import Forwarder
from pinic.forwarder.forwarderconfig import parse_from_file

if __name__ == "__main__":
    default_config = parse_from_file("config/forwarder.conf")
    Forwarder(default_config)  # Creating Hub starts HubServer as well

