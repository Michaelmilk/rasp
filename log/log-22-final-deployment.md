# 部署和运行文档

[TOC]

以下解释从一张空白的SD卡开始，配置树莓派、安装我的项目（项目目录名pinic）的依赖、配置项目并运行它的步骤。

## 配置树莓派

### 1. 写入镜像

1.  下载镜像到本地的。如 `2015-02-16-raspbian-wheezy.zip`
2.  解压缩这个压缩包，得到镜像文件。
3.  将镜像文件写入到到SD卡。使用工具： [win32diskimager]

### 2. 初次登录

1.  在其他电脑上，编辑SD卡上的`cmdline.txt`，给树莓派分配静态IP地址。例如，在已有行的末尾添加 `ip=192.168.1.100`。如果需要一同添加默认网关，则按 `ip=192.168.1.100::192.168.1.1` 的格式添加，双冒号后面的值是默认网关IP地址。
2.  用网线连接树莓派。接通电源启动树莓派。
3.  用SSH登录上述静态IP，默认用户pi，密码raspberry
4.  执行`sudo raspi-config`，执行`Expand Filesystem`。这样树莓派才能使用SD卡的全部空间。

**备注：**如果需要通过网线连接，需要在`cmdline.txt`中一同配置默认网关。如果不这么做，`cmdline.txt`的配置，会覆盖`/etc/network/interfaces`中以太网卡的配置，导致后者配置默认网关无效。

### 3. 网络配置

#### 如何让Pi连接至有线网络（不使用cmdline.txt)

建议通过配置`/etc/network/interfaces`的方式，实现复杂的有线网络设置。

设置了`/etc/network/intertaces`后，建议把`cmdline.txt`中的`ip=`一节去掉，以加块启动时间。

#### 如何让Pi自动连接到无线网络

1.  在树莓派上执行`sudo nano /etc/network/interfaces`
2.  编辑`interfaces`文件：

    ```
    auto lo

    iface lo inet loopback
    iface eth0 inet dhcp

    allow-hotplug wlan0
    auto wlan0

    iface wlan0 inet dhcp
       wpa-ssid "poi"
       wpa-psk "na*no*de*su*"
    ```

    即可配置为自动连接SSID为`poi`，密码为`na*no*de*su*`的无线网络。

3.  在计算机上建立批处理`enableHostedNetworkPi.bat`：

    ```
    echo
    netsh wlan set hostednetwork mode=allow ssid="poi" key=na*no*de*su*
    netsh wlan start hostednetwork
    pause
    ```
    
4.  在主机上执行批处理，并开启网络共享，网络共享将在192.168.137.1区段开启DHCP服务
5.  在Pi上执行`sudo /etc/init.d/networking restart`
6.  关闭Pi，拔掉以太网线。
7.  重新开启Pi。等待连接到无线网络。如果`cmdline.txt`中的`ip=`段没有去掉，这个时间可能比较长，约三分钟。
2.  在主机上，用`arp -a`查看ARP缓存，在192.168.137.1网段确认Pi的IP地址。
3.  SSH连接之。

### 4. 修改密码（可选）

1.  在Pi上执行`passwd`，修改密码。

### 5. 配置ssh（可选）

以下配置，将禁止直接通过没有密码的root账户，SSH登录树莓派。

1.  在Pi上执行`sudo nano /etc/ssh/sshd_config`
2.  编辑`PermitRootLogin no`

### 6. 更新软件包（可选）

1.  在Pi上执行`sudo apt-get update`

### 7. 配置Samba（可选）

1.  在Pi上执行`sudo apt-get install samba samba-common-bin`
2.  在Pi上编辑`sudo nano /etc/samba/smb.conf`  
    添加段：

    ```
    [pihome]
       commet = pi's home dir 
       path = /home/pi/
       browseable = yes
       read only = no
    ```

3. 添加samba用户：`sudo smbpasswd -a pi`，之后设置密码。
4. 重启samba服务：`sudo service samba restart`
5. 在主机上用用户`pi`访问即可。

