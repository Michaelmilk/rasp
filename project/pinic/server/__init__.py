# -*- coding: utf-8 -*-

"""
server

这个包是项目的Server部分。

Server在启动时并不知道任何关于Node的信息。每一个Node启动后，
会自己向Server的/server/regnode注册，并以一定间隔发送心跳请求。

一段时间没有收到来自某个Node的心跳请求后，该Node将从已知Node列表中被删除。

如果要……
==========

* 要运行Server，请先配置Server的配置文件 ``project/config/server.conf`` ，再在项目根目录 ``project`` 下运行 ``python runserver.py`` 。

* 要更改Server的初始配置，可以参考serverconfig.py的文档。

"""

__author__ = 'tgmerge'
