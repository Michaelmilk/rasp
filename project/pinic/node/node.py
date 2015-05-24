# -*- coding: utf8 -*-

"""
本Python模块含有Node类，即系统中的Node部分。

Node在自身启动后，会向Server的/server/regnode注册。

配置文件更改时，会先向Server的/server/unregnode注销，之后再次注册。
期间Node的ID等等根据新旧配置的不同可能会有变化。

模块线程
========

::

    main ----------- main          # 服务器线程
            |   |
            |   ---- SensorMonitor # 传感器监视线程，需要时发送数据给Server
            -------- ServerMonitor # Server监视线程，定期发送keepnode心跳

方法流程
========

::

    ! Warning: Out of date

    On start:
        1. Load config(from default path)
        Init sensors
        Init monitor threads
        2. Start bottle
        3. Reg to server(curl server/regnode)

    GET /node/sensordata/<sensor_id>
        check sensor_id
        find monitor thread
        return sensordata from that thread

    GET /node/nodeconfig/<node_id>
        check node_id
        return current nodeconfig

    POST /node/nodeconfig/<node_id>
        check node_id
        parse new config
        unreg to server POST server_addr:server_port/server/unregnode
        stop sensors
        stop monitor threads
        apply new config
        init sensors
        init threads
        reg to server POST server_addr:server_port/server/regnode

    GET /node/heartbeat/<node_id>
        check node_id
        return 200

    Sensor thread workflow

    On interval reached:
        Get data
        Check filter
        curl to server_addr:server_port/server/sensordata

"""

__author__ = "tgmerge"


from gevent import monkey
monkey.patch_all()
import logging
import threading
from importlib import import_module
from bottle import Bottle, request
import grequests
from requests.exceptions import RequestException
from pinic.util import generate_500
from pinic.sensor.sensordata import SensorData
from pinic.node.nodeconfig import NodeConfig
from pinic.node.nodeconfig import parse_from_string as parse_node_config_from_string


logging.basicConfig(level=logging.DEBUG)


