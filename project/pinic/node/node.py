# -*- coding: utf8 -*-

"""
本Python模块含有Node类，即系统中的Node部分。

Node在自身启动后，会向Server的/server/regnode注册。

配置文件更改时，会先向Server的/server/unregnode注销，之后再次注册。
期间Node的ID等等根据新旧配置的不同可能会有变化。
"""

__author__ = "tgmerge"

# 启用gevent环境支持
from gevent import monkey
monkey.patch_all()

# 外部模块
from bottle import Bottle, request
import grequests
from requests.exceptions import RequestException

# 项目内的其他模块
from pinic.util import generate_500
from pinic.sensor.sensordata import SensorData
from pinic.node.nodeconfig import NodeConfig
from pinic.node.nodeconfig import parse_from_string as parse_node_config_from_string

# python内置模块
from importlib import import_module
import threading
import logging


# 设置日志等级
logging.basicConfig(level=logging.DEBUG)


class Node(object):
    """
    本类是项目中的Node服务器。运行指导参见pinic.node.__init__.py的文档
    """

    def __init__(self, node_config):
        """
        :param NodeConfig node_config: 初始化用的Node配置（NodeConfig对象）。
        """

        self.config = None  # 类型：NodeConfig，是本服务器当前的配置

        self.bottle = Bottle()  # 类型：Bottle，是本服务器内含的Bottle Web服务器

        self.sensor_threads = []  # 类型：list of SensorThread，是传感器监视线程的列表。

        self.server_monitor = None  # 类型：ServerMonitor，用于定期向Server发送心跳请求。

        # 应用初始化配置
        self.apply_config(node_config)

        # 进行URL路由，并启动Bottle Web服务器
        self.start_bottle()

    # 行为抽象方法
    # ============

    def filter_sensor_data(self, sensor_data):
        """
        使用Node的配置（Node.config）中的规则（filters）过滤传感器数据。
        如果和过滤规则匹配，则丢弃它。

        :param SensorData sensor_data: 要检查的传感器数据（SensorData对象）

        :rtype bool: 如果为True，说明被丢弃；如果为False，说明未被丢弃
        """

        # 类型检查
        if not isinstance(sensor_data, SensorData):
            raise TypeError("sensor_data: %s is not a SensorData instance" % str(sensor_data))

        # 预设丢弃状态为False（未丢弃）
        is_dropped = False

        # 检查config.filters中的每条过滤规则
        for data_filter in self.config.filters:
            # 检查 "apply_on_sensor_type" 的值是否符合该传感器数据的sensor_type。
            # 如果不符合，则直接保留该数据。"*"将匹配任意的sensor_type。
            if (data_filter["apply_on_sensor_type"] != "*") and (data_filter["apply_on_sensor_type"] != sensor_data.sensor_type):
                continue

            # 检查 "apply_on_sensor_id" 的值是否符合该传感器数据的sensor_id。
            # 如果不符合，则直接保留该数据。"*"将匹配任意的sensor_id。
            if (data_filter["apply_on_sensor_id"] != "*") and (data_filter["apply_on_sensor_id"] != sensor_data.sensor_id):
                continue

            # 检查比较方法 "comparing_method" 和比较阈值 "threshold" 。
            # 比较方法可以是 "greater_than" 或 "less_than"，其他值无效（将保留数据）。
            # 例如：
            # COMPARING_METHOD  THRESHOLD
            # greater_than      100
            # 将丢弃大于100的数据。
            if (data_filter["comparing_method"] == "greater_than") and (sensor_data.raw_value > data_filter["threshold"]):
                is_dropped = True
                break
            if (data_filter["comparing_method"] == "less_than") and (sensor_data.raw_value < data_filter["threshold"]):
                is_dropped = True
                break

        return is_dropped

    def apply_config(self, new_config, load_old_config=False):
        """
        为Node服务器应用新的配置。

        :param NodeConfig new_config: 要应用的新配置（NodeConfig对象）。
        :param bool load_old_config: 是否在失败时重新加载旧的配置，默认为False。
        """
        logging.debug("[Node.apply_config] new_config=" + str(new_config) + "load_old_config=" + str(load_old_config))

        # 类型检查
        if not isinstance(new_config, NodeConfig):
            raise TypeError("%s is not a NodeConfig instance" % str(new_config))

        # 备份旧的配置
        old_config = self.config

        # 向Server解除注册
        if self.server_monitor is not None:
            self.server_monitor.stop()
            self.server_monitor.unreg_to_server()

        # 停止传感器线程
        self.stop_sensor_threads()

        # 将Node的配置设置为新的配置
        self.config = new_config

        # 向Server重新注册
        self.server_monitor = ServerMonitor(self)
        self.server_monitor.reg_to_server()
        self.server_monitor.start()

        # 启动新的传感器线程。如果有异常，并不视为配置应用失败
        self.start_sensor_threads()

        # 如果需要，重启整个服务器
        # TODO 由于需求变化，不实现
        if (old_config is not None) and ((new_config.node_port != old_config.node_port) or (new_config.node_host != old_config.node_host)):
            self.restart_bottle()

    def start_bottle(self):
        """
        进行URL路由，并开启Bottle Web服务器。
        """

        logging.debug("[Node.start_bottle] starting bottle, node_id=%s" % self.config.node_id)

        # URL路由
        self.bottle.route("/node/nodeconfig/<node_id>", method="POST", callback=self.post_node_config)
        self.bottle.route("/node/nodeconfig/<node_id>", method="GET", callback=self.get_node_config)
        self.bottle.route("/node/sensordata/<node_id>/<sensor_id>", method="GET", callback=self.get_sensor_data)
        self.bottle.route("/node/warningdata/<node_id>/<sensor_id>", method="GET", callback=self.get_warning_data)

        # 开启Bottle
        self.bottle.run(
            host=self.config.node_host,
            port=self.config.node_port,
            server="gevent"
        )

    def restart_bottle(self):
        logging.debug("[Node.restart_bottle] restarting bottle")
        pass

    def start_sensor_threads(self):
        """
        开启Node的配置（Node.config）中所描述的所有传感器的监视线程。
        """
        for index, sensor in enumerate(self.config.sensors):
            thread = SensorThread(self, index)
            self.sensor_threads.append(thread)
            thread.start()

    def stop_sensor_threads(self):
        """
        结束Node已经开启的所有传感器线程。
        """
        for thread in self.sensor_threads:
            thread.stop()

    # HTTP处理方法
    # ============

    def post_node_config(self, node_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法将处理Server发来的请求（HTTP POST），要求更新Node的当前配置。
        方法将试图解析POST正文中的新配置，并试图给Node自身应用这个配置。
        如果中途出现错误，将返回HTTP 500错误，并在响应正文中附上错误的信息和产生的异常。
        如果没有出现错误，将返回HTTP 200正常响应，并在响应正文中附上更新后的配置，以供检查。

        :param basestring node_id: URL中的<node_id>部分。
        """

        # 检查URL中的node_id是否和自身ID匹配
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 尝试解析POST正文中的NodeConfig
        try:
            new_config = parse_node_config_from_string(request.body.read())
        except ValueError as e:
            return generate_500("Error on parsing new config.", e)

        # 尝试应用新的配置
        try:
            self.apply_config(new_config)
        except Exception as e:
            return generate_500("CAUTION: Error on applying new config.", e)

        # 返回更新后的配置
        return self.config.get_json_string()

    def get_node_config(self, node_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理Server发来的请求，要求返回Node的当前配置。
        方法将在HTTP GET的响应（HTTP 200）中返回Json格式的、本Node的配置。

        :param basestring node_id: URL中的<node_id>部分。
        """
        # 检查URL中的node_id是否和自身ID匹配
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 返回当前的配置Json
        return self.config.get_json_string()

    def get_sensor_data(self, node_id, sensor_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理Server发来的请求，要求返回传感器的当前传感值。
        方法将以Json形式返回传感器数据。
        如果请求错误或出现异常，返回HTTP 500。

        :param basestring node_id: URL中的<node_id>部分。
        :param basestring sensor_id: URL中的<sensor_id>部分。
        """
        # 检查URL中的node_id是否和自身ID匹配
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 在Node自身的sensor_threads中查找sensor_id相符的SensorThread对象
        for x in self.sensor_threads:
            if sensor_id == x.sensor_id:
                sensor_thread = x
                break
        else:
            return generate_500("Cannot find sensor with sensor_id='%s'" % sensor_id)

        # 从该SensorThread对象获取传感器数据并返回
        return sensor_thread.get_json_dumps_sensor_data()

    def get_warning_data(self, node_id, sensor_id):
        """
        处理HTTP URL，参见start_bottle方法的注释。

        本方法处理Server发来的请求，要求返回某个传感器被过滤列表（filters）过滤后仍保留的警报数据。
        如果当前那个传感器的传感器值（SensorData）不符合任何filter的条件，则返回它。
        否则，如果那个传感器的值被filters中的filter过滤，则返回空的HTTP 200。
        如果请求错误或出现异常，返回HTTP 500。
        """

        # 检查URL中的node_id是否和自身ID匹配
        if node_id != self.config.node_id:
            return generate_500("Cannot find node with node_id='%s'" % node_id)

        # 在Node自身的sensor_thread中查找sensor_id相符的SensorThread对象
        for x in self.sensor_threads:
            if sensor_id == x.sensor_id:
                sensor_thread = x
                break
        else:
            return generate_500("Cannot find sensor with sensor_id='%s'" % node_id)

        # 从该SensorThread对象读传感器数据（SensorData），并过滤
        sensor_data = sensor_thread.get_data()
        if not self.filter_sensor_data(sensor_data):
            return sensor_data.get_json_dumps()
        else:
            return  # 空的HTTP 200


class ServerMonitor(threading.Thread):
    """
    Server监视线程。已经被gevent monkey_patch成为greenlet。
    该线程定期向Server发送/server/keepnode/<node_id>这个心跳请求，以表明当前的Node存活。
    """

    def __init__(self, node):
        """
        构造方法。

        :param Node node: 开启此线程的Node
        """
        super(ServerMonitor, self).__init__()

        self.node = node  # 开启此线程的Node
        self.server_addr = node.config.server_addr  # Node的当前配置
        self.server_port = node.config.server_port
        self.node_id = node.config.node_id
        self.keep_alive_interval = 10.0  # 秒，每隔这个间隔向Server发送心跳请求
        self.stop_event = threading.Event()  # 停止事件，建议使用ServerMonitor.stop()停止本线程

    def reg_to_server(self):
        """
        向Server注册自身（Node）。
        发送一个POST请求到server的/server/regnode，请求内容是Node的config。
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
        向Server解除注册自身（Node）。
        发送一个POST请求到server的/server/unregnode，请求内容是Node的config。
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
        向Server的/server/keepnode/<node_id>发送一个GET，证明自身存活。
        如果返回200，说明正常。
        如果返回500，说明Server尚不知道自身，故进行reg_to_server，重新向Server注册自己。
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
        ServerMonitor以如下方式运行：

        每keep_alive_interval秒，运行send_keep_node，发送自身存活消息。
        """

        while not self.stop_event.wait(self.keep_alive_interval):
            self.send_keep_node()

    def stop(self):
        """
        停止本ServerMonitor线程的运行。
        """

        self.stop_event.set()


class SensorThread(threading.Thread):
    """
    传感器监视线程。已经被gevent monkey_patch为greenlet。
    可以通过该线程的方法获取传感器的值。

    在最初的设计中，有定期检查传感器并推送报警信息给Server的功能。
    但后来在2015年4月29日，因导师要求被移除，改为Server定期检查。

    这次编辑参见Git commit记录： 699b6bc7aefe64eab56f5d9727ec341e001d0e4a
    """

    def __init__(self, node, index):
        """
        构造方法。

        :param Node node: 开启此线程的Node。
        :param int index: 传感器配置在Node.config中的索引。用于查找传感器的配置。
        """
        super(SensorThread, self).__init__()

        # 得到传感器的配置
        sensor_config = node.config.sensors[index]
        self.sensor_type = sensor_config["sensor_type"]
        self.sensor_id = sensor_config["sensor_id"]
        self.sensor_desc = sensor_config["sensor_desc"]
        self.sensor_config = sensor_config["sensor_config"]
        self.server_addr = node.config.server_addr
        self.server_port = node.config.server_port
        self.sensor_interval = 10.0  # 已经无需定期检查传感器，但保留供停止传感器用

        # 根据传感器的类型（sensor_type）导入传感器驱动的Python模块。
        # 路径为project/pinic/sensor/sensor_[sensor_type].py。
        # 例如，sensor_type="stub"，则模块为
        # project/pinic/sensor/sensor_stub.py
        sensor_module = import_module("pinic.sensor.sensor_" + self.sensor_type)  # 导入模块
        self.sensor = sensor_module.Sensor(self.sensor_id, self.sensor_desc, sensor_config)  # self.sensor类型：BaseSensor的子类的实例

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
        读取传感器数据(SensorData)并返回其Json形式的字符串。

        :rtype: str
        """
        return self.sensor.get_json_dumps_data()

    def run(self):
        """
        线程的入口方法。
        已经移除了线程自己定期检查传感器值并发送给Server的逻辑。
        """

        # 初始化传感器
        self.sensor.initialize()

        while not self.stop_event.wait(self.sensor_interval):
            try:
                pass  # 移除部分
            except Exception as e:
                logging.exception("[SensorThread.run] exception:" + str(e))

    def stop(self):
        """
        停止线程。同时将关闭传感器。
        """

        self.sensor.close()
        self.stop_event.set()
