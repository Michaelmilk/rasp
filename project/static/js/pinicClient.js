/**
 * Created by tgmerge on 5/9.
 */

(function() {
    var app = angular.module('pinicClient', []);

        app.service('constSrv', function() {
       return {
           TYPE_FORWARDER: 'FORWARDER',
           TYPE_SERVER: 'SERVER',
           TYPE_NODE: 'NODE',
           TYPE_SENSOR: 'SENSOR'
       };
    });

    app.service('apiSrv', ['$http', function($http) {
        var srv = {};

        srv.getForwarderConfig = function(succ, fail) {
            $http.get('/forwarder/forwarderconfig').success(succ).error(fail);
        };

        srv.getServerConfig = function(sId, succ, fail) {
            $http.get('/server/serverconfig/' + sId).success(succ).error(fail);
        };

        srv.getNodeConfig = function(sId, nId, succ, fail) {
            $http.get('/server/nodeconfig/' + sId + '/' + nId).success(succ).error(fail);
        };

        srv.setForwarderConfig = function(configJson, succ, fail) {
            $http.post('/forwarder/forwarderconfig', configJson).success(succ).error(fail);
        };

        srv.setServerConfig = function(configJson, sId, succ, fail) {
            $http.post('/server/serverconfig/' + sId, configJson).success(succ).error(fail);
        };

        srv.setNodeConfig = function(configJson, sId, nId, succ, fail) {
            $http.post('/server/nodeconfig/' + sId + '/' + nId, configJson).success(succ).error(fail);
        };

        srv.getSensorData = function(sId, nId, senId, succ, fail) {
            $http.get('/server/sensordata/' + sId + '/' + nId + '/' + senId).success(succ).error(fail);
        };

        srv.getKnownNodesOfServer = function(sId, succ, fail) {
            $http.get('/server/knownnodes/' + sId).success(succ).error(fail);
        };

        srv.getKnownServersOfForwarder = function(succ, fail) {
            $http.get('/forwarder/knownservers').success(succ).error(fail);
        };

        return srv;
    }]);

    app.service('devicesSrv', ['apiSrv', 'constSrv', function(apiSrv, constSrv) {
        var srv = {};

        srv.newSensor = function() {
            return {
                deviceType: constSrv.TYPE_SENSOR,
                config: {
                    id: '',
                    type: '',
                    desc: '',
                    value: ''
                }
            };
        };

        srv.newNode = function() {
            return {
                deviceType: constSrv.TYPE_NODE,
                config: {
                    id: '',
                    addr: '',
                    port: '',
                    desc: ''
                },
                sensors: []
            };
        };

        srv.newServer = function() {
            return {
                deviceType: constSrv.TYPE_SERVER,
                config: {
                    id: '',
                    addr: '',
                    port: '',
                    desc: ''
                },
                nodes: []
            }
        };

        srv.newForwarder = function() {
            return {
                deviceType: constSrv.TYPE_FORWARDER,
                config: {
                    id: '',
                    addr: '',
                    port: '',
                    desc: ''
                },
                servers: []
            }
        };

        srv.addSensorToNode = function(sensor, node) {
            node.sensors.push(sensor);
        };

        srv.addNodeToServer = function(node, server) {
            server.nodes.push(node);
        };

        srv.addServerToForwarder = function(server, forwarder) {
            forwarder.servers.push(server);
        };

        // Update sensor. Only update its raw value.
        // Sensor.config.id should be already set
        // TODO load sensor value parse function and parse it
        srv.updateSensor = function(server, node, sensor) {
            apiSrv.getSensorData(server.config.id, node.config.id, sensor.config.id, function(data) {
                // success
                sensor.config.value = data;
            }, function(data) {
                // error
                sensor.config.value = 'Error: ' + data;
            });
        };

        // Update node and its child-devices
        // Node.config.id, addr, port, desc should be already set
        srv.updateNodeAndChild = function(server, node) {
            node.sensors = [];
            apiSrv.getNodeConfig(server.config.id, node.config.id, function(data) {
                // success
                for (var i = 0; i < data.sensors.length; i ++) {
                    var newSensor = srv.newSensor();
                    newSensor.config.type = data.sensors[i].sensor_type;
                    newSensor.config.id = data.sensors[i].sensor_id;
                    newSensor.config.desc = data.sensors[i].sensor_desc;
                    srv.addSensorToNode(newSensor, node);
                    srv.updateSensor(server, node, newSensor);
                }
            }, function(data) {
                // error

            });
        };

        // Update server and its child-devices
        // Server.config.id, addr, port, desc should be already set
        srv.updateServerAndChild = function(server) {
            server.nodes = [];
            apiSrv.getKnownNodesOfServer(server.config.id, function(data) {
                // success
                for (var i = 0; i < data.length; i ++) {
                    var newNode = srv.newNode();
                    newNode.config.id = data[i].id;
                    newNode.config.addr = data[i].addr;
                    newNode.config.port = data[i].port;
                    newNode.config.desc = data[i].desc;
                    srv.addNodeToServer(newNode, server);
                    srv.updateNodeAndChild(server, newNode);
                }
            }, function(data) {
                // error

            });
        };

        // Update forwarder and its child-devices
        // Forwarder.config.id, addr, etc should be already set
        srv.updateForwarderAndChild = function(forwarder) {
            forwarder.servers = [];
            console.log('here');
            apiSrv.getKnownServersOfForwarder(function(data) {
                // success
                for (var i = 0; i < data.length; i ++) {
                    var newServer = srv.newServer();
                    newServer.config.id = data[i].id;
                    newServer.config.addr = data[i].addr;
                    newServer.config.port = data[i].port;
                    newServer.config.desc = data[i].desc;
                    srv.addServerToForwarder(newServer, forwarder);
                    srv.updateServerAndChild(newServer);
                }
            }, function(data) {
                // error

            });
        };

        // Update WHOLE system's device tree.
        // ONLY USE THIS METHOD OF THIS SERVICE.
        // Pass an object in, and you'll get the whole tree in that object's 'forwarder' property.
        srv.updateDevices = function(obj) {
            obj.forwarder = srv.newForwarder();
            apiSrv.getForwarderConfig(function(data) {
                // success
                obj.forwarder.config.id = data.forwarder_id;
                obj.forwarder.config.desc = data.forwarder_desc;
                obj.forwarder.config.port = data.forwarder_port;
                obj.forwarder.config.addr = 'host_addr';
                srv.updateForwarderAndChild(obj.forwarder);
            }, function(data) {
                // error

            });
        };

        return srv;
    }]);

    app.controller('DeviceTreeCtrl', ['devicesSrv', '$scope', function(devicesSrv, self) {

        self.deviceData = {};

        devicesSrv.updateDevices(self.deviceData);

    }]);

})();