### 8. 备份树莓派的SD卡

仍然在计算机上使用工具： [win32diskimager]，读取SD卡并保存为镜像即可。镜像可以压缩到比较小的体积。

- - -

[win32diskimager]: http://www.raspberry-projects.com/pi/pi-operating-systems/win32diskimager

## 连接数模转换器

如果要在Node上添加类型为`tlc1549`的传感器，可以按如下所示的电路连接，将电路图中`mcp9001`替换为`tlc1549`即可。

![](img\2201.png)

## 部署毕业设计的项目

以下步骤将安装毕业设计项目（pinic）所需的依赖项。

由于需要从树莓派和Python的包管理器安装依赖，所以在进行以下步骤前，请确保树莓派已经可以连接到互联网。

### 安装依赖项

#### 在树莓派上安装

通过SSH在树莓派上执行：

1. `sudo apt-get update` ，更新Linux系统包管理器apt-get的版本库
2. `sudo apt-get install python-dev libevent-dev python-setuptools` ，安装Python包管理器所需的一些其它包。
3. `sudo apt-get install python-pip` ，安装Python的包管理器PIP
4. `sudo pip install gevent` ，需要比较长时间。安装项目所需的Python包：gevent
5. `sudo pip install bottle` ，安装项目所需的Python包：bottle
6. `sudo pip install gevent-socketio` ，安装项目所需的Python包：gevent-socketio
7. `sudo pip install grequests` ，安装项目所需的Python包：grequests
8. `sudo pip install spidev` ，安装项目所需的Python包：spidev

#### 在Windows上安装

如果只需要在Windows上通过浏览器作为客户端连接到系统，则不需要安装任何依赖。浏览器建议使用IE 9以上，或者Chrome等现代浏览器。虽然理论上网页客户端可以兼容到IE 6，但在版本太低的IE上可能并不稳定。

如果需要在Windows系统上，通过Python运行项目的Node、Server或者Forwarder部分，则需要执行下面的部分，安装它们的依赖项。

1. 通过Python官方网站，安装Python 2.7。
2. 安装[Microsoft Visual C++ Compiler for Python 2.7]，gevent的安装需要这个。
3. 在命令提示符执行 `pip install gevent`
4. 在命令提示符执行 `pip install bottle`
6. 在命令提示符执行 `sudo pip install gevent-socketio`
7. 在命令提示符执行 `sudo pip install grequests`

## 配置毕业设计项目

如果运行毕业设计项目的树莓派或Windows系统已经安装好依赖项，之后将整个项目的目录，即`project`，放置在系统任意位置即可。无需其他安装。

项目目录下已经包含Node、Server和Forwarder三部分，可以任意运行，运行入口是`project`目录下的`runnode.py`、`runserver.py`和`runforwarder.py`。不过在运行之前，需要先编辑要运行的部分的配置文件。

Node的配置文件位于`project/config/node.conf`。

Server的配置文件位于`project/config/server.conf`。

Forwarder的配置文件位于`project/config/forwarder.conf`。

它们均是JSON格式存储的文本文件，在树莓派上用nano或者vim之类打开编辑即可。

### Node配置文件示例

`#`符号和之后的部分是为这份文档编写的说明，不能在实际的配置文件中出现。

