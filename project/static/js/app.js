/**
 * Created by tgmerge on 5/1.
 */

(function() {
	var app = angular.module('pinicClient', []);

    app.service('socketIO', function($rootScope) {
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

    app.service('deviceRefreshService', ['$rootScope', function($rootScope) {
        var srv = {};
        srv.broadcast = function() {
            $rootScope.$broadcast('deviceRefreshService');
        };
        srv.listen = function(callback) {
            $rootScope.$on('deviceRefreshService', callback);
        };
        return srv;
    }]);

    app.service('deviceConfigService', ['$http', '$rootScope', function($http, $rootScope) {
        var srv = {};

        srv.deviceType = '';
        srv.forwarderId = '';
        srv.serverId = '';
        srv.nodeId = '';

        srv.broadcastDeviceToConfig = function(type, fId, sId, nId) {
            srv.deviceType = type;
            srv.forwarderId = fId;
            srv.serverId = sId;
            srv.nodeId = nId;
            $rootScope.$broadcast('deviceConfigService');
        };

        srv.listenDeviceToConfig = function(callback) {
            $rootScope.$on('deviceConfigService', callback);
        };

        srv.getCurrentConfig = function(type, fId, sId, nId, success, error) {
            var url = '';
            if (type == 'forwarder') {
                url = '/forwarder/forwarderconfig';
            } else if (type == 'server') {
                url = '/server/serverconfig/' + sId;
            } else if (type == 'node') {
                url = '/server/nodeconfig/' + sId + '/' + nId;
            }
            $http.get(url).success(success).error(error);
        };

        return srv;
    }]);

    app.service('chartService', ['$rootScope', function($rootScope) {
        var srv = {};
        srv.forwarderId = '';
        srv.serverId = '';
        srv.nodeId = '';
        srv.sensorId = '';
        srv.methods = {
            STOP: 0,
            START: 1,
            CLEAR: 2
        };
        srv.action = srv.methods.STOP;
        srv.stop = function() {
            srv.action = srv.methods.STOP;
            $rootScope.$broadcast('chartService');
        };
        srv.start = function(forwarderId, serverId, nodeId, sensorId) {
            srv.action = srv.methods.START;
            srv.forwarderId = forwarderId;
            srv.serverId = serverId;
            srv.nodeId = nodeId;
            srv.sensorId = sensorId;
            $rootScope.$broadcast('chartService');
        };
        srv.clear = function() {
            srv.action = srv.methods.CLEAR;
            $rootScope.$broadcast('chartService');
        };
        srv.listen = function(callback) {
            $rootScope.$on('chartService', callback);
        };
        return srv;
    }]);

    app.service('deviceListService', ['$http', function($http) {
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

    app.controller('ControlCtrl', ['$scope', 'deviceRefreshService', 'chartService', function($scope, deviceRefreshService, chartService) {

        $scope.listDevices = function() {
            deviceRefreshService.broadcast();
        };

        $scope.stopChart = function() {
            chartService.stop();
        }
    }]);

    app.controller('DevicesCtrl', ['$scope', 'deviceRefreshService', 'deviceListService', 'deviceConfigService', 'chartService', function($scope, deviceRefreshService, deviceListService, deviceConfigService, chartService) {

        $scope.deviceData = {};

        deviceListService.prepare($scope.deviceData);

        deviceRefreshService.listen(function () {
            deviceListService.updateAll();
        });

        $scope.selectToConfig = function(dType, fId, sId, nId) {
            deviceConfigService.broadcastDeviceToConfig(dType, fId, sId, nId);
        };

        $scope.selectToDraw = function(fId, sId, nId, senId) {
            chartService.start(fId, sId, nId, senId);
        };
    }]);

    app.controller('DeviceConfigCtrl', ['$scope', '$http', 'deviceConfigService', function($scope, $http, deviceConfigService) {

        $scope.deviceType = 'forwarder';
        $scope.forwarderId = '';
        $scope.serverId = '';
        $scope.nodeId = '';

        $scope.currentConfig = '';

        $scope.newConfig = '';

        deviceConfigService.listenDeviceToConfig(function () {
            var srv = deviceConfigService;
            $scope.deviceType = srv.deviceType;
            $scope.forwarderId = srv.forwarderId;
            $scope.serverId = srv.serverId;
            $scope.nodeId = srv.nodeId;
            $scope.currentConfig = srv.getCurrentConfig($scope.deviceType, $scope.forwarderId, $scope.serverId, $scope.nodeId,
                function(data) {
                    $scope.currentConfig = data;
                },
                function(data) {
                    $scope.currentConfig = data;
                }
            );
        });
    }]);

    app.controller('ChartCtrl', ['$scope', '$http', '$interval', 'chartService', function($scope, $http, $interval, chartService) {

        $scope.chartOptions = {
            bindto: '#sensor-chart',
            legend: {
                show: false
            },
            transition: {
                duration: 0
            },
            axis: {
                x: {
                    type: 'timeseries',
                    tick: {
                        format: '%I:%M:%S',
                        count: 3
                    }
                }
            },
            data: {
                //type: 'spline',
                x: 'x',
                columns: [
                    ['x', 0],
                    ['y', 0]
                ]
            }
        };

        $scope.chart = null;
        $scope.isChartRunning = false;
        $scope.chartTimer = null;
        $scope.dataX = [];
        $scope.dataY = [];

        $scope.chartInterval = 500;
        $scope.serverId = '';
        $scope.nodeId = '';
        $scope.sensorId = '';

        chartService.listen(function() {
           if (chartService.action == chartService.methods.START) {
               $scope.serverId = chartService.serverId;
               $scope.nodeId = chartService.nodeId;
               $scope.sensorId = chartService.sensorId;
               $scope.startChart();
           } else if (chartService.action == chartService.methods.STOP) {
               $scope.stopChart();
           } else if (chartService.action == chartService.methods.CLEAR) {
               $scope.clearChart();
           }
        });

        $scope.addChartData = function() {
            $http.get('/server/sensordata/' + $scope.serverId + '/' + $scope.nodeId + '/' + $scope.sensorId).success(function(data) {
                $scope.dataX.push(new Date(data.timestamp * 1000));
                $scope.dataY.push(data.raw_value);
                if ($scope.dataX.length > 40) {
                    $scope.dataX.shift();
                    $scope.dataY.shift();
                }
                $scope.chart.load({
                    columns: [
                        ['x'].concat($scope.dataX),
                        ['y'].concat($scope.dataY)
                    ]
                });
            });
        };

        $scope.initChart = function() {
            if ($scope.chart != null) {
                $scope.chart.destroy();
            }

            $scope.dataX = [];
            $scope.dataY = [];

            for(var i = 0; i < 40; i ++) {
                $scope.dataX.push(new Date());
                $scope.dataY.push(0);
            }

            $scope.chart = c3.generate($scope.chartOptions);
        };

        $scope.startChart = function() {
            $scope.stopChart();
            $scope.initChart();
            $scope.chartTimer = $interval($scope.addChartData, $scope.chartInterval);
            $scope.isChartRunning = true;
        };

        $scope.stopChart = function() {
            if ($scope.chartTimer != null) {
                $interval.cancel($scope.chartTimer);
                $scope.chartTimer = null;
            }
            $scope.isChartRunning = false;
        };

        $scope.clearChart = function() {
            $scope.stopChart();
            $scope.dataX = [];
            $scope.dataY = [];
            if ($scope.chart != null) {
                $scope.chart.destroy();
            }
        };

    }]);

    app.controller('WarningCtrl', ['socketIO', function(socketIO) {

        this.warningText = 'Empty';
        this.socketStatus = 'Unconnected';

        var warning = this;

        socketIO.on('warning', function(data) {
            var info = JSON.parse(data.data);
            var time = new Date(info.timestamp * 1000);
            warning.warningText = "[" + time.toString().split(' ')[4] + "] " + info.sensor_id + " -> " + info.raw_value + "\n" + warning.warningText;
            warning.warningText = warning.warningText.split("\n").slice(0, 10).join("\n")
        });
    }]);


    app.controller('SensorCtrl', ['$http', '$interval', function($http, $interval) {

		this.serverId = 'SERVER-RPi-01';
		this.nodeId = 'NODE-RPi-01';
		this.sensorId = 'TLC1549';
		this.sensorData = 'Empty';

		this.chartInterval = 2000;

        this.chart = null;
        this.chartDOM = null;
		this.isChartRunning = false;
		this.chartTimer = null;
        this.chartData = [[new Date(), 0]];

        this.chartOptions = {
            drawPoints: true,
            showRoller: true,
            labels: ['Time', 'SensorValue']
        };


		var sensor = this;

		this.getSensorData = function() {
			$http.get('/server/sensordata/' + sensor.serverId + '/' + sensor.nodeId + '/' + sensor.sensorId).success(function(data) {
				sensor.sensorData = data;
			}).error(function(data) {
				sensor.sensorData = data;
			});
		};

		this.initChart = function() {
            sensor.chartDOM = document.getElementById('sensor-chart-dy');
            if(sensor.chart != null) {
				sensor.chart.destroy();
			}
			sensor.chart = new Dygraph(sensor.chartDOM, sensor.chartData, sensor.chartOptions);
            sensor.chartOptions.labels[1] = sensor.sensorId;
		};

		this.addChartData = function() {
			$http.get('/server/sensordata/' + sensor.serverId + '/' + sensor.nodeId + '/' + sensor.sensorId).success(function(data) {
				sensor.sensorData = data;
                var x = new Date(data.timestamp * 1000);
                var y = data.raw_value;
                sensor.chartData.push([x, y]);
                if (sensor.chartData.length > 100) {
                    sensor.chartData.shift();
                }
                console.log(sensor.chartData);
                sensor.chart.updateOptions({'file': sensor.chartData});
			}).error(function(data) {
				sensor.sensorData = data;
			});
		};

		this.startChart = function() {
			if (sensor.chart == null) {
				sensor.initChart()
			}
			sensor.chartTimer = $interval(sensor.addChartData, sensor.chartInterval);
			sensor.isChartRunning = true;
		};

		this.stopChart = function() {
			$interval.cancel(sensor.chartTimer);
			sensor.isChartRunning = false;
		};

        this.clearChart = function() {
            sensor.stopChart();
            sensor.chartData = [];
            if (sensor.chart != null) {
                sensor.chart.updateOptions({'file': sensor.chartData}, false);
            }
        };

	}]);

})();
