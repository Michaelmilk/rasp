# -*- coding: utf8 -*-

__author__ = "tgmerge"


from gevent import monkey
monkey.patch_all()
from bottle import Bottle, request, redirect, static_file, ServerAdapter
import grequests
from requests.exceptions import RequestException
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from pinic.forwarder.forwarderconfig import ForwarderConfig
from pinic.forwarder.forwarderconfig import parse_from_string as parse_forwarder_config_from_string
from pinic.server.serverconfig import parse_from_string as parse_server_config_from_string
from pinic.util import generate_500
import logging
import threading
from time import time
from json import dumps

logging.basicConfig(level=logging.DEBUG)


class WarningNamespace(BaseNamespace, BroadcastMixin):

    # All alive sockets:
    connections = {}
    """ :type: dict[int, WarningNamespace] """

    def initialize(self):
        WarningNamespace.connections[id(self)] = self
        print "Socket.io - Init WarningNamespace, current %d alive" % len(WarningNamespace.connections)
        super(WarningNamespace, self).initialize()

    def disconnect(self, silent=False):
        del WarningNamespace.connections[id(self)]
        print "Socket.io - Disconnect WarningNamespace, current %d alive" % len(WarningNamespace.connections)
        super(WarningNamespace, self).disconnect(silent)


class Forwarder(object):
    """Forwarder"""

    def __init__(self, forwarder_config):
        """
        :param ForwarderConfig forwarder_config: 最初配置
        """

        self.config = None
        """ :type: ForwarderConfig """

        self.bottle = Bottle()
        """ :type: Bottle """

        self.server_monitor = None
        """ :type: ServerMonitor """

        self.known_servers = []
        """ :type: list of ServerInfo """

        self.apply_config(forwarder_config)
        self.start_bottle()

    # 行为方法
    # ========

    def apply_config(self, new_config, load_old_config=False):
        """
        :param ForwarderConfig new_config: -
        :param bool load_old_config: -
        """
        logging.debug("[Forwarder.apply_config] new_config=" + str(new_config) + " load_old_config=" + str(load_old_config))

        if not isinstance(new_config, ForwarderConfig):
            raise TypeError("%s is not a ForwarderConfig instance" % str(new_config))

        old_config = self.config

        if self.server_monitor is not None:
            self.server_monitor.stop()

        self.config = new_config

        self.server_monitor = ServerMonitor(self)
        self.server_monitor.start()

        if (old_config is not None) and ((new_config.forwarder_port != old_config.forwarder_port) or (new_config.forwarder_host != old_config.forwarder_host)):
            self.restart_bottle()

    def start_bottle(self):
        logging.debug("[Forwarder.start_bottle] starting bottle, forwarder_id=%s" % self.config.forwarder_id)

        self.bottle.route("/forwarder/forwarderconfig", method="GET", callback=self.get_forwarder_config)
        self.bottle.route("/forwarder/forwarderconfig", method="POST", callback=self.post_forwarder_config)

        self.bottle.route("/forwarder/regserver", method="POST", callback=self.post_reg_server)
        self.bottle.route("/forwarder/unregserver", method="POST", callback=self.post_unreg_server)
        self.bottle.route("/forwarder/keepserver/<server_id>", method="GET", callback=self.get_keep_server)

        self.bottle.route("/forwarder/knownservers", method="GET", callback=self.get_known_servers)

        self.bottle.route("/forwarder/warningdata", method="POST", callback=self.post_warning_data)

        self.bottle.route("/server/<request_method>/<server_id>", method=["GET", "POST"], callback=self.server_method)
        self.bottle.route("/server/<request_method>/<server_id>/<other_ids:path>", method=["GET", "POST"], callback=self.server_method)

        # 页面部分
        self.bottle.route("/", method="GET", callback=lambda: redirect("/static/index.html"))
        self.bottle.route("/static/<path:path>", method="GET", callback=lambda path: static_file(path, root="static/"))

        # Socket.io
        self.bottle.route("/socket.io/<path:re:.*>", method="GET", callback=self.http_socket_io)

        self.bottle.run(
            host=self.config.forwarder_host,
            port=self.config.forwarder_port,
            server="geventSocketIO"
        )  # todo 加锁？

    def restart_bottle(self):
        logging.debug("[Forwarder.restart_bottle] restarting bottle")
        # todo
        pass

    def find_server_by_id(self, server_id):
        """
        :rtype ServerInfo:
        """
        for s in self.known_servers:
            if s.id == server_id:
                return s

    def remove_known_server(self, server_id):
        server_to_remove = self.find_server_by_id(server_id)
        if isinstance(server_to_remove, ServerInfo):
            logging.debug("[Forwarder.remove_known_server] removing server with server_id=%s" % server_id)
            self.known_servers.remove(server_to_remove)

    def add_known_server(self, server_addr, server_port, server_id, server_desc, server_config):
        logging.debug("[Forwarder.add_known_server] adding server with server_id=%s" % server_id)
        self.remove_known_server(server_id)
        self.known_servers.append(ServerInfo(server_addr, server_port, server_id, server_desc, server_config))

    def refresh_server_alive(self, server_id):
        server_to_refresh = self.find_server_by_id(server_id)
        if isinstance(server_to_refresh, ServerInfo):
            server_to_refresh.last_active_time = time()
        else:
            logging.warning("[Forwarder.refresh_server_alive] cannot find server with server_id=%s to refresh." % server_id)

    # HTTP处理方法
    # ============

    def http_socket_io(self, path):
        socketio_manage(request.environ, {"/warning": WarningNamespace}, request=request)

    def post_warning_data(self):
        warning_data = request.body.read()

        # 向SocketIO的WarningNamespace发送广播
        for connection in WarningNamespace.connections.values():
            # double check, todo ADD LOCK
            if isinstance(connection, WarningNamespace):
                connection.emit("warning", {"data": warning_data})

    def server_method(self, request_method, server_id, other_ids=None):
        # 1. find server
        server = self.find_server_by_id(server_id)
        if server is None:
            return generate_500("Can't find server with server_id=%s in this forwarder." % server_id)

        # 2. construct new request
        if other_ids is None:
            request_url = "http://%s:%d/server/%s/%s" % (server.addr, server.port, request_method, server_id)
        else:
            request_url = "http://%s:%d/server/%s/%s/%s" % (server.addr, server.port, request_method, server_id, other_ids)

        # 3. send
        try:
            if request.method == "POST":
                greq = grequests.post(request_url, data=request.body.read())
            else:
                greq = grequests.get(request_url)
            response = greq.send()
        except RequestException as e:
            return generate_500("Error on curling to server.", e)

        # 4. throw response back
        http_code = response.status_code
        if http_code == 500:
            return generate_500("Curling to server get 500. Response: %s", response.text)
        elif http_code == 200:
            return response.text
        else:
            return generate_500("Got unknown HTTP code: %d response: %s" % (http_code, response.text))

    def post_reg_server(self):
        body = request.body.read()
        try:
            server_config = parse_server_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing server config.", e)

        server_addr = request.environ.get("REMOTE_ADDR")
        server_port = server_config.server_port
        server_id = server_config.server_id
        server_desc = server_config.server_desc
        self.add_known_server(server_addr, server_port, server_id, server_desc, server_config)
        return

    def post_unreg_server(self):
        body = request.body.read()
        try:
            server_config = parse_server_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing server config.", e)

        server_id = server_config.server_id
        self.remove_known_server(server_id)
        return

    def get_keep_server(self, server_id):
        server = self.find_server_by_id(server_id)
        if server is None:
            return generate_500("Cannot find server with server_id=%s from this forwarder" % server_id)

        self.refresh_server_alive(server_id)
        return

    def get_forwarder_config(self):
        return self.config.get_json_string()

    def post_forwarder_config(self):
        try:
            new_config = parse_forwarder_config_from_string(request.body.read())
        except ValueError as e:
            return generate_500("Error on parsing new config.", e)

        try:
            self.apply_config(new_config)
        except Exception as e:
            return generate_500("CAUTION: Error on applying new config.", e)

        return self.config.get_json_string()

    def get_known_servers(self):
        result = []

        for s in self.known_servers:
            result.append(s.get_dict())
        return dumps(result)


class ServerMonitor(threading.Thread):

    def __init__(self, forwarder):
        super(ServerMonitor, self).__init__()
        self.forwarder = forwarder
        self.max_live_interval = 30.0
        self.check_interval = 10.0
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.wait(self.check_interval):
            logging.debug("[ServerMonitor.run] checking %d known servers." % len(self.forwarder.known_servers))
            for s in self.forwarder.known_servers:
                if time() - s.last_active_time > self.max_live_interval:
                    self.forwarder.remove_known_server(s.id)
            logging.debug("[ServerMonitor.run] done. remain: %d known servers." % len(self.forwarder.known_servers))

    def stop(self):
        self.stop_event.set()

class ServerInfo(object):

    def __init__(self, addr, port, id, desc, config, last_active_time=None):
        self.addr = addr
        self.port = port
        self.id = id
        self.desc = desc
        self.config = config
        if last_active_time is None:
            self.last_active_time = time()
        else:
            self.last_active_time = last_active_time

    def get_dict(self):
        """
        :rtype: dict
        """
        return {
            "addr": self.addr,
            "port": self.port,
            "id": self.id,
            "desc": self.desc,
            "last_active_time": self.last_active_time
        }
