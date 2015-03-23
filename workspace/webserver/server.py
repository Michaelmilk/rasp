# -*- coding: utf-8 -*-
from bottle import Bottle, route, run, response
from json import dumps

server = Bottle()
import display_tlc1549_value as tlc1549

with server:
	@route("/value/get")
	def getValue():
		response.content_type = "application/json"
		valueJson = { "value": tlc1549.readValue() }
		return dumps(valueJson)

run(app=server, host="0.0.0.0", port=8080)
print "Server is running"
