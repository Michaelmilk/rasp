from bottle import Bottle, request
from gevent import monkey
from time import time

monkey.patch_all()
app = Bottle()

@app.get("/<url:re:.+>")
def show(url):
    print "===Request GET==="
    print "URL  ", url
    print "BODY ", request.body.read()
    print "TIME ", str(time())

@app.post("/<url:re:.+>")
def show(url):
    print "===Request POST==="
    print "URL  ", url
    print "BODY ", request.body.read()
    print "TIME ", str(time())

app.run(host="localhost", port=6001, server="gevent")
