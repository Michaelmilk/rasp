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

		this.serverId = 'TEST-SERVER-1';
		this.nodeId = 'TEST-NODE-1';
		this.sensorId = 'TEST-SENSOR-STUB-2';
		this.sensorData = 'Empty';

		this.chart = null;
		this.isChartRunning = false;
		this.chartTimer = null;
		this.chartInterval = 2000;
		this.lineChartData = {
			labels: [''],
			datasets: [{
	            fillColor: "rgba(151,187,205,0.2)",
	            strokeColor: "rgba(151,187,205,1)",
	            pointColor: "rgba(151,187,205,1)",
	            pointStrokeColor: "#fff",
	            pointHighlightFill: "#fff",
	            pointHighlightStroke: "rgba(151,187,205,1)",
				label: "Sensor ",
				data: [0]
			}]
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
			var ctx = document.getElementById('sensor-chart').getContext('2d');
			if(sensor.chart != null) {
				sensor.chart.clear();
			}
			sensor.lineChartData.datasets[0].label = "Sensor " + sensor.sensorId;
			sensor.chart = new Chart(ctx).Line(sensor.lineChartData, {
				responsive: true,
				bezierCurve : false,
				animationSteps: 5
			});
		};

		this.addChartData = function() {
			$http.get('/server/sensordata/' + sensor.serverId + '/' + sensor.nodeId + '/' + sensor.sensorId).success(function(data) {
				sensor.sensorData = data;
				if(sensor.lineChartData.datasets[0].data.length > 40) {
					sensor.lineChartData.datasets[0].data.shift();
					sensor.chart.removeData();
				}
				sensor.lineChartData.datasets[0].data.push(data.raw_value);
				sensor.chart.addData([data.raw_value], '');
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
            var len = sensor.chart.datasets[0].points.length;
            for (var i = 0; i < len; i ++)
                sensor.chart.removeData();
            sensor.lineChartData.datasets[0].data = [0];
        };

	}]);

})();
