(function(){
	var app = angular.module('pinicClient', []);

    app.factory('$socketio', function($rootScope) {
        var socket = io.connect('/warning');
        var status = "Connected";
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

    app.controller('WarningCtrl', ['$socketio', function($socketio) {

        this.warningText = 'Empty';
        this.socketStatus = 'Unconnected';
        this.socketStatus = $socketio.status;

        var warning = this;

        $socketio.on('warning', function(data) {
            info = JSON.parse(data.data);
            time = new Date(info.timestamp * 1000);
            warning.warningText = "[" + time.toString().split(' ')[4] + "] " + info.sensor_id + " -> " + info.raw_value + "\n" + warning.warningText;
            warning.warningText = warning.warningText.split("\n").slice(0, 10).join("\n")
        });
    }]);

	app.controller('ForwarderCtrl', ['$http', function($http) {
		
		this.config = 'Empty';
        this.newConfig = 'Empty';
        this.newConfigReply = 'Empty';
		this.serverList = 'Empty';
		
		var forwarder = this;
		
		this.getConfig = function() {
			$http.get('/forwarder/forwarderconfig').success(function(data) {
				forwarder.config = data;
			});
		};

        this.updateConfig = function() {
            $http.post('/forwarder/forwarderconfig', forwarder.newConfig).success(function(data) {
                forwarder.newConfigReply = data;
            }).error(function(data) {
                forwarder.newConfigReply = data;
            });
        };
		
		this.listServers = function() {
			$http.get('/forwarder/knownservers').success(function(data) {
				forwarder.serverList = data;
			});
		};
	
	}]);

	app.controller('ServerCtrl', ['$http', function($http) {

		this.serverId = '';
		this.config = 'Empty';
		this.nodeList = 'Empty';

		var server = this;

		this.getConfig = function() {
			$http.get('/server/serverconfig/' + server.serverId).success(function(data) {
				server.config = data;
			}).error(function(data) {
				server.config = data;
			});
		};

		this.listNodes = function() {
			$http.get('/server/knownnodes/' + server.serverId).success(function(data) {
				server.nodeList = data;
			}).error(function(data) {
				server.nodeList = data;
			});
		};

	}]);

	app.controller('NodeCtrl', ['$http', function($http) {

		this.serverId = '';
		this.nodeId = '';
		this.config = 'Empty';

		var node = this;

		this.getConfig = function() {
			$http.get('/server/nodeconfig/' + node.serverId + '/' + node.nodeId).success(function(data) {
				node.config = data;
			}).error(function(data) {
				node.config = data;
			});
		};

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
            sensor.chartDOM = document.getElementById('sensor-chart');
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
