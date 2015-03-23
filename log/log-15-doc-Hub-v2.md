# 文档: Hub模块

[TOC]

## 依赖

* `pycurl`，用于发送HTTP请求`pip install pycurl`
* `gevent` 1.0.1, 作为HTTP服务器`pip install gevent`
* `bottle` 0.12.8, 作为Web框架`pip install bottle`

## 安装

环境配置：

1. 需要python 2.7+ x86
2. `sudo apt-get install python-pycurl`
3. `sudo apt-get install python-dev libevent-dev python-setuptools`
3. `sudo pip install gevent` 需要很长时间……
4. `sudo pip install bottle`

将工程目录`project`作为当前目录。

## 运行

1. 配置hub.conf配置文件
2. 运行`python hub/hub.py`