```
    {
        "node_host":"0.0.0.0",               # Node程序的服务主机，如果需要让网络中任何主机均可访问，应设置为0.0.0.0。如果仅可让本机的其他程序访问，则设置为localhost。
        "node_port":9001,                    # Node程序的服务端口
        "node_id":"TEST-NODE-1",             # Node的ID，需要在网络中唯一，建议只包含字母、英文字符和减号、下划线，下同
        "node_desc":"Test node.",            # Node的描述文本
        "server_addr":"127.0.0.1",           # 要连接到的Server的IP地址
        "server_port":9011,                  # 要连接到的Server的端口
        "sensors":[                          # 连接到Node的传感器列表，可包含多个传感器
            {
                "sensor_type":"stub",            # 传感器的设备类型
                "sensor_id":"TEST-SENSOR-1",     # 传感器的ID，建议在网络中唯一
                "sensor_desc":"Test sensor.",    # 传感器描述文字
                "sensor_config": {}              # 传感器初始化配置，可留空（设置为{}）。
            },
            {
                "sensor_type":"random",          # 另一个类型的传感器
                "sensor_id":"TEST-SENSOR-2",
                "sensor_desc":"Another test sensor.",
                "sensor_config": {}                  
            }
        ],
        "filters":[                           # 报警数据过滤规则列表，可包含多个过滤规则
            {
                "apply_on_sensor_type":"none",     # 仅在特定类型的传感器上使用。设为"*"则包含任意传感器。
                "apply_on_sensor_id":"none",       # 仅在特定ID的传感器上使用。设为"*"则包含任意传感器。
                "comparing_method":"greater_than", # 可设置为"greater_than"和"less_than"。符合的数据不被视为报警。
                "threshold":50                     # 报警阈值。例如，"greater_than" 50，则大于50的数据不会被视为报警。
            }
        ]
    }
```

### Server配置文件示例

    {
        "server_host": "0.0.0.0",       # Server自身的服务主机，和Node的意义类似
        "server_port": 9011,            # Server自身的服务端口
        "server_id": "TEST-SERVER-1",   # Server的ID，需要在网络中唯一
        "server_desc": "地区A/地点1",    # Server的位置描述。以路径的方式配置。路径中的节点将在客户端中显示为Server的目录节点。
        "forwarder_addr": "127.0.0.1",  # 要连接到的Forwarder的IP地址
        "forwarder_port": 9021          # 要连接到的Server的端口
    }

### Forwarder配置文件示例

```
    {
        "forwarder_host": "0.0.0.0",              # Forwarder的服务主机，和Node的意义类似
        "forwarder_port": 9005,                   # Forwarder的服务端口
        "forwarder_id": "TEST-FORWARDER-1",       # Forwarder ID
        "forwarder_desc": "Test forwarder.",      # Forwarder的描述文字
    }
```

## 运行毕业设计项目

配置结束后即可运行项目所需的部分。

### 在树莓派上运行

要运行Node，在`project`目录下执行

```
nohup python runnode.py&
```

其中，nohup命令可以使命令输出重定向至nohup.out，而不会扰乱屏幕；末尾的&表示在后台执行。

如果出现问题，需要查看输出记录，则只需要执行

```
python runnode.py
```

要运行Server或Forwarder，只需要将上述的runnode.py替换为runserver.py或runforwarder.py。

要终止各部分的运行，直接杀死相应python进程即可。

### 在Windows上运行

使用命令提示符，在`project`目录下执行

```
python runnode.py
```

即可运行Node。其他部分相应改成runserver.py或runforwarder.py即可。

### 使用客户端

在网络中任意计算机或手机等的浏览器访问Forwarder的IP和端口即可。例如，Forwarder机器的IP地址为192.168.1.100，Forwarder端口号为9021（如上配置），则用浏览器访问`http://192.168.1.100:9021`即可。

## 关于项目目录结构和文档

有用的目录结构如下。要查看从注释自动生成的HTML版文档，打开project/docs/html/index.html即可。

```
project
├─config            # 存放程序配置文件，如上所述
├─docs              # Sphinx（从代码注释自动生成程序文档）工作目录
│  ├─_apidoc
│  └─_build
│      └─html           # 存放Sphinx自动生成的网页版程序文档（仅包含Python部分，不含JavaScript部分）
├─pinic             # 存放项目的Python部分
│  ├─forwarder          # 项目的Forwarder部分
│  ├─node               # 项目的Node部分
│  ├─sensor             # 项目的传感器驱动部分
│  ├─server             # 项目的Server部分
│  └─sysid              # 获取mac地址的功能
└─static            # 存放项目的前端网页部分，由Forwarder向客户端浏览器提供
    ├─css               # CSS样式表
    ├─html              # HTML页面
    └─js                # JavaScript部分
        └─lib               # 依赖的其他JavaScript库
```
