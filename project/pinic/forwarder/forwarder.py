# -*- coding: utf8 -*-

"""
本Python模块包含项目的Forwarder的服务器部分。
"""

__author__ = "tgmerge"


# 启用gevent环境支持
from gevent import monkey
monkey.patch_all()

# 外部模块
from bottle import Bottle, request, redirect, static_file
import grequests
from requests.exceptions import RequestException
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

# 项目内的其他模块
from pinic.forwarder.forwarderconfig import ForwarderConfig
from pinic.forwarder.forwarderconfig import parse_from_string as parse_forwarder_config_from_string
from pinic.server.serverconfig import parse_from_string as parse_server_config_from_string
from pinic.util import generate_500

# python内置模块
import logging
import threading
from time import time
from json import dumps


# 设置日志等级
logging.basicConfig(level=logging.DEBUG)


class WarningNamespace(BaseNamespace, BroadcastMixin):
    """
    继承Socket.IO的命名空间BaseNamespace。用于警报信息的实时推送。
    """

    # 当前已知的所有连接:
    connections = {}
    """ :type: dict[int, WarningNamespace] """

    def initialize(self):
        """
        初始化本命名空间。
        初始化后，命名空间即可用于SocketIO连接。
        """

        WarningNamespace.connections[id(self)] = self
        print "Socket.io - Init WarningNamespace, current %d alive" % len(WarningNamespace.connections)
        super(WarningNamespace, self).initialize()  # 调用父类的initialize方法

    def disconnect(self, silent=False):
        """
        处理SocketIO连接断开事件。

        :param silent: 是否对客户端静默，不对客户端返回任何断开确认信息。默认值为False（不静默）。
        """

        del WarningNamespace.connections[id(self)]
        print "Socket.io - Disconnect WarningNamespace, current %d alive" % len(WarningNamespace.connections)
        super(WarningNamespace, self).disconnect(silent)  # 调用父类的disconnect方法


