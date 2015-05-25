# -*- coding: utf8 -*-

"""
本Python模块含有Server类，即系统中的Server部分。
这个包是项目的Server部分。

Server在启动时并不知道任何关于Node的信息。每一个Node启动后，
会自己向Server的/server/regnode注册，并以一定间隔发送心跳请求。

一段时间没有收到来自某个Node的心跳请求后，该Node将从已知Node列表中被删除。
"""

__author__ = "tgmerge"

# 启用gevent环境支持
from gevent import monkey
monkey.patch_all()

# 外部模块
import grequests
from requests.exceptions import RequestException
from bottle import Bottle, request

# 项目内的其他模块
from pinic.server.serverconfig import ServerConfig
from pinic.server.serverconfig import parse_from_string as parse_server_config_from_string
from pinic.util import generate_500
from pinic.node.nodeconfig import parse_from_string as parse_node_config_from_string
from pinic.node.nodeconfig import NodeConfig

# python内置模块
from time import time
from json import dumps, loads
import threading
import logging


# 设置日志等级
logging.basicConfig(level=logging.DEBUG)


class Server(object):
    """
    本类是项目中的Server服务器。运行指导参见pinic.server.__init__.py的文档
    """

    def __init__(self, server_config):
        """
        :param ServerConfig server_config: 初始化用的Server配置（ServerConfig对象）。
        """

        self.config = None                # 类型：ServerConfig，本Server当前的配置

        self.bottle = Bottle()            # 类型：Bottle，是本Server内含的Bottle Web服务器

        self.node_monitor = None          # 类型：NodeMonitor，定期检查Node的最后存活时间

        self.forwarder_monitor = None     # 类型：ForwarderMonitor，定期向Forwarder确认自身存活

        self.known_nodes = []             # 类型：list of NodeInfo，已知的node

        # 应用初始化配置
        self.apply_config(server_config)

        # 进行URL路由，并启动Bottle Web服务器
        self.start_bottle()

    # 行为抽象方法
    # ============

    def apply_config(self, new_config, load_old_config=False):
        """
        为Server服务器应用新的配置。

        :param ServerConfig new_config: 要应用的新配置（ServerConfig对象）。
        :param bool load_old_config: 是否在失败时重新加载旧的配置，默认为False。
        """
        logging.debug("[Server.apply_config] new_config=" + str(new_config) + "load_old_config=" + str(load_old_config))

        # 类型检查
        if not isinstance(new_config, ServerConfig):
            raise TypeError("%s is not a ServerConfig instance" % str(new_config))

        # 备份旧的配置
        old_config = self.config

        # 向Forwarder解除注册
        if self.forwarder_monitor is not None:
            self.forwarder_monitor.stop()
            self.forwarder_monitor.unreg_to_forwarder_destory_tunnel()

        # 停止Node监视线程
        if self.node_monitor is not None:
            self.node_monitor.stop()

        # 将Server的配置设置为新的配置
        self.config = new_config

        # 向Forwarder重新注册
        self.forwarder_monitor = ForwarderMonitor(self)
        self.forwarder_monitor.reg_to_forwarder_establish_tunnel()
        self.forwarder_monitor.start()

        # 启动新的Node监视线程
        self.node_monitor = NodeMonitor(self)
        self.node_monitor.start()

        # 如果需要，重启整个服务器
        # TODO 由于需求变化，不实现
        if (old_config is not None) and ((new_config.server_port != old_config.server_port) or (new_config.server_host != old_config.server_host)):
            self.restart_bottle()

    def start_bottle(self):
        """
        进行URL路由，并开启Bottle Web服务器。
        """

        logging.debug("[Server.start_bottle] starting bottle, server_id=%s" % self.config.server_id)

        # URL路由
        self.bottle.route("/server/regnode", method="POST", callback=self.post_reg_node)
        self.bottle.route("/server/unregnode", method="POST", callback=self.post_unreg_node)
        self.bottle.route("/server/keepnode/<node_id>", method="GET", callback=self.get_keep_node)
        self.bottle.route("/server/serverconfig/<server_id>", method="GET", callback=self.get_server_config)
        self.bottle.route("/server/serverconfig/<server_id>", method="POST", callback=self.post_server_config)
        self.bottle.route("/server/nodeconfig/<server_id>/<node_id>", method="GET", callback=self.get_node_config)
        self.bottle.route("/server/nodeconfig/<server_id>/<node_id>", method="POST", callback=self.post_node_config)
        self.bottle.route("/server/sensordata/<server_id>/<node_id>/<sensor_id>", method="GET", callback=self.get_sensor_data)
        self.bottle.route("/server/sensordata", method="POST", callback=self.post_sensor_data)
        self.bottle.route("/server/knownnodes/<server_id>", method="GET", callback=self.get_known_nodes)

        # 开启Bottle
        self.bottle.run(
            host=self.config.server_host,
            port=self.config.server_port,
            server="gevent"
        )

    def restart_bottle(self):
        logging.debug("[Server.restart_bottle] restarting bottle")
        pass

    def find_node_by_id(self, node_id):
        """
        在Server的已知Node列表里按ID查找一个Node，并返回它（一个NodeInfo对象）。

        :param basestring node_id: 要查找的Node ID。

        :rtype NodeInfo:
        """
        for n in self.known_nodes:
            if n.id == node_id:
                return n

    def remove_known_node(self, node_id):
        """
        从Server的已知Node列表里按ID删除一个Node。

        :param basestring node_id: 要删除的Node的ID。
        """
        node_to_remove = self.find_node_by_id(node_id)
        if isinstance(node_to_remove, NodeInfo):
            logging.debug("[Server.remove_known_node] removing node with node_id=%s" % node_id)
            self.known_nodes.remove(node_to_remove)

    def add_known_node(self, node_addr, node_port, node_id, node_desc, node_config):
        """
        用Node的信息添加一个Node到已知Node列表里。

        :param basestring node_addr: 要添加的Node的地址
        :param int node_port: 要添加的Node的端口号
        :param basestring node_id: 要添加的Node的ID
        :param basestring node_desc: 要添加的Node的描述
        :param NodeConfig node_config: 要添加的Node的配置（一个NodeConfig对象）
        """
        logging.debug("[Server.add_known_node] adding node with node_id=%s" % node_id)
        self.remove_known_node(node_id)
        self.known_nodes.append(NodeInfo(node_addr, node_port, node_id, node_desc, node_config))

    def refresh_node_alive(self, node_id):
        """
        刷新已知Node列表中的一个Node的最后存活时间。
        具体方法是修改对应NodeInfo对象的last_active_time值，设置为调用这个方法的当前时间。
        如果一个Node长期没有被刷新（30s），将从已知Node列表中被删除。

        :param basestring node_id: 要刷新的Node的ID
        """

        node_to_refresh = self.find_node_by_id(node_id)
        if isinstance(node_to_refresh, NodeInfo):
            node_to_refresh.last_active_time = time()
        else:
            logging.warning("[Server.refresh_node_alive] cannot find node with node_id=%s to refresh." % node_id)

    # HTTP处理方法
    # ============

    def post_reg_node(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理由Node发送的注册请求（HTTP POST）。
        请求的正文包含Node的配置（NodeConfig）。
        收到请求后，本Server在已知的Node列表中添加这个Node。
        """

        # 从请求的POST正文中解析Node的配置（NodeConfig）
        body = request.body.read()
        try:
            node_config = parse_node_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing node config.", e)

        # 添加Node
        node_addr = request.environ.get("REMOTE_ADDR")
        node_port = node_config.node_port
        node_id = node_config.node_id
        node_desc = node_config.node_desc
        self.add_known_node(node_addr, node_port, node_id, node_desc, node_config)
        return

    def post_unreg_node(self):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理由Node发送的解除注册请求（HTTP POST）。
        请求的正文包含Node的配置（NodeConfig）。
        收到请求后，本Server在已知的Node列表中删除这个Node。
        """

        # 从请求的POST正文中解析Node的配置（NodeConfig）
        body = request.body.read()
        try:
            node_config = parse_node_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing node config.", e)

        # 从已知Node列表中删除这个Node
        node_id = node_config.node_id
        self.remove_known_node(node_id)
        return

    def get_keep_node(self, node_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理Node发来的心跳请求。请求的目的是证明Node依然存活，可以连通。
        如果某个Node长时间没有发送心跳请求（30s），认为它已经无法连接，它将被从Node列表中删除。

        :param node_id: URL中的<node_id>部分，即发送心跳的Node的ID。
        """

        # 在已知列表里查找这个Node
        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" % node_id)

        # 刷新Node的最后存活时间
        self.refresh_node_alive(node_id)
        return

    def get_server_config(self, server_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理Forwarder发来的请求，要求返回Server的当前配置。
        方法将在HTTP GET的响应（HTTP 200）中返回Json格式的、本Server的配置。

        :param basestring server_id: URL中的<server_id>部分
        """

        # 检查URL中的server_id是否和自身的ID相符，如不符则返回HTTP 500
        if server_id == self.config.server_id:
            return self.config.get_json_string()
        else:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

    def post_server_config(self, server_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理Forwarder发来的请求（HTTP POST），要求更新Server的当前配置。
        方法将试图解析POST正文中的新配置，并试图给Server自身应用这个配置。
        如果中途出现错误，将返回HTTP 500错误，并在响应正文中附上错误的信息和产生的异常。
        如果没有出现错误，将返回HTTP 200正常响应，并在响应正文中附上更新后的配置，以供检查。

        :param basestring server_id: URL中的<server_id>部分。
        """

        # 检查URL中的server_id是否和自身的ID相符
        if server_id != self.config.server_id:
            return generate_500("Cannot find node with server_id='%s'" % server_id)

        # 尝试解析POST正文中的ServerConfig
        try:
            new_config = parse_server_config_from_string(request.body.read())
        except ValueError as e:
            return generate_500("Error on parsing new config.", e)

        # 尝试应用新的配置
        try:
            self.apply_config(new_config)
        except Exception as e:
            return generate_500("CAUTION: Error on applying new config.", e)

        # 返回更新后的配置
        return self.config.get_json_string()

    def get_node_config(self, server_id, node_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理Forwarder发来的请求，要求返回某个Node的当前配置。
        方法将在已知的Node列表中寻找node_id符合的Node，并发送请求返回它的配置。

        :param basestring server_id: URL中的<server_id>部分。
        :param basestring node_id: URL中的<node_id>部分。
        """

        # 检查URL中的server_id是否和自身的ID相符
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        # 在自身已知的Server列表里查找URL中给出的目标Node
        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" % node_id)

        # 向那个Node发送请求
        request_url = str("http://%s:%d/node/nodeconfig/%s" % (node.addr, node.port, node.id))
        try:
            greq = grequests.get(request_url)
            response = greq.send()
        except RequestException as e:
            return generate_500("Error on curling config from node.", e)

        # 向Forwarder返回结果
        return response.text

    def post_node_config(self, server_id, node_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理Forwarder发来的请求（HTTP POST），要求更新某个Node的当前配置。
        新的配置以Json格式在HTTP POST的正文中。
        方法将在已知的Node列表中寻找node_id符合的Node，并发送请求更新它的配置。

        :param basestring server_id: URL中的<server_id>部分。
        :param basestring node_id: URL中的<node_id>部分。
        """

        # 检查URL中的server_id是否和自身的ID相符
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        # 在自身已知的Server列表里查找URL中给出的目标Node
        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" % node_id)

        # 向那个Node发送请求
        request_url = str("http://%s:%d/node/nodeconfig/%s" % (node.addr, node.port, node.id))
        try:
            greq = grequests.post(request_url, data=request.body.read())
            response = greq.send()
        except RequestException as e:
            return generate_500("Error on sending config to node.", e)

        # 向Forwarder返回请求的结果
        return response.text

    def get_sensor_data(self, server_id, node_id, sensor_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理Forwarder发来的请求，要求获得某个传感器的传感器值。
        方法将把请求转发给相应的Node，并把获得的响应转发回Forwarder。
        目标传感器的值（SensorData）以Json形式在响应中返回。
        """

        # 检查URL中的server_id是否和自身的ID相符
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        # 在自身已知的Server列表里查找URL中给出的目标Node
        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" % node_id)

        # 向那个Node发送请求
        request_url = str("http://%s:%d/node/sensordata/%s/%s" % (node.addr, node.port, node_id, sensor_id))
        try:
            greq = grequests.get(request_url)
            response = greq.send()
        except RequestException as e:
            return generate_500("Error on sending config to node.", e)

        # 向Forwarder返回请求的结果
        return response.text

    def post_sensor_data(self):
        """
        处理POST /server/sensordata，即Node主动发送的传感器值。
        由于需求变更，本方法现在没有作用。
        参见Git commit记录：699b6bc7aefe64eab56f5d9727ec341e001d0e4a
        """
        request_url = str("http://%s:%d/forwarder/sensordata" % (self.config.forwarder_addr, self.config.forwarder_port))
        try:
            greq = grequests.post(request_url, data=request.body.read())
            response = greq.send()
        except RequestException as e:
            return generate_500("Error on send sensordata to forwarder.", e)
        return  # HTTP 200

    def get_known_nodes(self, server_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理Forwarder发来的请求，返回Server当前已知的Node列表。
        列表将以Json格式返回，返回的内容是NodeInfo的list。
        """

        # 检查URL中的server_id是否和自身的ID相符
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        result = []

        for n in self.known_nodes:
            # 调用每个NodeInfo的get_dict方法，将NodeInfo的信息转换为字典，以供返回
            result.append(n.get_dict())
        return dumps(result)


class NodeMonitor(threading.Thread):
    """
    NodeMonitor线程。已经被gevent monkey_patch成为greenlet。
    以一定间隔检查已知的Node列表，如果发现其中的Node超过一段时间（30秒）没有发送心跳请求，
    则将其从Server的已知Node列表中删除。
    """

    def __init__(self, server):
        """
        构造方法。

        :param Server server: 开启这个线程的server对象。
        """

        super(NodeMonitor, self).__init__()

        self.server = server  # 开启这个线程的Server对象

        self.max_live_interval = 30.0  # Node不发送心跳请求后的最大存活时间

        self.check_interval = 5.0  # 执行检查的时间间隔

        self.stop_event = threading.Event()  # 本线程的停止事件。使用stop_event.set()可停止本线程，但更推荐使用NodeMonitor.stop()方法

    def check_warning(self, node_info):
        """
        检查一个Node的所有Sensor是否超过警报阈值。如果有，发送数据给forwarder。

        :param NodeInfo node_info: node to check
        """
        # 对node的每一个传感器……
        for sensor in node_info.config.sensors:
            request_url = "http://%s:%d/node/warningdata/%s/%s" % (node_info.addr, node_info.port, node_info.id, sensor["sensor_id"])
            try:
                # 检查是否有警报
                greq = grequests.get(request_url)
                response = greq.send()
                # 有警报数据，发送给forwarder
                if len(response.text) > 0:
                    request_url = "http://%s:%d/forwarder/warningdata" % (self.server.config.forwarder_addr, self.server.config.forwarder_port)
                    warning_json_obj = loads(response.text)
                    warning_json_obj["node"] = node_info.get_dict()
                    warning_json_obj["server"] = self.server.config.server_id
                    greq = grequests.post(request_url, data=dumps(warning_json_obj))
                    response = greq.send()
            except RequestException as e:
                logging.debug("[Exception on check_warning]" + str(e))
                pass

    def run(self):
        """
        线程执行入口方法。
        间隔check_interval秒进行一次检查，删除太久没有发送心跳请求的Node。
        """
        while not self.stop_event.wait(self.check_interval):
            logging.debug("[NodeMonitor.run] checking %d known nodes." % len(self.server.known_nodes))
            for n in self.server.known_nodes:
                if time() - n.last_active_time > self.max_live_interval:
                    self.server.remove_known_node(n.id)
                else:
                    self.check_warning(n)
            logging.debug("[NodeMonitor.run] done. remain: %d known nodes." % len(self.server.known_nodes))

    def stop(self):
        """
        停止这个线程。
        """

        self.stop_event.set()


class ForwarderMonitor(threading.Thread):
    """
    Forwarder监视线程，定期向Forwarder发送/forwarder/keepsensor/<sensor_id>以表明自己存活。
    """

    def __init__(self, server):
        """
        初始化。

        :param Server server: 开启此线程的Server
        """
        super(ForwarderMonitor, self).__init__()
        # 参数
        self.server = server
        self.forwarder_addr = server.config.forwarder_addr
        self.forwarder_port = server.config.forwarder_port
        self.server_id = server.config.server_id
        self.keep_alive_interval = 10.0  # 秒
        self.stop_event = threading.Event()  # 设置停止事件

    def reg_to_forwarder_establish_tunnel(self):
        """
        向Forwarder注册Server。发送一个POST请求到Forwarder的``/forwarder/regserver``，请求内容是Server的config。
        """
        logging.debug("[ForwarderMonitor.reg_to_forwarder_establish_tunnel] reg to forwarder. addr=%s, port=%d" % (self.forwarder_addr, self.forwarder_port))
        request_url = str("http://%s:%d/forwarder/regserver" % (self.forwarder_addr, self.forwarder_port))
        try:
            greq = grequests.post(request_url, data=self.server.config.get_json_string())
            greq.send()
        except RequestException as e:
            logging.warning("[ServerMonitor.reg_to_server] reg failed. err:" + str(e))

    def unreg_to_forwarder_destory_tunnel(self):
        """
        向Forwarder解除注册Server。发送一个POST请求到Forwarder的``/server/unregserver``，请求内容是Server的config。
        """
        logging.debug("[ForwarderMonitor.unreg_to_forwarder_destory_tunnel] unreg to forwarder. addr=%s, port=%d" % (self.forwarder_addr, self.forwarder_port))
        request_url = str("http://%s:%d/forwarder/unregserver" % (self.forwarder_addr, self.forwarder_port))
        try:
            greq = grequests.post(request_url, data=self.server.config.get_json_string())
            greq.send()
        except RequestException as e:
            logging.warning("[ServerMonitor.reg_to_server] reg failed. err:" + str(e))

    def send_keep_server(self):
        """
        向Forwarder的/forwarder/keepserver/<server_id>发送一个GET，证明自身存活
        如果返回200，说明正常
        如果返回500，说明Forwarder尚不知道自身，故进行reg_to_forwarder向Forwarder注册自己。
        """
        logging.debug("[ForwarderMonitor.send_keep_server] sending keep_server message")
        request_url = str("http://%s:%d/forwarder/keepserver/%s" % (self.forwarder_addr, self.forwarder_port, self.server_id))
        try:
            greq = grequests.get(request_url)
            response = greq.send()
            if response.status_code == 500:
                self.unreg_to_forwarder_destory_tunnel()
                self.reg_to_forwarder_establish_tunnel()
        except Exception as e:
            logging.exception("[ForwarderMonitor.send_keep_node] exception:" + str(e))

    def run(self):
        """
        ForwarderMonitor以如下方式运行。

        每self.keep_alive_interval秒，运行send_keep_server，发送自身存活消息。
        """
        while not self.stop_event.wait(self.keep_alive_interval):
            self.send_keep_server()
            # self.check_reverse_tunnel()

    def stop(self):
        self.stop_event.set()


class NodeInfo(object):
    """
    表示一个Node的信息，在Server中使用，包含addr, port, id, desc属性。
    last_active_time是node最后一次发送keepnode证明自己存活的时间。
    新建NodeInfo对象时，last_active_time默认为当前时间。
    """

    def __init__(self, addr, port, id, desc, config, last_active_time=None):
        """
        构造方法。

        :param basestring addr: node address
        :param int port: node port
        :param basestring id: node id
        :param basestring desc: node desc
        :param NodeConfig config: node config
        :param float last_active_time: last active timestamp
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
        以dict的形式返回自身信息。

        :rtype: dict
        """
        return {
            "addr": self.addr,
            "port": self.port,
            "id": self.id,
            "desc": self.desc,
            "last_active_time": self.last_active_time
        }
