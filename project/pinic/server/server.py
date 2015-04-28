# -*- coding: utf8 -*-

"""
本Python模块含有Server类，即系统中的Server部分。

Server在启动时并不知道任何关于Node的信息。每一个Node启动后，
会自己向Server的/server/regnode注册。

为验证Server当前所知的Node是否存活，Server会间隔一定时间，
使用NodeMonitorThread向Node的/heartbeat/<node_id>验证。
连续失败一定次数之后，Server即认为这个Node处于异常状态，
并放慢验证间隔（<--TODO 待定）。

关于反向代理……

Server启动后，先向Forwarder发出请求，获取可用的ssh端口。

Forwarder记录Server和端口之间的对应关系。

之后使用ssh反向代理： Server --> Forwarder

Server向Forwarder的通信：直接发送给Forwarder的IP

Forwarder向Server的通信：发送给自身的相应端口

模块线程
========

::

    Main ----------- Main           # 服务器线程
                |
                ---- NodeMonitor(s) # Node监视线程，监视其存活

方法流程
========

::

    On start:
        1. Load config from default path
        Start 
        2. Start bottle
        3. Reg to forwarder
        4. get forwarder's ssh port
        5. open ssh reverse tunnel

    POST /server/regnode
        parse nodeconfig from post load
        get origin ip from wsgi
        save (ip, port, id) to known nodes list
        start a thread to keep it alive

    POST /server/unregnode
        parse nodeconfig from post load
        get origin ip from wsgi
        find (ip, port, id) from known nodes list
        if found, remove it
        stop thread

    GET /server/serverconfig/server_id
        similiar to node

    POST /server/serverconfig/server_id
        similiar to node

    GET /server/nodeconfig/server_id/node_id
        find node_id in known node list
        if found, curl get /node/nodeconfig/node_id, return that

    POST /server/serverconfig/server_id/node_id
        find node_id in known node list
        if found, curl post /node/nodeconfig/node_id, return its response

    POST /server/sensordata
        curl to forwarder

"""

__author__ = "tgmerge"


from gevent import monkey
monkey.patch_all()
import logging
import threading
import pycurl
from pinic.server.serverconfig import ServerConfig
from pinic.server.serverconfig import parse_from_string as parse_server_config_from_string
from pinic.util import generate_500, TimeoutError
from pinic.node.nodeconfig import parse_from_string as parse_node_config_from_string
from bottle import Bottle, request
from StringIO import StringIO
from time import time


logging.basicConfig(level=logging.DEBUG)