class Forwarder(object):
    """
    本类是项目中的Forwarder服务器。运行指导参见pinic.forwarder.__init__.py的文档。
    """

    def __init__(self, forwarder_config):
        """
        :param ForwarderConfig forwarder_config: 初始化用的Forwarder配置（ForwarderConfig对象）。
        """

        self.config = None  # 类型：ForwarderConfig，是本服务器的当前配置

        self.bottle = Bottle()  # 类型：Bottle，是本服务器内含的Bottle Web服务器

        self.server_monitor = None  # 类型：ServerMonitor，是每隔一定时间监控Server存活的线程（已经被gevent patch过）

        self.known_servers = []  # 类型：list of ServerInfo，是已知的服务器信息的列表。

        # 应用初始化配置
        self.apply_config(forwarder_config)

        # 进行URL路由，并启动Bottle Web服务器
        self.start_bottle()

    # 行为抽象方法
    # ============

    def apply_config(self, new_config, load_old_config=False):
        """
        为Forwarder服务器应用新的配置。

        :param ForwarderConfig new_config: 要应用的新配置（ForwarderConfig对象）。
        :param bool load_old_config: 是否在失败时重新加载旧的配置，默认为False。
        """
        logging.debug("[Forwarder.apply_config] new_config=" + str(new_config) + " load_old_config=" + str(load_old_config))

        # 类型检查
        if not isinstance(new_config, ForwarderConfig):
            raise TypeError("%s is not a ForwarderConfig instance" % str(new_config))

        # 备份旧的配置
        old_config = self.config

        # 清空已知的Server列表，停止监视线程
        if self.server_monitor is not None:
            self.server_monitor.stop()

        # 将Forwarder的配置设置为新的配置
        self.config = new_config

        # 开启新的Server监视线程
        self.server_monitor = ServerMonitor(self)
        self.server_monitor.start()

        # 如果需要，重启整个服务器
        # TODO 由于需求变化，不实现
        if (old_config is not None) and ((new_config.forwarder_port != old_config.forwarder_port) or (new_config.forwarder_host != old_config.forwarder_host)):
            self.restart_bottle()

    def start_bottle(self):
        """
        进行URL路由，并开启Bottle Web服务器。
        """

        logging.debug("[Forwarder.start_bottle] starting bottle, forwarder_id=%s" % self.config.forwarder_id)

        # URL路由
        self.bottle.route("/forwarder/forwarderconfig", method="GET", callback=self.get_forwarder_config)
        self.bottle.route("/forwarder/forwarderconfig", method="POST", callback=self.post_forwarder_config)
        self.bottle.route("/forwarder/regserver", method="POST", callback=self.post_reg_server)
        self.bottle.route("/forwarder/unregserver", method="POST", callback=self.post_unreg_server)
        self.bottle.route("/forwarder/keepserver/<server_id>", method="GET", callback=self.get_keep_server)
        self.bottle.route("/forwarder/knownservers", method="GET", callback=self.get_known_servers)
        self.bottle.route("/forwarder/warningdata", method="POST", callback=self.post_warning_data)
        self.bottle.route("/server/<request_method>/<server_id>", method=["GET", "POST"], callback=self.server_method)
        self.bottle.route("/server/<request_method>/<server_id>/<other_ids:path>", method=["GET", "POST"], callback=self.server_method)

        # URL路由，静态页面部分
        self.bottle.route("/", method="GET", callback=lambda: redirect("/static/index.html"))
        self.bottle.route("/static/<path:path>", method="GET", callback=lambda path: static_file(path, root="static/"))

        # URL路由，Socket.IO部分
        self.bottle.route("/socket.io/<path:re:.*>", method="GET", callback=self.http_socket_io)

        # 开启Bottle
        self.bottle.run(
            host=self.config.forwarder_host,
            port=self.config.forwarder_port,
            server="geventSocketIO"
        )

    def restart_bottle(self):
        logging.debug("[Forwarder.restart_bottle] restarting bottle")
        pass

    def find_server_by_id(self, server_id):
        """
        在Forwarder的已知Server列表里按ID查找一个Server，并返回它（一个ServerInfo对象）。

        :param basestring server_id: 要查找的Server ID。

        :rtype ServerInfo:
        """
        for s in self.known_servers:
            if s.id == server_id:
                return s

    def remove_known_server(self, server_id):
        """
        从Forwarder的已知Server列表里按ID删除一个Server。

        :param basestring server_id: 要删除的Server的ID。
        """
        server_to_remove = self.find_server_by_id(server_id)
        if isinstance(server_to_remove, ServerInfo):
            logging.debug("[Forwarder.remove_known_server] removing server with server_id=%s" % server_id)
            self.known_servers.remove(server_to_remove)

    def add_known_server(self, server_addr, server_port, server_id, server_desc, server_config):
        """
        用Server的信息添加一个Server到已知Server列表里。

        :param basestring server_addr: 要添加的Server的地址
        :param int server_port: 要添加的Server的端口号
        :param basestring server_id: 要添加的Server的ID
        :param basestring server_desc: 要添加的Server的描述
        :param ServerConfig server_config: 要添加的Server的配置（一个ServerConfig对象）
        """
        logging.debug("[Forwarder.add_known_server] adding server with server_id=%s" % server_id)
        self.remove_known_server(server_id)
        self.known_servers.append(ServerInfo(server_addr, server_port, server_id, server_desc, server_config))

    def refresh_server_alive(self, server_id):
        """
        刷新已知Server列表中的一个Server的最后存活时间。
        具体方法是修改对应ServerInfo对象的last_active_time值，设置为调用这个方法的当前时间。
        如果一个Server长期没有被刷新（30s），将从已知Server列表中被删除。

        :param basestring server_id: 要刷新的Server的ID
        """

        server_to_refresh = self.find_server_by_id(server_id)
        if isinstance(server_to_refresh, ServerInfo):
            server_to_refresh.last_active_time = time()
        else:
            logging.warning("[Forwarder.refresh_server_alive] cannot find server with server_id=%s to refresh." % server_id)

    # HTTP处理方法
    # ============

    def http_socket_io(self, path):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理Socket.IO相关的URL，将socketIO数据发送给WarningNamespace处理。

        :param path: URL中的<path:path>部分，是需要交给SocketIO内部处理的参数。
        """
        socketio_manage(request.environ, {"/warning": WarningNamespace}, request=request)

    def post_warning_data(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理由Server向上发送的报警数据（HTTP POST）。
        报警数据以Json格式，在POST的正文中。
        接到数据后，将向SocketIO的WarningNamespace发送广播，将报警推送给客户端。
        """
        warning_data = request.body.read()

        # 向SocketIO的WarningNamespace发送广播
        for connection in WarningNamespace.connections.values():
            # 再次检查类型
            if isinstance(connection, WarningNamespace):
                connection.emit("warning", {"data": warning_data})

    def server_method(self, request_method, server_id, other_ids=None):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理由客户端发送的、目标为Server的各个请求。
        接到请求后，根据请求的目标ServerID在自己已知的Server列表中查找。
        如果找到，将请求转发给那个Server。
        如果找不到，返回HTTP 500。

        :param request_method: URL中的<request_method>部分，是请求的操作类型。
        :param server_id: URL中的<server_id>部分，是请求的目标Server的ID。
        :param other_ids: URL中的<other_ids:path>部分，即URL结尾的其他所有部分。将原样转发给目标Server。
        """

        # 1. 在自身已知的Server列表中查找URL中给出的目标Server
        server = self.find_server_by_id(server_id)
        if server is None:
            return generate_500("Can't find server with server_id=%s in this forwarder." % server_id)

        # 2. 根据请求URL构造要转发的新URL
        if other_ids is None:
            request_url = "http://%s:%d/server/%s/%s" % (server.addr, server.port, request_method, server_id)
        else:
            request_url = "http://%s:%d/server/%s/%s/%s" % (server.addr, server.port, request_method, server_id, other_ids)

        # 3. 转发新的请求给Server
        try:
            if request.method == "POST":
                greq = grequests.post(request_url, data=request.body.read())
            else:
                greq = grequests.get(request_url)
            response = greq.send()
        except RequestException as e:
            return generate_500("Error on curling to server.", e)

        # 4. 将从Server获得的响应转发回客户端，包括错误
        http_code = response.status_code
        if http_code == 500:
            return generate_500("Curling to server get 500. Response: %s", response.text)
        elif http_code == 200:
            return response.text
        else:
            return generate_500("Got unknown HTTP code: %d response: %s" % (http_code, response.text))

    def post_reg_server(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理由Server发送的注册请求（HTTP POST）。
        请求的正文包含Server的配置（ServerConfig）。
        收到请求后，本Forwarder在已知的Server列表中添加这个Server。
        """

        # 从请求的POST正文中解析Server的配置（ServerConfig）
        body = request.body.read()
        try:
            server_config = parse_server_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing server config.", e)

        # 添加Server
        server_addr = request.environ.get("REMOTE_ADDR")
        server_port = server_config.server_port
        server_id = server_config.server_id
        server_desc = server_config.server_desc
        self.add_known_server(server_addr, server_port, server_id, server_desc, server_config)
        return

    def post_unreg_server(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理由Server发送的解除注册请求（HTTP POST）。
        请求的正文包含Server的配置（ServerConfig）。
        收到请求后，本Forwarder在已知的Server列表中删除这个Server。
        """

        # 从请求的POST正文中解析Server的配置（ServerConfig）
        body = request.body.read()
        try:
            server_config = parse_server_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing server config.", e)

        # 从已知Server列表中删除这个Server
        server_id = server_config.server_id
        self.remove_known_server(server_id)
        return

    def get_keep_server(self, server_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理Server发来的心跳请求。请求的目的是证明Server依然存活，可以连通。
        如果某个Server长时间没有发送心跳请求（30s），认为它已经无法连接，它将被从Server列表中删除。

        :param server_id: URL中的<server_id>部分，即发送心跳的Server的ID。
        """

        # 在已知列表里查找这个Server
        server = self.find_server_by_id(server_id)
        if server is None:
            return generate_500("Cannot find server with server_id=%s from this forwarder" % server_id)

        # 刷新Server的最后存活时间
        self.refresh_server_alive(server_id)
        return

    def get_forwarder_config(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理客户端发来的请求，要求返回Forwarder的当前配置。
        方法将在HTTP GET的响应（HTTP 200）中返回Json格式的、本Forwarder的配置。
        """

        return self.config.get_json_string()

    def post_forwarder_config(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理客户端发来的请求（HTTP POST），要求更新Forwarder的当前配置。
        方法将试图解析POST正文中的新配置，并试图给Forwarder自身应用这个配置。
        如果中途出现错误，将返回HTTP 500错误，并在响应正文中附上错误的信息和产生的异常。
        如果没有出现错误，将返回HTTP 200正常响应，并在响应正文中附上更新后的配置，以供检查。
        """

        # 尝试解析POST正文中的ForwarderConfig
        try:
            new_config = parse_forwarder_config_from_string(request.body.read())
        except ValueError as e:
            return generate_500("Error on parsing new config.", e)

        # 尝试应用新的配置
        try:
            self.apply_config(new_config)
        except Exception as e:
            return generate_500("CAUTION: Error on applying new config.", e)

        # 返回更新后的配置
        return self.config.get_json_string()

    def get_known_servers(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理客户端发来的请求，返回Forwarder当前已知的Server列表。
        列表将以Json格式返回，返回的内容是ServerInfo的list。
        """

        result = []

        for s in self.known_servers:
            # 调用每个ServerInfo的get_dict方法，将ServerInfo的信息转换为字典，以供返回
            result.append(s.get_dict())

        # dumps是json.dumps，将result列表转换为Json字符串
        return dumps(result)


class ServerMonitor(threading.Thread):
    """
    ServerMonitor线程。已经被gevent monkey_patch成为greenlet。
    以一定间隔检查已知的Server列表，如果发现其中的Server超过一段时间（30秒）没有发送心跳请求，
    则将其从Forwarder的已知Server列表中删除。
    """

    def __init__(self, forwarder):
        """
        构造方法。

        :param Forwarder forwarder: 开启这个线程的Forwarder对象。
        """

        super(ServerMonitor, self).__init__()

        self.forwarder = forwarder  # 开启这个线程的Forwarder对象

        self.max_live_interval = 30.0  # Server不发送心跳请求后的最大存活时间

        self.check_interval = 10.0  # 执行检查的时间间隔

        self.stop_event = threading.Event()  # 本线程的停止事件。使用stop_event.set()可停止本线程，但更推荐使用ServerMonitor.stop()方法

    def run(self):
        """
        线程执行入口方法。
        间隔check_interval秒进行一次检查，删除太久没有发送心跳请求的Server。
        """

        while not self.stop_event.wait(self.check_interval):
            logging.debug("[ServerMonitor.run] checking %d known servers." % len(self.forwarder.known_servers))
            for s in self.forwarder.known_servers:
                if time() - s.last_active_time > self.max_live_interval:
                    self.forwarder.remove_known_server(s.id)
            logging.debug("[ServerMonitor.run] done. remain: %d known servers." % len(self.forwarder.known_servers))

    def stop(self):
        """
        停止这个线程。
        """

        self.stop_event.set()

class ServerInfo(object):
    """
    存放一个Server的信息。
    用途是，在Forwarder的known_servers列表中代表Forwarder已知的Server。
    """

    def __init__(self, addr, port, id, desc, config, last_active_time=None):
        """
        构造方法。

        :param basestring addr: Server的地址
        :param int port: Server的端口
        :param basestring id: Server的ID
        :param basestring desc: Server的描述
        :param ServerConfig config: Server的配置（ServerConfig）
        :param int last_active_time: Server的最后存活时间。如果为默认的None，则设置为当前时间。
        :return:
        """
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
        以字典形式返回这个Server的信息（地址，端口，ID，描述，最后存活时间）。

        :rtype: dict
        """
        return {
            "addr": self.addr,
            "port": self.port,
            "id": self.id,
            "desc": self.desc,
            "last_active_time": self.last_active_time
        }