class Node(object):
    """Node"""

    def __init__(self, node_config):
        """
        :param NodeConfig node_config: 必需，启动配置
        """

        self.config = None              # Node当前的配置
        """ :type: NodeConfig """

        self.bottle = Bottle()          # 服务器bottle
        """ :type: Bottle """

        self.sensor_threads = []
        """ :type: list of SensorThread """

        self.server_monitor = None       # ServerMonitor
        """ :type: ServerMonitor """

        self.apply_config(node_config)  # 1. 应用配置，向server注册
        self.start_bottle()       # 2. 启动bottle

    # 行为方法
    # ========

    def filter_sensor_data(self, sensor_data):
        """
        使用配置中的规则过滤传感器数据。
        如果和过滤规则匹配，则丢弃它。

        :param SensorData sensor_data: 要检查的SensorData对象
        :rtype bool: 如果为True，说明被丢弃；如果为False，说明未被丢弃
        """

        if not isinstance(sensor_data, SensorData):
            raise TypeError("sensor_data: %s is not a SensorData instance" % str(sensor_data))

        is_dropped = False

        for data_filter in self.config.filters:
            # Check "apply_on_sensor_type"
            if (data_filter["apply_on_sensor_type"] != "*") and (data_filter["apply_on_sensor_type"] != sensor_data.sensor_type):
                continue

            # Check "apply_on_sensor_id"
            if (data_filter["apply_on_sensor_id"] != "*") and (data_filter["apply_on_sensor_id"] != sensor_data.sensor_id):
                continue

            # Check method and threshold
            if (data_filter["comparing_method"] == "greater_than") and (sensor_data.raw_value > data_filter["threshold"]):
                is_dropped = True
                break
            if (data_filter["comparing_method"] == "less_than") and (sensor_data.raw_value < data_filter["threshold"]):
                is_dropped = True
                break

        return is_dropped

    def apply_config(self, new_config, load_old_config=False):
        """
        更新这个Node的配置。
        如果开启新的传感器监视线程时发生了异常，将回滚到旧的配置。
        如果这个回滚操作也发生了异常，将什么也不做并抛出它。

        :param NodeConfig new_config: 要载入的新配置
        :param bool load_old_config: 调用时无需设置。在载入失败时防止无限回滚。
        """
        logging.debug("[Node.apply_config] new_config=" + str(new_config) + "load_old_config=" + str(load_old_config))

        # 1. 类型检查
        if not isinstance(new_config, NodeConfig):
            raise TypeError("%s is not a NodeConfig instance" % str(new_config))

        # 2. 备份旧的配置
        old_config = self.config

        # 3. 向Server解除注册(如果有Server)
        if self.server_monitor is not None:
            self.server_monitor.stop()
            self.server_monitor.unreg_to_server()

        # 4. 停止传感器线程
        self.stop_sensor_threads()

        # 5. 更换config
        self.config = new_config

        # 6. 向Server重新注册
        self.server_monitor = ServerMonitor(self)
        self.server_monitor.reg_to_server()
        self.server_monitor.start()

        # 7. 启动新的传感器线程。如果有异常，**不视为**配置应用失败
        self.start_sensor_threads()

        # 8. 如果新配置的node_host或node_port与旧配置不同，
        # TODO 执行shell脚本以重启整个应用。bottle无法自行重启……
        if (old_config is not None) and ((new_config.node_port != old_config.node_port) or (new_config.node_host != old_config.node_host)):
            self.restart_bottle()

    def start_bottle(self):
        """
        启动Node的Bottle服务器。
        """
        # URL路由
        logging.debug("[Node.start_bottle] starting bottle, node_id=%s" % self.config.node_id)

        self.bottle.route("/node/nodeconfig/<node_id>", method="POST", callback=self.post_node_config)
        self.bottle.route("/node/nodeconfig/<node_id>", method="GET", callback=self.get_node_config)
        self.bottle.route("/node/sensordata/<node_id>/<sensor_id>", method="GET", callback=self.get_sensor_data)
        self.bottle.route("/node/warningdata/<node_id>/<sensor_id>", method="GET", callback=self.get_warning_data)

        self.bottle.run(
            host=self.config.node_host,
            port=self.config.node_port,
            server="gevent"
        )  # TODO 使用Node时加锁？

    def restart_bottle(self):
        # todo implement
        logging.debug("[Node.restart_bottle] restarting bottle")
        pass

    def start_sensor_threads(self):
        """
        根据Node的配置，开启所有传感器线程。
        """
        for index, sensor in enumerate(self.config.sensors):
            thread = SensorThread(self, index)
            self.sensor_threads.append(thread)
            thread.start()

    def stop_sensor_threads(self):
        """
        结束已经开启的传感器线程。
        """
        for thread in self.sensor_threads:
            thread.stop()

    # HTTP处理方法
    # ============

    def post_node_config(self, node_id):
        """
        处理POST /node/nodeconfig/<node_id>。
        以Json形式返回新的Node配置。
        如果请求错误或出现异常，返回HTTP 500。

        :param basestring node_id: URL中的<node_id>部分。
        """
        # 1. 检查node_id:
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 2. 解析新的node_config：
        try:
            new_config = parse_node_config_from_string(request.body.read())
        except ValueError as e:
            return generate_500("Error on parsing new config.", e)

        # 3. 应用新的node_config:
        try:
            self.apply_config(new_config)
        except Exception as e:
            return generate_500("CAUTION: Error on applying new config.", e)

        # 4. 成功
        return self.config.get_json_string()

    def get_node_config(self, node_id):
        """
        处理GET /node/nodeconfig/<node_id>。
        以Json形式返回Node的当前配置。
        如果请求错误或出现异常，返回HTTP 500。

        :param basestring node_id: URL中的<node_id>部分。
        """
        # 1. 检查node_id:
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 2. 返回node_config:
        return self.config.get_json_string()

    def get_sensor_data(self, node_id, sensor_id):
        """
        处理GET /node/sensordata/<node_id>/<sensor_id>。
        以Json形式返回传感器数据。
        如果请求错误或出现异常，返回HTTP 500。

        :param sensor_id: URL中的<sensor_id>部分。
        """
        # 1. 检查node_id:
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 2. 查找sensor_id相符的SensorThread对象:
        for x in self.sensor_threads:
            if sensor_id == x.sensor_id:
                sensor_thread = x
                break
        else:
            return generate_500("Cannot find sensor with sensor_id='%s'" % sensor_id)

        # 3. 从该传感器读数据
        return sensor_thread.get_json_dumps_sensor_data()

    def get_warning_data(self, node_id, sensor_id):
        """
        处理GET /node/warningdata/<node_id>/<sensor_id>。
        如果传感器值超过阈值，则返回它；否则返回空200。
        如果请求错误或出现异常，返回HTTP 500。
        """

        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        for x in self.sensor_threads:
            if sensor_id == x.sensor_id:
                sensor_thread = x
                break
        else:
            return generate_500("Cannot find sensor with sensor_id='%s'" % node_id)

        sensor_data = sensor_thread.get_data()
        if not self.filter_sensor_data(sensor_data):
            return sensor_data.get_json_dumps()
        else:
            return  # 空的HTTP 200


