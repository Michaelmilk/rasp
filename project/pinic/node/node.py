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
                |
                ---- SensorMonitor # 传感器监视线程，需要时发送数据给Server

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
import pycurl
from pinic.util import generate_500
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

        self.apply_config(node_config)  # 1. 应用配置，向server注册
        self.start_local_server()       # 2. 启动bottle

    # 行为方法
    # ========

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
        if self.config is not None:
            self.unreg_to_server()

        # 4. 停止传感器线程
        self.stop_sensor_threads()

        # 5. 更换config
        self.config = new_config

        # 6. 向Server重新注册
        self.reg_to_server()

        # 7. 启动新的传感器线程。如果有异常，**不视为**配置应用失败
        self.start_sensor_threads()

        # 8. 如果新配置的node_host或node_port与旧配置不同，
        # TODO 执行shell脚本以重启整个应用。bottle无法自行重启……
        if (old_config is not None) and ((new_config.node_port != old_config.node_port) or (new_config.node_host != old_config.node_host)):
            self.restart_bottle()

    def start_local_server(self):
        """
        启动Node的Bottle服务器。
        """
        # URL路由
        self.bottle.route("/node/nodeconfig/<node_id>", method="POST", callback=self.post_node_config)
        self.bottle.route("/node/nodeconfig/<node_id>", method="GET", callback=self.get_node_config)
        self.bottle.route("/node/sensordata/<sensor_id>", method="GET", callback=self.get_sensor_data)
        self.bottle.route("/node/heartbeat/<node_id>", method="GET", callback=self.get_heartbeat)

        self.bottle.run(
            host=self.config.node_host,
            port=self.config.node_port,
            server="gevent"
        )  # TODO 使用Node时加锁？

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

    def reg_to_server(self):
        """
        向Server注册自己。发送一个POST请求到server的``/server/regnode``，请求内容是自身的config。
        """
        request_url = str("http://%s:%d/server/regnode" % (self.config.server_addr, self.config.server_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.POSTFIELDS, self.config.get_json_string())
        curl.perform()
        curl.close()
        # todo 处理异常

    def unreg_to_server(self):
        """
        向Server解除注册自己。发送一个POST请求到server的``/server/unregnode``，请求内容是自身的config。
        """
        request_url = str("http://%s:%d/server/unregnode" % (self.config.server_addr, self.config.server_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)
        curl.setopt(pycurl.POSTFIELDS, self.config.get_json_string())
        curl.perform()
        curl.close()
        # todo 处理异常

    def restart_bottle(self):
        # todo implement
        pass

    # HTTP处理方法
    # ============

    def get_heartbeat(self, node_id):
        """
        处理GET /node/heartbeat/<node_id>。
        返回一个空的HTTP 200，用以确认Node存活。
        如果请求错误或出现异常，返回HTTP 500。

        :param basestring node_id: URL中的<node_id>部分。
        """
        # 1. 检查node_id:
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 2. 返回HTTP 200
        return

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

    def get_sensor_data(self, sensor_id):
        """
        处理GET /node/sensordata/<sensor_id>。
        以Json形式返回传感器数据。
        如果请求错误或出现异常，返回HTTP 500。

        :param sensor_id: URL中的<sensor_id>部分。
        """
        # 1. 查找sensor_id相符的SensorThread对象:
        for x in self.sensor_threads:
            if sensor_id == x.sensor_id:
                sensor_thread = x
                break
        else:
            return generate_500("Cannot find sensor with sensor_id='%s'" % sensor_id)

        # 2. 从该传感器读数据
        return sensor_thread.get_json_dumps_sensor_data()


class SensorThread(threading.Thread):
    """传感器监视线程。以固定时间间隔从传感器读取数据，并发送给Gateway。"""

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
        self.sensor_interval = sensor_config["sensor_interval"]
        self.server_addr = node.config.server_addr
        self.server_port = node.config.server_port

        # 导入传感器驱动module
        sensor_module = import_module("pinic.sensor.sensor_" + self.sensor_type)
        self.sensor = sensor_module.Sensor(self.sensor_id, self.sensor_desc, sensor_config)

        # 设置停止事件
        self.stop_event = threading.Event()

    def get_json_dumps_sensor_data(self):
        """
        读取传感器数据(SensorData)并返回其Json形式。

        :rtype: str
        """
        # TODO 自动时间间隔和手动获取值同时使用时，可能会超过传感器设备的最短时间间隔
        return self.sensor.get_json_dumps_data()

    def run(self):
        request_url = str("http://%s:%d/server/sensordata" % (self.server_addr, self.server_port))
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, request_url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 10)
        curl.setopt(pycurl.TIMEOUT, 30)

        self.sensor.initialize()

        while not self.stop_event.wait(self.sensor_interval):
            try:
                curl.setopt(pycurl.POSTFIELDS, self.sensor.get_json_dumps_data())
                curl.perform()
                curl.close()
            except Exception as e:
                logging.exception("[SensorThread.run] exception:" + str(e))

    def stop(self):
        self.sensor.close()
        self.stop_event.set()
