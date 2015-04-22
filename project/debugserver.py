# coding=utf-8

"""
本Python模块包含一个测试用的Web服务器。

它以gevent作为HTTP服务器，显示所有收到的POST和GET请求。

要启动服务器，直接运行本模块。
"""

__author__ = "tgmerge"


from gevent import monkey
monkey.patch_all()
from bottle import Bottle, request
from time import time

app = Bottle()  # A server printing all requests

@app.get("/<url:re:.+>")
def show_get(url):
    print "===Request GET==="
    print "URL  ", url
    print "BODY ", request.body.read()
    print "TIME ", str(time())

@app.post("/<url:re:.+>")
def show_post(url):
    print "===Request POST==="
    print "URL  ", url
    print "BODY ", request.body.read()
    print "TIME ", str(time())


if __name__ == "__main__":
    app.run(host="localhost", port=9002, server="gevent")
