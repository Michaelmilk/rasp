/**
 * Created by tgmerge on 5/8.
 */

(function() {
    var app = angular.module('pinicClientService');


    app.service('socketio', function($rootScope) {
        var socket = io.connect('/warning');
        return {
            on: function(eventName, callback) {
                socket.on(eventName, function() {
                    var args = arguments;
                    $rootScope.$apply(function() {
                        callback.apply(socket, args);
                    });
                });
            },
            emit: function(eventName, data, callback) {
                socket.emit(eventName, data, function() {
                    var args = arguments;
                    $rootScope.$apply(function() {
                        if (callback) {
                            callback.apply(socket, args);
                        }
                    });
                })
            }
        };
    });


    app.service('refreshDeviceMsg', function($rootScope) {
        var srv = {};
        srv.broadcast = function() {
            $rootScope.$broadcast('refreshDeviceMsg');
        };
        srv.listen = function(callback) {
            $rootScope.$on('refreshDeviceMsg', callback);
        };
        return srv;
    });


    app.service('chartMsg', function($rootScope) {
        var srv = {};
        srv.forwarderId = '';
        srv.serverId = '';
        srv.nodeId = '';
        srv.sensorId = '';
        srv.timeInterval = 1000; //ms
        srv.methods = {
            STOP: 0,
            START: 1,
            CLEAR: 2
        };
        srv.action = srv.methods.STOP;
        srv.stop = function() {
            srv.action = srv.methods.STOP;
            $rootScope.$broadcast('chartMsg');
        };
        srv.start = function(forwarderId, serverId, nodeId, sensorId, timeInterval) {
            srv.action = srv.methods.START;
            srv.forwarderId = forwarderId;
            srv.serverId = serverId;
            srv.nodeId = nodeId;
            srv.sensorId = sensorId;
            srv.timeInterval = timeInterval;
            $rootScope.$broadcast('chartMsg');
        };
        srv.clear = function() {
            srv.action = srv.methods.CLEAR;
            $rootScope.$broadcast('chartMsg');
        };
        srv.listen = function(callback) {
            $rootScope.$on('chartMsg', callback);
        };
        return srv;
    });


    app.service('deviceList', ['$http', function($http) {
        var srv = {};
        srv.newSensor = function(sensorId) {
            return {
                type: 'sensor',
                id: sensorId
            };
        };
        srv.newNode = function(nodeId) {
            return {
                type: 'node',
                id: nodeId,
                sensors: []
            };
        };
        srv.newServer = function(serverId) {
            return {
                type: 'server',
                id: serverId,
                nodes: []
            };
        };
        srv.newForwarder = function(forwarderId) {
            return {
                type: 'forwarder',
                id: forwarderId,
                servers: []
            };
        };

        srv.addServerToForwarder = function(server, forwarder) {
            forwarder.servers.push(server);
        };
        srv.addNodeToServer = function(node, server) {
            server.nodes.push(node);
        };
        srv.addSensorToNode = function(sensor, node) {
            node.sensors.push(sensor);
        };

        srv.updateSubDevicesOfNode = function(server, node) {
			node.sensors = [];
            $http.get('/server/nodeconfig/' + server.id + '/' + node.id).success(function(data) {
                for (var i = 0; i < data.sensors.length; i ++) {
                    srv.addSensorToNode(srv.newSensor(data.sensors[i].sensor_id), node);
                }
			}).error(function(data) {
                console.log("Error on updateSubDevicesOfNode.");
                console.log(data);
			});
        };
        srv.updateSubDevicesOfServer = function(server) {
            server.nodes = [];
			$http.get('/server/knownnodes/' + server.id).success(function(data) {
				for (var i = 0; i < data.length; i ++) {
                    var node = srv.newNode(data[i].id);
                    srv.addNodeToServer(node, server);
                    srv.updateSubDevicesOfNode(server, node);
                }
			}).error(function(data) {
                console.log("Error on updateSubDevicesOfServer.");
                console.log(data);
			});
        };
        srv.updateSubDevicesOfForwarder = function(forwarder) {
            forwarder.servers = [];
            $http.get('/forwarder/knownservers').success(function(data) {
                for (var i = 0; i < data.length; i ++) {
                    var server = srv.newServer(data[i].id);
                    srv.addServerToForwarder(server, forwarder);
                    srv.updateSubDevicesOfServer(server);
                }
            }).error(function(data) {
                console.log("Error on updateSubDevicesOfForwarder.");
                console.log(data);
            });
        };

        srv.updateAll = function() {
            srv.deviceData.forwarder = srv.newForwarder('');
            srv.updateSubDevicesOfForwarder(srv.deviceData.forwarder);
			$http.get('/forwarder/forwarderconfig').success(function(data) {
				srv.deviceData.forwarder.id = data.forwarder_id;
			});
        };

        srv.prepare = function(obj) {
            srv.deviceData = obj;
        };

        return srv;
    }]);

})();
