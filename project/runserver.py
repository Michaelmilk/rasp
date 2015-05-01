from pinic.server.server import Server
from pinic.server.serverconfig import parse_from_file

if __name__ == "__main__":
    default_config = parse_from_file("config/server.conf")
    Server(default_config)  # Creating Hub starts HubServer as well