class ServerMonitor(threading.Thread):
    """Server监视线程，定期向Server发送/server/keepnode/<node_id>以表明自己存活"""

    def __init__(self, node):
        """
        初始化。

        :param Node node: 开启此线程的Node
        TODO 加锁
        """
        super(ServerMonitor, self).__init__()
        # 参数
        self.node = node
        self.server_addr = node.config.server_addr
        self.server_port = node.config.server_port
        self.node_id = node.config.node_id
        self.keep_alive_interval = 10.0  # 秒
        self.stop_event = threading.Event()  # 设置停止事件

    def reg_to_server(self):
        """
        向Server注册Node。发送一个POST请求到server的``/server/regnode``，请求内容是Node的config。
        """
        logging.debug("[ServerMonitor.reg_to_server] reg to server. addr=%s, port=%d" % (self.server_addr, self.server_port))
        request_url = str("http://%s:%d/server/regnode" % (self.server_addr, self.server_port))
        try:
            greq = grequests.post(request_url, data=self.node.config.get_json_string())
            greq.send()
        except RequestException as e:
            logging.warning("[ServerMonitor.reg_to_server] reg failed. err:" + str(e))

    def unreg_to_server(self):
        """
        向Server解除注册Node。发送一个POST请求到server的``/server/unregnode``，请求内容是Node的config。
        """
        logging.debug("[ServerMonitor.unreg_to_server] unreg to server. addr=%s, port=%d" % (self.server_addr, self.server_port))
        request_url = str("http://%s:%d/server/unregnode" % (self.server_addr, self.server_port))
        try:
            greq = grequests.post(request_url, data=self.node.config.get_json_string())
            greq.send()
        except RequestException as e:
            logging.warning("[ServerMonitor.reg_to_server] reg failed. err:" + str(e))

    def send_keep_node(self):
        """
        向Server的/server/keepnode/<node_id>发送一个GET，证明自身存活
        如果返回200，说明正常
        如果返回500，说明Server尚不知道自身，故进行reg_to_server向Server注册自己。
        """
        logging.debug("[ServerMonitor.send_keep_node] sending keep_node message")
        request_url = str("http://%s:%d/server/keepnode/%s" % (self.server_addr, self.server_port, self.node_id))
        try:
            greq = grequests.get(request_url)
            response = greq.send()
            if response.status_code == 500:
                self.unreg_to_server()
                self.reg_to_server()
        except Exception as e:
            logging.exception("[ServerMonitor.send_keep_node] exception:" + str(e))

    def run(self):
        """
        ServerMonitor以如下方式运行。

        每self.keep_alive_interval秒，运行send_keep_node，发送自身存活消息。
        """
        # todo 加锁

        while not self.stop_event.wait(self.keep_alive_interval):
            self.send_keep_node()

    def stop(self):
        self.stop_event.set()


class SensorThread(threading.Thread):
    """传感器监视线程。"""

    def __init__(self, node, index):
        """
        初始化传感器监视线程。

        :param Node node: 开启此线程的Node
        :param int index: 传感器配置在Node.config中的索引
        TODO 加锁
        """
        super(SensorThread, self).__init__()

        # 得到配置
        sensor_config = node.config.sensors[index]
        self.sensor_type = sensor_config["sensor_type"]
        self.sensor_id = sensor_config["sensor_id"]
        self.sensor_desc = sensor_config["sensor_desc"]
        self.sensor_config = sensor_config["sensor_config"]
        self.server_addr = node.config.server_addr
        self.server_port = node.config.server_port

        # 导入传感器驱动module
        sensor_module = import_module("pinic.sensor.sensor_" + self.sensor_type)
        self.sensor = sensor_module.Sensor(self.sensor_id, self.sensor_desc, sensor_config)
        """ :type: pinic.sensor.basesensor.BaseSensor """

        # 设置停止事件
        self.stop_event = threading.Event()

    def get_data(self):
        """
        读取传感器数据(SensorData)并返回SensorData对象。

        :rtype: SensorData
        """
        return self.sensor.get_data()

    def get_json_dumps_sensor_data(self):
        """
        读取传感器数据(SensorData)并返回其Json形式。

        :rtype: str
        """
        # TODO 自动时间间隔和手动获取值同时使用时，可能会超过传感器设备的最短时间间隔
        return self.sensor.get_json_dumps_data()

    def run(self):
        request_url = str("http://%s:%d/server/sensordata" % (self.server_addr, self.server_port))

        self.sensor.initialize()

    def stop(self):
        self.sensor.close()
        self.stop_event.set()

