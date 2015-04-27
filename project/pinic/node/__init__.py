# -*- coding: utf-8 -*-

"""
这个Python包中，含有系统的Node部分。

Node在自身启动后，会向Server的/server/regnode注册。

配置文件更改时，会先向Server的/server/unregnode注销，之后再次注册。
期间Node的ID等等根据新旧配置的不同可能会有变化。

HTTP API说明
============

Node具有以下HTTP API，全部供Server调用：

**POST /node/nodeconfig/<node_id>**

    配置一个Node，新的配置放在Payload中。
    成功则返回新的配置的Json形式。
    如果请求错误或出现异常，返回HTTP 500并在Payload中以Json形式给出异常细节。

    请求处理过程如下：

    1. 检查URL中的node_id是否和自身的node_id相符；
    #. 解析Payload中的Node配置；
    #. 应用新的Node配置；
    #. 返回HTTP 200，内容为新的Node配置。

**GET /node/nodeconfig/<node_id>**

    获取一个Node的当前配置。
    成功则返回当前配置的Json形式。
    如果请求错误或出现异常，返回HTTP 500并在Payload中以Json形式给出异常细节。

    请求处理过程如下：

    1. 检查URL中的node_id是否和自身的node_id相符；
    #. 返回HTTP 200，内容为当前Node配置。

**GET /node/sensordata/<sensor_id>**

    获取一个传感器的当前读值。
    成功则以Json形式返回一份SensorData。
    如果请求错误或出现异常，返回HTTP 500并在Payload中以Json形式给出异常细节。

    请求处理过程如下：

    1. 在Node已知的传感器中查找sensor_id相符的SensorThread对象；
    #. 从该传感器读取数据作为HTTP 200的内容返回。

**GET /node/heartbeat/<node_id>**

    用于让Server确认Node存活。
    成功则返回一个空的HTTP 200。
    如果请求错误或出现异常，返回HTTP 500并在Payload中以Json形式给出异常细节。

    请求处理过程如下：

    1. 检查URL中的node_id是否和自身的node_id相符；
    #. 返回HTTP 200，内容为空。

类说明
======

**node模块**

    详情参看node.py的文档。

    * node.Node是系统中的一个Node。

    * node.SensorThread是用于监视一个传感器的线程。

**nodeconfig模块**

    详情参看nodeconfig.py的文档。

    * nodeconfig.NodeConfig是一份Node的配置。

如果要……
==========

* 要运行Node，请先配置config/node.conf，再运行runnode.py。

* 要添加一个已有驱动的传感器，请参考nodeconfig.py的文档，修改node.conf的配置。

* 要编写一个新的传感器驱动，请参考sensor包的文档。

"""

__author__ = 'tgmerge'
