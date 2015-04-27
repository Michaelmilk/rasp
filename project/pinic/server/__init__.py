# -*- coding: utf-8 -*-

"""
这个Python包中，含有系统的Server部分。

Server在启动时并不知道任何关于Node的信息。每一个Node启动后，
会自己向Server的/server/regnode注册。

为验证Server当前所知的Node是否存活，Server会间隔一定时间，
使用NodeMonitorThread向Node的/heartbeat/<node_id>验证。
连续失败一定次数之后，Server即认为这个Node处于异常状态，
并放慢验证间隔（<--TODO 待定）。

HTTP API说明
============

Server具有以下HTTP API，供Node和Forwarder调用：

**POST /server/regnode**

    供Node调用。向Server注册一个Node。

**POST /server/unregnode**

    供Node调用。向Server注销一个Node。

**GET /server/serverconfig/<server_id>**

    供Forwarder调用。获取Server的当前配置。

**POST /server/serverconfig/<server_id>**

    供Forwarder调用。更新Server的配置。

**GET /server/nodeconfig/<server_id>/<node_id>**

    供Forwarder调用。获取Server连接到的一个Node的当前配置。

**POST /server/nodeconfig/<server_id>/<node_id>**

    供Forwarder调用。更新Server连接到的一个Node的当前配置。

**GET /server/sensordata/<server_id>/<node_id>/<sensor_id>**

    供Forwarder调用。获取一个传感器的传感数值。

**POST /server/sensordata**

    供Node调用。发送一个传感数值，去向未定。TODO

**GET /server/heartbeat/<server_id>**

    供Forwarder调用。确认Server存活。

如果要……
==========

* 要运行Server，先配置config/server.conf，再运行runserver.py。

* 要更改Server的配置，可以参考serverconfig.py的文档。

"""

__author__ = 'tgmerge'