class Server(object):
    """Server"""

    def __init__(self, server_config):
        """
        :param ServerConfig server_config: 最初配置
        """

        self.config = None                # Server当前的配置
        """ :type: ServerConfig """

        self.bottle = Bottle()            # 服务器bottle
        """ :type: Bottle """

        self.node_monitor = None          # 定期检查Node的最后存活时间
        """ :type: NodeMonitor """

        self.forwarder_monitor = None     # 定期向Forwarder确认自身存活
        """ :type: ForwarderMonitor """

        self.known_nodes = []             # 已知的node
        """ :type: list of NodeInfo"""

        self.apply_config(server_config)  # 1. 应用配置，向forwarder注册
        self.start_bottle()         # 2. 启动bottle

    # 行为方法
    # ========

    def apply_config(self, new_config, load_old_config=False):
        """
        更新这个Gateway的配置。
        如果开启新的传感器监视线程时发生了异常，将回滚到旧的配置。
        如果这个回滚操作也发生了异常，将什么也不做并抛出它。

        :param ServerConfig new_config: 要载入的新配置
        :param bool load_old_config: 调用时无需设置。在载入失败时防止无限回滚使用。
        """
        logging.debug("[Server.apply_config] new_config=" + str(new_config) + "load_old_config=" + str(load_old_config))

        if not isinstance(new_config, ServerConfig):
            raise TypeError("%s is not a ServerConfig instance" % str(new_config))

        old_config = self.config

        if self.forwarder_monitor is not None:
            self.forwarder_monitor.stop()
            self.forwarder_monitor.unreg_to_forwarder_destory_tunnel()

        if self.node_monitor is not None:
            self.node_monitor.stop()

        self.config = new_config

        self.forwarder_monitor = ForwarderMonitor(self)
        self.forwarder_monitor.reg_to_forwarder_establish_tunnel()
        self.forwarder_monitor.start()

        self.node_monitor = NodeMonitor(self)
        self.node_monitor.start()

        # 6. 如果新配置的node_host或node_port与旧配置不同，
        # TODO 执行shel脚本以重启整个应用
        if (old_config is not None) and ((new_config.server_port != old_config.server_port) or (new_config.server_host != old_config.server_host)):
            self.restart_bottle()

    def start_bottle(self):
        """
        启动Node的Bottle服务器。
        """
        # URL路由
        logging.debug("[Server.start_bottle] starting bottle, server_id=%s" % self.config.server_id)

        self.bottle.route("/server/regnode", method="POST", callback=self.post_reg_node)
        self.bottle.route("/server/unregnode", method="POST", callback=self.post_unreg_node)
        self.bottle.route("/server/keepnode/<node_id>", method="GET", callback=self.get_keep_node)

        self.bottle.route("/server/serverconfig/<server_id>", method="GET", callback=self.get_server_config)
        self.bottle.route("/server/serverconfig/<server_id>", method="POST", callback=self.post_server_config)

        self.bottle.route("/server/nodeconfig/<server_id>/<node_id>", method="GET", callback=self.get_node_config)
        self.bottle.route("/server/nodeconfig/<server_id>/<node_id>", method="POST", callback=self.post_node_config)

        self.bottle.route("/server/sensordata/<server_id>/<node_id>/<sensor_id>", method="GET", callback=self.get_sensor_data)
        self.bottle.route("/server/sensordata", method="POST", callback=self.post_sensor_data)

        self.bottle.run(
            host=self.config.server_host,
            port=self.config.server_port,
            server="gevent"
        )  # TODO 使用Node时加锁

    def restart_bottle(self):
        """
        重启整个bottle。
        """
        logging.debug("[Server.restart_bottle] restarting bottle")
        # todo
        pass

    def find_node_by_id(self, node_id):
        """
        按node_id在已知Node列表中查找Node并返回它。找不到则返回None。

        :rtype: NodeInfo
        """
        for n in self.known_nodes:
            if n.id == node_id:
                return n

    def remove_known_node(self, node_id):
        """
        按node_id从已知的Node列表中删除一个Node。
        如果找不到，什么也不做。
        """
        node_to_remove = self.find_node_by_id(node_id)
        if isinstance(node_to_remove, NodeInfo):
            logging.debug("[Server.remove_known_node] removing node with node_id=%s" % node_id)
            self.known_nodes.remove(node_to_remove)

    def add_known_node(self, node_addr, node_port, node_id, node_desc):
        """
        添加一个Node到已知Node列表。如果已经有相同ID的Node存在，则覆盖它/它们。

        :param basestring node_addr: node addr
        :param int node_port: node port
        :param basestring node_id: node id
        :param basestring node_desc: node desc
        """
        logging.debug("[Server.add_known_node] adding node with node_id=%s" % node_id)
        self.remove_known_node(node_id)
        self.known_nodes.append(NodeInfo(node_addr, node_port, node_id, node_desc))

    def refresh_node_alive(self, node_id):
        """
        刷新一个Node（按node_id查找)的last_active_time为当前时间。
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
        处理POST /server/regnode。
        如果成功，返回HTTP 200。
        1. 解析POST内容为node_config
        2. 获取请求的IP地址、端口、node信息
        3. 添加到已知node列表
        4. 返回200
        """
        body = request.body.read()
        try:
            node_config = parse_node_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing node config.", e)

        node_addr = request.environ.get("REMOTE_ADDR")
        node_port = node_config.node_port
        node_id = node_config.node_id
        node_desc = node_config.node_desc
        self.add_known_node(node_addr, node_port, node_id, node_desc)
        return

    def post_unreg_node(self):
        """
        处理POST /server/unregnode，
        如果成功，返回HTTP 200。
        1. 解析POST内容为node_config
        2. 获取请求的IP地址、端口、node信息
        3. 从已知node列表清除node
        4. 返回200
        """
        body = request.body.read()
        try:
            node_config = parse_node_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing node config.", e)

        node_id = node_config.node_id
        self.remove_known_node(node_id)
        return

    def get_keep_node(self, node_id):
        """
        处理GET /server/keepnode/<node_id>。
        如果成功，返回HTTP 200。
        如果找不到Node之类，返回http 500。
        """
        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" % node_id)

        self.refresh_node_alive(node_id)
        return

    def get_server_config(self, server_id):
        """
        处理GET /server/serverconfig/<server_id>。
        以Json形式返回Server的当前配置。
        如果请求错误或出现异常，返回HTTP 500。
        1. 检查server_id:
        2. 返回server_config:

        :param basestring server_id: URL中的<server_id>部分。
        """
        if server_id == self.config.server_id:
            return self.config.get_json_string()
        else:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

    def post_server_config(self, server_id):
        """
        处理POST /server/serverconfig/<server_id>。
        以Json形式返回新的Server配置。
        如果请求错误或出现异常，返回HTTP 500。
        # 1. 检查server_id:
        # 2. 解析新的server_config:
        # 3. 应用新的server_config：
        # 4. 成功，返回新的配置

        :param basestring server_id: URL中的<server_id>部分。
        """
        if server_id != self.config.server_id:
            return generate_500("Cannot find node with server_id='%s'" % server_id)

        try:
            new_config = parse_server_config_from_string(request.body.read())
        except ValueError as e:
            return generate_500("Error on parsing new config.", e)

        try:
            self.apply_config(new_config)
        except Exception as e:
            return generate_500("CAUTION: Error on applying new config.", e)

        return self.config.get_json_string()

    def get_node_config(self, server_id, node_id):
        """
        处理GET /server/nodeconfig/<server_id>/<node_id>
        如果成功，返回HTTP 200，内容为node的当前配置。
        # 1. 检查server_id
        # 2. 查找node_id
        # 3. 发送GET /node/nodeconfig/<node_id>
        # 4. 原样返回上面的发送结果

        :param basestring server_id: URL中的<server_id>部分。
        :param basestring node_id: URL中的<node_id>部分。
        """

        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" % node_id)

        request_url = str("http://%s:%d/node/nodeconfig/%s" % (node.addr, node.port, node.id))
        try:
            curl_buffer = StringIO()
            curl = pycurl.Curl()
            curl.setopt(pycurl.URL, request_url)
            curl.setopt(pycurl.WRITEDATA, curl_buffer)
            curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            curl.setopt(pycurl.TIMEOUT, 30)
            curl.perform()
        except pycurl.error as e:
            return generate_500("Error on curling config from node.", e)

        return curl_buffer.getvalue()

    def post_node_config(self, server_id, node_id):
        """
        处理POST /server/nodeconfig/<server_id>/<node_id>
        如果成功，返回HTTP 200，内容为node的新配置。
        # 1. 检查server_id
        # 2. 查找node_id
        # 3. 发送POST /node/nodeconfig/<node_id>
        # 4. 原样返回上面的发送结果

        :param basestring server_id: URL中的<server_id>部分。
        :param basestring node_id: URL中的<node_id>部分。
        """

        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" % node_id)

        request_url = str("http://%s:%d/node/nodeconfig/%s" % (node.addr, node.port, node.id))
        curl_buffer = StringIO()
        try:
            curl = pycurl.Curl()
            curl.setopt(pycurl.URL, request_url)
            curl.setopt(pycurl.POSTFIELDS, request.body.read())
            curl.setopt(pycurl.WRITEDATA, curl_buffer)
            curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            curl.setopt(pycurl.TIMEOUT, 30)
            curl.perform()
        except pycurl.error as e:
            return generate_500("Error on sending config to node.", e)

        return curl_buffer.getvalue()

    def get_sensor_data(self, server_id, node_id, sensor_id):
        """
        处理GET /server/sensordata/<server_id>/<node_id>/<sensor_id>
        如果成功，返回传感器数据（Json格式的SensorData）。
        # 1. 检查server_id
        # 2. 查找node_id
        # 3. 发送GET /node/sensordata/<sensor_id>
        # 4. 原样返回收到的数据
        """
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        node = self.find_node_by_id(node_id)
        if node is None:
            return generate_500("Cannot find node with node_id='%s' from this server" & node_id)

        request_url = str("http://%s:%d/node/sensordata/%s" % (node.addr, node.port, sensor_id))
        curl_buffer = StringIO()
        try:
            curl = pycurl.Curl()
            curl.setopt(pycurl.URL, request_url)
            curl.setopt(pycurl.WRITEDATA, curl_buffer)
            curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            curl.setopt(pycurl.TIMEOUT, 30)
            curl.perform()
        except pycurl.error as e:
            return generate_500("Error on sending config to node.", e)

        return curl_buffer.getvalue()

    def post_sensor_data(self):
        """
        处理POST /server/sensordata。
        如果成功，返回HTTP 200，数据将原样递交给Forwarder。
        如果失败，返回HTTP 500(todo)。
        """
        request_url = str("http://%s:%d/forwarder/sensordata" % (self.config.forwarder_addr, self.config.forwarder_port))
        try:
            curl = pycurl.Curl()
            curl.setopt(pycurl.URL, request_url)
            curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            curl.setopt(pycurl.TIMEOUT, 30)
            curl.setopt(pycurl.POSTFIELDS, request.body.read())
            curl.perform()
        except pycurl.error as e:
            return generate_500("Error on send sensordata to forwarder.", e)
        return  # HTTP 200


