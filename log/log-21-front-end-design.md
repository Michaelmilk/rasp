# 关于前端

在server上，可以用的接口有以下这些。

获取server的配置。
``GET /server/serverconfig/<server_id>``

更新server的配置。
``POST /server/serverconfig/<server_id>``

获取server已知的所有node。
``GET /server/knownnodes/<server_id>``

获取一个node的配置，包括传感器列表。
``GET /server/nodeconfig/<server_id>/<node_id>``

更新一个node的配置。
``POST /server/nodeconfig/<server_id>/<node_id>``

从一个node获取传感器值。
``GET /server/sensordata/<server_id>/<node_id>/<sensor_id>``

现在要做个界面出来。

- - -

界面功能需要下面这些。

* 显示server本身的信息。
* 显示和server连接的node。
* 实时监控一个node，并绘图。

关于界面。

访问http://server_addr:server_port/

```
 --------------------------------------------
 | Server: server_id                        |
 |                                          |
 | Nodes:     <- auto refresh               |
 | - node_id  <- Click: node monitor        |
 | - node_id                                |
 |                                          |
 --------------------------------------------
```

- - -

文档：

* 架构文档
    - Node部分文档
    - Server部分文档
    - Forwarder部分文档
    - 网页功能设计
* 网卡MAC地址读取，C&python --> uuid
* 页面

+ 批量取多个传感器的值

+ 