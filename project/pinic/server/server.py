# -*- coding: utf8 -*-

"""
本Python模块含有Server类，即系统中的Server部分。

Server在启动时并不知道任何关于Node的信息。每一个Node启动后，
会自己向Server的/server/regnode注册。

为验证Server当前所知的Node是否存活，Server会间隔一定时间，
使用NodeMonitorThread向Node的/heartbeat/<node_id>验证。
连续失败一定次数之后，Server即认为这个Node处于异常状态，
并放慢验证间隔（<--TODO 待定）。

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

        self.node_threads = []
        """ :type: list of NodeThread """

        self.apply_config(server_config)  # 1. 应用配置，向forwarder注册
        self.start_local_server()         # 2. 启动bottle

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

        # 1. 类型检查
        if not isinstance(new_config, ServerConfig):
            raise TypeError("%s is not a ServerConfig instance" % str(new_config))

        # 2. 备份旧的配置
        old_config = self.config

        # 3. 向Forwarder解除注册(如果有Forwarder)
        if self.config is not None:
            self.unreg_to_forwarder()

        # 4. 更换config
        self.config = new_config

        # 5. 向Server重新注册
        self.reg_to_forwarder()

        # 6. 如果新配置的node_host或node_port与旧配置不同，
        # TODO 执行shel脚本以重启整个应用
        if (old_config is not None) and ((new_config.server_port != old_config.server_port) or (new_config.server_host != old_config.server_host)):
            self.restart_bottle()

    def start_local_server(self):
        """
        启动Node的Bottle服务器。
        """
        # URL路由
        self.bottle.route("/server/regnode", method="POST", callback=self.post_reg_node)
        self.bottle.route("/server/unregnode", method="POST", callback=self.post_unreg_node)

        self.bottle.route("/server/serverconfig/<server_id>", method="GET", callback=self.get_server_config)
        self.bottle.route("/server/serverconfig/<server_id>", method="POST", callback=self.post_server_config)

        self.bottle.route("/server/nodeconfig/<server_id>/<node_id>", method="GET", callback=self.get_node_config)
        self.bottle.route("/server/nodeconfig/<server_id>/<node_id>", method="POST", callback=self.post_node_config)

        self.bottle.route("/server/sensordata/<server_id>/<node_id>/<sensor_id>", method="GET", callback=self.get_sensor_data)

        self.bottle.route("/server/sensordata", method="POST", callback=self.post_sensor_data)
        self.bottle.route("/server/heartbeat/<server_id>", method="GET", callback=self.get_heartbeat)

        self.bottle.run(
            host=self.config.server_host,
            port=self.config.server_port,
            server="gevent"
        )  # TODO 使用Node时加锁

    def reg_to_forwarder(self):
        """
        向Forwarder注册自己。发送一个POST请求到forwarder的``/forwarder/regserver``，请求内容是自身的config。

        """
        request_url = str("http://%s:%d/forwarder/regserver" % (self.config.forwarder_addr, self.config.forwarder_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.POSTFIELDS, self.config.get_json_string())
        curl.perform()
        curl.close()
        # todo 处理异常

    def unreg_to_forwarder(self):
        """
        向Forwarder解除注册自己。发送一个POST到Forwarder的``/forwarder/unregserver``，请求内容是自身的config。
        """
        request_url = str("http://%s:%d/forwarder/unregnode" % (self.config.forwarder_addr, self.config.forwarder_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.POSTFIELDS, self.config.get_json_string())
        curl.perform()
        curl.close()
        # todo 处理异常

    # HTTP处理方法
    # ============

    def get_heartbeat(self, server_id):
        """
        处理GET /node/heartbeat/<server_id>。
        返回一个空的HTTP 200，用以确认Server存活。
        如果请求错误或出现异常，返回HTTP 500。

        :param basestring server_id: URL中的<server_id>部分。
        """
        # 1. 检查server_id：
        if server_id != self.config.server_id:
            return generate_500("Cannot find node with node_id")

        # 2. 返回HTTP 200
        return

    def post_sensor_data(self):
        """
        处理POST /server/sensordata。
        如果成功，返回HTTP 200，数据将原样递交给Forwarder。
        如果失败，返回HTTP 500(todo)。
        """
        request_url = str("http://%s:%d/forwarder/sensordata" % (self.config.forwarder_addr, self.config.forwarder_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.POSTFIELDS, request.body.read())
        curl.perform()  # TODO 处理异常
        return  # HTTP 200

    def get_server_config(self, server_id):
        """
        处理GET /server/serverconfig/<server_id>。
        以Json形式返回Server的当前配置。
        如果请求错误或出现异常，返回HTTP 500。

        :param basestring server_id: URL中的<server_id>部分。
        """
        # 1. 检查server_id:
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        # 2. 返回server_config:
        return self.config.get_json_string()

    def post_server_config(self, server_id):
        """
        处理POST /server/serverconfig/<server_id>。
        以Json形式返回新的Server配置。
        如果请求错误或出现异常，返回HTTP 500。

        :param basestring server_id: URL中的<server_id>部分。
        """
        # 1. 检查server_id:
        if server_id != self.config.server_id:
            return generate_500("Cannot find node with server_id='%s'" % server_id)

        # 2. 解析新的server_config:
        try:
            new_config = parse_server_config_from_string(request.body.read())
        except ValueError as e:
            return generate_500("Error on parsing new config.", e)

        # 3. 应用新的server_config：
        try:
            self.apply_config(new_config)
        except Exception as e:
            return generate_500("CAUTION: Error on applying new config.", e)

        # 4. 成功
        return self.config.get_json_string()

    def post_reg_node(self):
        """
        处理POST /server/regnode。
        如果成功，返回HTTP 200。
        """
        # 1. 解析POST内容为node_config
        body = request.body.read()
        try:
            node_config = parse_node_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing node config.", e)

        # 2. 获取请求的IP地址、端口、node信息
        node_addr = request.environ.get("REMOTE_ADDR")
        node_port = node_config.node_port
        node_id = node_config.node_id
        node_desc = node_config.node_desc

        # 3. 开启线程
        thread = NodeThread(self, node_addr, node_port, node_id, node_desc)
        self.node_threads.append(thread)
        thread.start()

        # 4. 返回200
        return

    def post_unreg_node(self):
        """
        处理POST /server/unregnode，
        如果成功，返回HTTP 200。
        """
        # 1. 解析POST内容为node_config
        body = request.body.read()
        try:
            node_config = parse_node_config_from_string(body)
        except ValueError as e:
            return generate_500("Error on parsing node config.", e)

        # 2. 获取请求的IP地址、端口、node信息
        # node_addr = request.environ.get("REMOTE_ADDR")
        # node_port = node_config.node_port
        node_id = node_config.node_id
        # node_desc = node_config.node_desc

        # 停止node_id相符的线程
        for thread in self.node_threads:
            if thread.node_id == node_id:
                thread.stop()
            break
        else:
            return generate_500("Cannot find node thread with node_id='%s'" % node_id)

    def get_node_config(self, server_id, node_id):
        """
        处理GET /server/nodeconfig/<server_id>/<node_id>
        如果成功，返回HTTP 200，内容为node的当前配置。
        """

        # 1. 检查server_id
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        # 2. 查找node_id
        for x in self.node_threads:
            if node_id == x.node_id:
                node_thread = x
                break
        else:
            return generate_500("Cannot find node with node_id='%s' from this server" & node_id)

        # 3. 发送GET /node/nodeconfig/<node_id>
        curl_buffer = StringIO()
        request_url = str("http://%s:%d/node/nodeconfig/%s" % (node_thread.node_addr, node_thread.node_port, node_thread.node_id))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.WRITEDATA, curl_buffer)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        try:
            curl.perform()
        except pycurl.error as e:
            return generate_500("Error on curling config from node.", e)
        finally:
            curl.close()

        # 4. 原样返回上面的发送结果
        return curl_buffer.getvalue()

    def post_node_config(self, server_id, node_id):
        """
        处理POST /server/nodeconfig/<server_id>/<node_id>
        如果成功，返回HTTP 200，内容为node的新配置。
        """

        # 1. 检查server_id
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        # 2. 查找node_id
        for x in self.node_threads:
            if node_id == x.node_id:
                node_thread = x
                break
        else:
            return generate_500("Cannot find node with node_id='%s' from this server" & node_id)

        # 3. 发送POST /node/nodeconfig/<node_id>
        curl_buffer = StringIO()
        request_url = str("http://%s:%d/node/nodeconfig/%s" % (node_thread.node_addr, node_thread.node_port, node_thread.node_id))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.POSTFIELDS, request.body.read())
        curl.setopt(pycurl.WRITEDATA, curl_buffer)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        try:
            curl.perform()
        except pycurl.error as e:
            return generate_500("Error on sending config to node.", e)
        finally:
            curl.close()

        # 4. 原样返回上面的发送结果
        return curl_buffer.getvalue()

    def get_sensor_data(self, server_id, node_id, sensor_id):
        """
        处理GET /server/sensordata/<server_id>/<node_id>/<sensor_id>
        如果成功，返回传感器数据（Json格式的SensorData）。
        """
        # 1. 检查server_id
        if server_id != self.config.server_id:
            return generate_500("Cannot find server with server_id='%s'" % server_id)

        # 2. 查找node_id
        for x in self.node_threads:
            if node_id == x.node_id:
                node_thread = x
                break
        else:
            return generate_500("Cannot find node with node_id='%s' from this server" & node_id)

        # 3. 发送GET /node/sensordata/<sensor_id>
        curl_buffer = StringIO()
        request_url = str("http://%s:%d/node/sensordata/%s" % (node_thread.node_addr, node_thread.node_port, sensor_id))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.WRITEDATA, curl_buffer)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        try:
            curl.perform()
        except pycurl.error as e:
            return generate_500("Error on sending config to node.", e)
        finally:
            curl.close()

        # 4. 原样返回收到的数据
        return curl_buffer.getvalue()


class NodeThread(threading.Thread):
    """
    Node监视线程。以固定时间间隔向已知Node发送GET /node/heartbeat请求。
    如果连续超时或失败一定次数，则将Node置于“不连通”状态，并减慢继续发送请求的速度。
    """

    def __init__(self, server, node_addr, node_port, node_id, node_desc):
        """
        初始化监视线程。

        :param Server server: 开启此线程的Server
        :param int index: Node在Server.config中的索引
        TODO 加锁
        """
        super(NodeThread, self).__init__()

        # 得到Node配置
        self.node_addr = node_addr
        self.node_port = node_port
        self.node_id = node_id
        self.node_desc = node_desc

        # 设置参数
        self.is_on = True             # 状态是否正常，False为不联通
        self.normal_heartbeat_interval = 10  # 正常heartbeat间隔
        self.slow_heartbeat_interval = 30    # 异常时的heartbeat间隔
        self.timeout_count = 0        # 超时次数
        self.max_timeout_count = 5    # 最大超时次数，超过则置于不连通状态

        # 设置停止事件
        self.stop_event = threading.Event()

    def run(self):
        request_url = str("http://%s:%d/node/heartbeat/%s" % (self.node_addr, self.node_port, self.node_id))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)

        if self.is_on:
            interval = self.heartbeat_interval
        else:
            interval = self.slow_heartbeat_interval

        while not self.stop_event.wait(interval):
            try:
                curl.perform()
                if curl.getinfo(pycurl.HTTP_CODE) != '200':
                    raise TimeoutError()
                self.is_on = True
                self.timeout_count = 0
            except (pycurl.error, TimeoutError) as e:
                logging.debug("[NodeThread.run] heartbeat error: " + str(e))
                self.timeout_count += 1
                if self.timeout_count > self.max_timeout_count:
                    self.is_on = False
                    self.toggle_down()
            finally:
                curl.close()
                if self.is_on:
                    interval = self.heartbeat_interval
                else:
                    interval = self.slow_heartbeat_interval

    def toggle_down(self):
        """
        Node的状态变成“不连通”之后，要执行的任务。
        """
        # TODO 清除这个线程，之类
        pass

    def stop(self):
        self.stop_event.set()


def run_gateway():
    """
    运行Gateway。请使用rungateway.py调用。

    :rtype: Server
    """
    from serverconfig import parse_from_file
    default_config = parse_from_file("config/gateway.conf")
    return Server(default_config)