class NodeMonitor(threading.Thread):
    """Node监视线程，定期检查已知Node的最后存活时间，如果超出限制则从已知Node列表中清除Node"""

    def __init__(self, server):
        """
        初始化

        :param Server server: 开启此线程的Server
        """
        super(NodeMonitor, self).__init__()
        self.server = server
        self.max_live_interval = 30.0  # 秒，超过这个限制则认为已经无连接
        self.check_interval = 10.0  # 秒，检查间隔
        self.stop_event = threading.Event()  # 设置停止事件

    def run(self):
        """
        检查Server中各个已知Node的最后存活时间是否超出max_live_interval，如果超过，将它从已知的node列表中去除。
        TODO 加锁
        """
        while not self.stop_event.wait(self.check_interval):
            logging.debug("[NodeMonitor.run] checking %d known nodes." % len(self.server.known_nodes))
            for n in self.server.known_nodes:
                if time() - n.last_active_time > self.max_live_interval:
                    self.server.remove_known_node(n.id)
            logging.debug("[NodeMonitor.run] done. remain: %d known nodes." % len(self.server.known_nodes))

    def stop(self):
        self.stop_event.set()


class ForwarderMonitor(threading.Thread):
    """
    Forwarder监视线程，定期向Forwarder发送/forwarder/keepsensor/<sensor_id>以表明自己存活。
    另外，还定期检查ssh隧道是否可用。如果变得不可用，将断开并尝试重新向Forwarder重新注册和连接隧道。
    """

    def __init__(self, server):
        """
        初始化。

        :param Server server: 开启此线程的Server
        TODO 加锁
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
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.POSTFIELDS, self.server.config.get_json_string())
        curl.perform()
        # todo 建立反向隧道

    def unreg_to_forwarder_destory_tunnel(self):
        """
        向Forwarder解除注册Server。发送一个POST请求到Forwarder的``/server/unregserver``，请求内容是Server的config。
        """
        logging.debug("[ForwarderMonitor.unreg_to_forwarder_destory_tunnel] unreg to forwarder. addr=%s, port=%d" % (self.forwarder_addr, self.forwarder_port))
        request_url = str("http://%s:%d/forwarder/unregserver" % (self.forwarder_addr, self.forwarder_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.POSTFIELDS, self.server.config.get_json_string())
        curl.perform()
        # todo 关闭反向隧道

    def check_reverse_tunnel(self):
        """
        检查反向隧道是否可用。
        """
        pass  # todo

    def send_keep_server(self):
        """
        向Forwarder的/forwarder/keepserver/<server_id>发送一个GET，证明自身存活
        如果返回200，说明正常
        如果返回500，说明Forwarder尚不知道自身，故进行reg_to_forwarder向Forwarder注册自己。
        """
        logging.debug("[ForwarderMonitor.send_keep_server] sending keep_server message")
        request_url = str("http://%s:%d/forwarder/keepserver/%s" % (self.forwarder_addr, self.forwarder_port, self.server_id))
        try:
            curl = pycurl.Curl()
            curl.setopt(pycurl.URL, request_url)
            curl.setopt(pycurl.CONNECTTIMEOUT, 10)
            curl.setopt(pycurl.TIMEOUT, 30)
            curl.perform()
            if curl.getinfo(pycurl.HTTP_CODE) == '500':
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
            self.check_reverse_tunnel()

    def stop(self):
        self.stop_event.set()


class NodeInfo(object):
    """
    表示一个Node的信息，在Server中使用，包含addr, port, id, desc属性。
    last_active_time是node最后一次发送keepnode证明自己存活的时间。
    新建NodeInfo对象时，last_active_time默认为当前时间。
    """

    def __init__(self, addr, port, id, desc, last_active_time=None):
        """
        :param basestring addr: node address
        :param int port: node port
        :param basestring id: node id
        :param basestring desc: node desc
        :param float last_active_time: last active timestamp
        """
        self.addr = addr
        self.port = port
        self.id = id
        self.desc = desc
        if last_active_time is None:
            self.last_active_time = time()
        else:
            self.last_active_time = last_active_time


def run_server():
    """
    运行Server。请使用runserver.py调用。

    :rtype: Server
    """
    from serverconfig import parse_from_file
    default_config = parse_from_file("config/server.conf")
    return Server(default_config)