# 文档: Hub模块

[TOC]

## 模块功能

### 配置相关

* 从文件读取配置
* 通过网络从Gateway接收配置
* 解析、应用配置

### 传感器相关

* 根据配置加载、初始化任意数量的传感器
* 定时采样
* 发送样本到Gateway

### 关于“配置”

“配置”包括Hub的服务主机(host)、端口；Gateway的地址、端口；各个传感器的类型、ID、描述和采样间隔。

## 依赖

* python 2.7+ x86
* `pycurl`，用于发送HTTP请求
* `gevent` 1.0.1, 作为HTTP服务器
* `bottle` 0.12.8, 作为Web框架

## 安装

在Raspberry Pi上的环境配置：

1. `sudo apt-get update`
1. `sudo apt-get install python-pycurl`
2. `sudo apt-get install python-pip`
3. `sudo apt-get install python-dev libevent-dev python-setuptools`
4. `sudo pip install gevent`，需要很长时间
5. `sudo pip install bottle`
6. `sudo pip install gevent-socketio`
7. `sudo pip install grequests`
8. `sudo pip install spidev`

在Windows上的环境配置：

1. 按[Install pycurl on windows]的说明安装pycUrl。需要从[pycurl.sourceforge.net]下载`pycurl-7.19.5.win32-py2.7.msi`文件。
2. 安装[Microsoft Visual C++ Compiler for Python 2.7]，gevent的安装需要这个。
3. `pip install gevent`
4. `pip install bottle`
6. `sudo pip install gevent-socketio`
7. `sudo pip install grequests`
8. `sudo pip install spidev`

## 运行

将工程目录`project/hub`作为当前目录。

1. 配置`hub.conf`配置文件，可以参照`hub.conf.md`的说明
2. 运行`python hub.py`

## 增加传感器

要增加传感器，按如下规范编写一个传感器驱动模块，放置在`hub`目录中，并在配置文件`hub.conf`中添加，或通过网络更新Hub的配置即可。

传感器驱动模块文件需要遵循`sensor_[type].py`的命名方式，放置在`hub`目录中。其中`[type]`是传感器配置中的`type`值。

驱动模块必须含有`Sensor`类，并提供以下方法和返回值：

```
class Sensor(basesensor.BaseSensor):
    # Method signiture                         # Return type
    def __init__(self, sensor_id, sensor_desc) # -> None
    def initialize(self, config=None)          # -> None
    def get_data(self)                         # -> sensordata.SensorData
    def get_json_dumps_data(self)              # -> str
    def close(self)                            # -> None
```

可以参照一个测试用传感器（仅返回虚假数据）`sensor_stab.py`的代码。

## HTTP API

Hub可被调用的Web API：

* `POST /hub/config`，接收同`hub.conf`内容的json字符串，用于更新Hub的配置，包括Hub的服务主机和端口、Hub连接到的Gateway的IP和端口、Hub连接的传感器信息和更新频率。
* `POST /hub/log`，仅测试使用，将接收到的数据显示在终端

Hub可能调用的Gateway的Web API：

* `POST /gateway/sensordata`，以Json文本发送传感器读到的值。包括一些额外信息。
* `POST /gateway/log`，仅测试使用。

## TODO

* 传感器还需要端口信息，即“初始化信息”。为HubConfig.sensors增加一个key`config`。
* 增加一个Web API`GET /hub/config`，用于获取hub的配置。


[Install pycurl on windows]: http://pycurl.sourceforge.net/doc/install.html#windows

[pycurl.sourceforge.net]: http://pycurl.sourceforge.net/download/

[Microsoft Visual C++ Compiler for Python 2.7]: http://www.microsoft.com/en-us/download/details.aspx?id=44266