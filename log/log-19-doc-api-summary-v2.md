# Summary

```plain

Config of Node
	node_host
	node_port
	node_id
	node_desc

	server_addr
	server_port

	sensors:list of
		sensor_type
		sensor_id
		sensor_desc
		sensor_interval
	
	filters:list of
		apply_on_sensor_type
		apply_on_sensor_id
		comparing_method
		threshold

Config of Server
	server_host
	server_port
	server_id
	server_desc
	
	forwarder_addr
	forwarder_port

- - -

Node threads:

Main ----------- Main
        |   |
        |   ---- SensorMonitor(s)
        |
        ---- Server

Node workflow:

On start:
	Load config from default path
	Init sensors
	Init monitor threads
	Start bottle
	Reg to server(curl server/regnode)

GET /node/sensordata/<sensor_id>
	check sensor_id
	find monitor thread
	return sensordata from that thread

GET /node/nodeconfig/<node_id>
	check node_id
	return current nodeconfig

POST /node/nodeconfig/<node_id>
	check node_id
	parse new config
	unreg to server POST server_addr:server_port/server/unregnode
	stop sensors
	stop monitor threads
	apply new config
	init sensors
	init threads
	reg to server POST server_addr:server_port/server/regnode

GET /node/heartbeat/<node_id>
	check node_id
	return 200

- - -

Sensor thread workflow

On interval reached:
	Get data
	Check filter
	curl to server_addr:server_port/server/sensordata

- - -
- - -

Server monitor lock workflow

On heartbeat interval:
	curl node/heartbeat/<node_id>
	if failed, remove it from known node list and kill thread itself

- - -

Server threads:

Main ----------- Main
        |   |
        |   ---- NodeMonitor(s)
        |
        ---- Server

Server workflow:

On start:
	Load config from default path
	Start bottle
	Reg to forwarder
	get forwarder's ssh port
	open ssh reverse tunnel

POST /server/regnode
	parse nodeconfig from post load
	get origin ip from wsgi
	save (ip, port, id) to known nodes list
	start a thread to keep it alive

POST /server/unregnode
	parse nodeconfig from post load
	get origin ip from wsgi
	find (ip, port, id) from known nodes list
	if found, remove it
	stop thread

GET /server/serverconfig/server_id
	similiar to node

POST /server/serverconfig/server_id
	similiar to node

GET /server/nodeconfig/server_id/node_id
	find node_id in known node list
	if found, curl get /node/nodeconfig/node_id, return that

POST /server/serverconfig/server_id/node_id
	find node_id in known node list
	if found, curl post /node/nodeconfig/node_id, return its response

POST /server/sensordata
	curl to forwarder

- - -

Forwarder workflow:

POST /forwarder/regserver
	return available port
	add that port and server id to known server list

