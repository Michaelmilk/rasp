from pinic.node.node import Node
from pinic.node.nodeconfig import parse_from_file

if __name__ == "__main__":
    default_config = parse_from_file("config/node.conf")
    Node(default_config)  # Creating Hub starts HubServer as well

