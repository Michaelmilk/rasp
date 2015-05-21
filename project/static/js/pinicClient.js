/**
 * Created by tgmerge on 5/9.
 */
'use strict';

(function() {
    var app = angular.module('pinicClient', []);

    app.directive('deviceTreeTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'device-tree-tab.html'
        };
    });

    app.directive('deviceListTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'device-list-tab.html'
        };
    });

    app.directive('warningTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'warning-tab.html'
        };
    });

    app.directive('chartTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'chart-tab.html'
        };
    });

    app.directive('forwarderConfigTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'forwarder-config-tab.html'
        };
    });

    app.directive('serverConfigTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'server-config-tab.html'
        };
    });

    app.directive('nodeConfigTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'node-config-tab.html'
        };
    });

    app.controller('tabController', ['tabSrv', '$scope', function(tabSrv, self) {
        self.tabIsSet = function(checkTab) {
            return tabSrv.tabIsSet(checkTab);
        };

        self.setTab = function(activeTab) {
            tabSrv.setTab(activeTab);
        };
    }]);

    app.service('valueConvertSrv', function() {
        var srv = {};

        // return [convertedValue, unit].
        srv.convertFunctions = {
            'tlc1549': function(value) {
                // u/v = r/(250+r), v is 5V DC, u is detected voltage
                // ->
                // raw/1024 = r/(250+r)
                // ->
                // r = 250raw/(1024-raw)
                var raw = Number(value);
                var r = (250.0 * raw) / (1024.01 - raw);
                return [r, 'Ω'];
            },
            'stub': function(value) {
                return [value, '次'];
            },
            'random': function(value) {
                return [Math.ceil(value), ''];
            }
        };

        srv.convert = function(type, raw_value) {
            if (type in srv.convertFunctions) {
                return srv.convertFunctions[type](raw_value).join('');
            } else {
                return raw_value;
            }
        };

        srv.convertWithoutFormat = function(type, raw_value) {
            if (type in srv.convertFunctions) {
                return srv.convertFunctions[type](raw_value)[0];
            } else {
                return raw_value;
            }
        };

        return srv;
    });

    app.service('tabSrv', function() {
        var srv = {};

        srv.tab = 1;

        srv.tabIsSet = function(checkTab) {
            return srv.tab === checkTab;
        };

        srv.setTab = function(activeTab) {
            srv.tab = activeTab;
        };

        return srv;
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

    app.service('devicesSrv', ['apiSrv', 'valueConvertSrv', function(apiSrv, valueConvertSrv) {
        var srv = {};

        srv.const = {
            TYPE_FORWARDER: 'FORWARDER',
            TYPE_SERVER: 'SERVER',
            TYPE_NODE: 'NODE',
            TYPE_SENSOR: 'SENSOR'
        };

        srv.newSensor = function() {
            return {
                deviceType: srv.const.TYPE_SENSOR,
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
                deviceType: srv.const.TYPE_NODE,
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
                deviceType: srv.const.TYPE_SERVER,
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
                deviceType: srv.const.TYPE_FORWARDER,
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
                // todo changed!
                sensor.config.value = valueConvertSrv.convert(data.sensor_type, data.raw_value);
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

    app.service('broadcastSrv', ['$rootScope', function($rootScope) {
        var srv = {};

        srv.msgs = {};

        srv.const = {
            // device type, used in show_config broadcast
            DEVICE_FORWARDER: 'FORWARDER',
            DEVICE_SERVER: 'SERVER',
            DEVICE_NODE: 'NODE',
            DEVICE_SENSOR: 'SENSOR',

            // broadcast type
            JUMP_PAGE: 'JUMP_PAGE',
            SHOW_SUBTREE: 'SHOW_SUBTREE',
            SHOW_CONFIG: 'SHOW_CONFIG',
            SHOW_CHART: 'SHOW_CHART',
            SHOW_WARNING: 'SHOW_WARNING',
            REFRESH_TREE: 'REFRESH_TREE'
        };

        srv.sayJumpPage = function(toPageNo) {
            srv.msgs[srv.const.JUMP_PAGE] = {
                toPageNo: toPageNo
            };
            $rootScope.$broadcast(srv.const.JUMP_PAGE);
        };

        // to get 'toPageNo', use
        //     broadcastSrv.msgs[broadcastSrv.const.JUMP_PAGE].toPageNo
        srv.onJumpPage = function(callback) {
            $rootScope.$on(srv.const.JUMP_PAGE, callback);
        };

        srv.sayShowSubtree = function(server) {
            srv.msgs[srv.const.SHOW_SUBTREE] = {
                server: server
            };
            $rootScope.$broadcast(srv.const.SHOW_SUBTREE);
        };

        // to get 'server', use
        //     broadcastSrv.msgs[broadcastSrv.const.SHOW_SUBTREE].server
        srv.onShowSubtree = function(callback) {
            $rootScope.$on(srv.const.SHOW_SUBTREE, callback);
        };

        srv.sayShowConfig = function(deviceType, fId, sId, nId, senId) {
            srv.msgs[srv.const.SHOW_CONFIG] = {
                deviceType: deviceType,
                fId: fId,
                sId: sId,
                nId: nId,
                senId: senId
            };
            $rootScope.$broadcast(srv.const.SHOW_CONFIG);
        };

        srv.onShowConfig = function(callback) {
            $rootScope.$on(srv.const.SHOW_CONFIG, callback);
        };

        // timeInterval - ms
        srv.sayShowChart = function(sId, nId, senId, timeInterval) {
            srv.msgs[srv.const.SHOW_CHART] = {
                sId: sId,
                nId: nId,
                senId: senId,
                timeInterval: timeInterval
            };
            $rootScope.$broadcast(srv.const.SHOW_CHART);
        };

        srv.onShowChart = function(callback) {
            $rootScope.$on(srv.const.SHOW_CHART, callback);
        };

        srv.sayShowWarning = function(deviceType, fId, sId, nId, senId, value) {
            srv.msgs[srv.const.SHOW_WARNING] = {
                deviceType: deviceType,
                fId: fId,
                sId: sId,
                nId: nId,
                senId: senId,
                value: value
            };
            $rootScope.$broadcast(srv.const.SHOW_WARNING);
        };

        srv.onShowWarning = function(callback) {
            $rootScope.$on(srv.const.SHOW_WARNING, callback);
        };

        srv.sayRefreshTree = function() {
            srv.msgs[srv.const.REFRESH_TREE] = {};
            $rootScope.$broadcast(srv.const.REFRESH_TREE);
        };

        srv.onRefreshTree = function(callback) {
            $rootScope.$on(srv.const.REFRESH_TREE, callback);
        };

        return srv;
    }]);

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

    app.controller('DeviceTreeCtrl', ['tabSrv', 'devicesSrv', 'broadcastSrv', '$interval', '$scope', function(tabSrv, devicesSrv, broadcastSrv, $interval, self) {

        self.deviceData = {};

        self.hostName = window.location.hostname;

        self.refreshTimer = null;

        // --- Function of controller

        self.refreshTree = function() {
            devicesSrv.updateDevices(self.deviceData);
        };

        self.lastShownServerId = '';

        self.showServerInDeviceList = function(server) {
            self.lastShownServerId = server.config.id;
            broadcastSrv.sayShowSubtree(server);
        };

        self.refreshServerInDeviceList = function() {
            if (self.lastShownServerId === undefined || self.lastShownServerId === '') {
                return;
            }
            var servers = self.deviceData.forwarder.servers;
            for (var k in servers) {
                if (servers[k].config.id === self.lastShownServerId) {
                    broadcastSrv.sayShowSubtree(servers[k]);
                    break;
                }
            }
        };

        self.showForwarderConfig = function() {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_FORWARDER);
            tabSrv.setTab(3);
        };

        self.showServerConfig = function(sId) {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_SERVER, null, sId);
            tabSrv.setTab(4);
        };

        // --- Listener of broadcast

        broadcastSrv.onRefreshTree(function() {
            self.refreshTree();
        });

        self.refreshTree();
        // todo make time interval changeable
        self.refreshTimer = $interval(function() {
            self.refreshServerInDeviceList();
            self.refreshTree();
        }, 15000);
    }]);

    app.controller('DeviceListCtrl', ['tabSrv', 'broadcastSrv', 'valueConvertSrv', '$scope', function(tabSrv, broadcastSrv, valueConvertSrv, self) {

        self.server = {};

        // --- Function of controller

        // server is a 'server' object in deviceData of devicesSrv.
        // it will be DEEP COPIED to this controller.
        self.loadSubTree = function(server) {
            self.server = {};
            self.server = server;
        };

        self.removeWarning = function(device) {
            if (device != undefined) {
                device.isWarning = false;
            }
        };

        self.removeNodeAndSubDeviceWarning = function(device) {
            if (device != undefined) {
                for (var sensor in device.sensors) {
                    device.sensors[sensor].isWarning = false;
                }
                device.isWarning = false;
            }
        };

        self.toSensorChart = function(sId, nId, senId) {
            tabSrv.setTab(2);
            broadcastSrv.sayShowChart(sId, nId, senId, 500);
        };

        self.showServerConfig = function(sId) {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_SERVER, null, sId);
            tabSrv.setTab(4);
        };

        self.showNodeConfig = function(sId, nId) {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_NODE, null, sId, nId);
            tabSrv.setTab(5);
        };

        // --- Broadcast listener

        broadcastSrv.onShowSubtree(function() {
            self.loadSubTree(broadcastSrv.msgs[broadcastSrv.const.SHOW_SUBTREE].server);
        });

        broadcastSrv.onShowWarning(function() {
            if (typeof self.server !== 'object' || typeof self.server.nodes !== 'object') {
                return;
            }
            var msg = angular.copy(broadcastSrv.msgs[broadcastSrv.const.SHOW_WARNING]);
            var sId = msg.sId;
            var nId = msg.nId;
            var senId = msg.senId;
            var value = msg.value;
            if (typeof(self.server.config) !== 'undefined' && sId === self.server.config.id) {
                self.server.isWarning = true;
            }
            var nodes = self.server.nodes;
            for (var i = 0; i < nodes.length; i ++) {
                var node = nodes[i];
                if (nId === node.config.id) {
                    node.isWarning = true;
                    var sensors = node.sensors;
                    for (var j = 0; j < sensors.length; j ++) {
                        var sensor = sensors[j];
                        if (senId === sensor.config.id) {
                            sensor.isWarning = true;
                            sensor.config.value = valueConvertSrv.convert(sensor.config.type, value);
                        }
                    }
                }
            }
        });

    }]);

    app.controller('WarningCtrl', ['socketIO', 'broadcastSrv', 'valueConvertSrv', '$scope', function(socketIO, broadcastSrv, valueConvertSrv, self) {

        self.warningItems = [];
        self.maxWarningNum = 6;

        // --- Function of controller

        self.highlightDevice = function(sId, nId, senId, value) {
            broadcastSrv.sayShowWarning(null, null, sId, nId, senId, value)
        };

        self.addWarningItem = function(date, deviceName, sensorName, sensorType, infoType, value) {
            var warningItem = {
                timeString: date.toString().split(' ')[4],
                deviceName: deviceName,
                sensorName: sensorName,
                sensorType: sensorType,
                infoType: infoType,
                value: valueConvertSrv.convert(sensorType, value)
            };

            // Add warning item
            self.warningItems.unshift(warningItem);

            // Delete eldest items if necessary
            if (self.warningItems.length > self.maxWarningNum) {
                self.warningItems.splice(self.maxWarningNum, self.warningItems.length-self.maxWarningNum);
            }
        };

        socketIO.on('warning', function(data) {
            var info = JSON.parse(data.data);
            var time = new Date(info.timestamp * 1000);
            self.highlightDevice(info.server, info.node.id, info.sensor_id, info.raw_value);
            self.addWarningItem(time, info.server + '\\' + info.node.id, info.sensor_id, info.sensor_type, '警报', info.raw_value);
        });
    }]);

    app.controller('ChartCtrl', ['apiSrv', 'broadcastSrv', 'valueConvertSrv', '$interval', '$timeout', '$scope', function(apiSrv, broadcastSrv, valueConvertSrv, $interval, $timeout, self) {

        self.colorSet = ['#97BBCD'];

        self.chartOptions = {
            drawPoints: true,
            labels: ['时间', '传感器'],
            legend: 'follow',
            drawGrid: false,
            fillGraph: true,
            strokeWidth: 2.0,
            colors: self.colorSet
        };

        self.chart = null;
        self.chartDOM = null;
        self.isInitialized = false;
        self.isChartRunning = false;
        self.chartTimer = null;
        self.chartData = [[new Date(), 0]];
        self.chartInterval = 500;

        self.serverId = '';
        self.nodeId = '';
        self.sensorId = '';

        // --- Function of controller

        self.addChartPoint = function() {
            apiSrv.getSensorData(self.serverId, self.nodeId, self.sensorId, function(data) {
                // success
                // todo load some parsing module and parse the raw value
                var x = new Date(data.timestamp * 1000);
                var y = valueConvertSrv.convertWithoutFormat(data.sensor_type, data.raw_value);
                self.chartData.push([x, y]);
                if (self.chartData.length > 40) {
                    self.chartData.shift();
                }
                self.chart.updateOptions({
                    'file': self.chartData
                });
            }, function(data) {
                // fail

            });
        };

        self.initChart = function(serverId, nodeId, sensorId, timeInterval) {
            self.serverId = serverId;
            self.nodeId = nodeId;
            self.sensorId = sensorId;
            self.chartInterval = timeInterval;

            self.chartDOM = document.getElementById('sensor-chart');
            if (self.chart != null) {
                self.chart.destroy();
            }
            self.chartData = [[new Date(), 0]];
            self.chart = new Dygraph(self.chartDOM, self.chartData, self.chartOptions);
            self.chartOptions.labels[1] = self.sensorId;
            self.isInitialized = true;
        };

        // should 'initChart' first
        self.startChart = function() {
            if (self.isInitialized !== true) {
                return;
            }
            if (self.chartTimer != null) {
                self.stopChart();
            }
            self.chartTimer = $interval(self.addChartPoint, self.chartInterval);
            self.isChartRunning = true;
        };

        // should 'initChart' first
        self.stopChart = function() {
            if (self.isInitialized !== true) {
                return;
            }
            if (self.chartTimer != null) {
                $interval.cancel(self.chartTimer);
                self.chartTimer = null;
            }
            self.isChartRunning = false;
        };

        // should 'initChart' first
        self.clearChart = function() {
            if (self.isInitialized !== true) {
                return;
            }
            self.stopChart();
            if (self.chart != null) {
                self.chartData = [[new Date(), 0]];
                self.chart.updateOptions({
                    'file': self.chartData
                });
            }
            self.serverId = null;
            self.nodeId = null;
            self.sensorId = null;
            self.isInitialized = false;
        };

        // --- Broadcast listener
        broadcastSrv.onShowChart(function() {
            var msg = broadcastSrv.msgs[broadcastSrv.const.SHOW_CHART];
            // avoid dygraphs issue
            $timeout(function() {
                self.clearChart();
                self.initChart(msg.sId, msg.nId, msg.senId, msg.timeInterval);
                self.startChart();
            }, 500);
        });
    }]);

    app.controller('ForwarderConfigCtrl', ['apiSrv', 'broadcastSrv', '$scope', function(apiSrv, broadcastSrv, self) {
        self.currentConfig = {
            forwarder_host: '',
            forwarder_port: 0,
            forwarder_id: '',
            forwarder_desc: ''
        };

        self.newConfig = angular.copy(self.currentConfig);

        self.newConfigStr = '';

        self.isSentSuccess = false;
        self.sentSuccessMsg = '';
        self.isSentError = false;
        self.sentErrorMsg = '';

        // --- Function of controller

        // Object --> self.currentConfig
        self.setCurrentConfig = function(config) {
            if (config !== null && typeof config === 'object') {
                for (var key in self.currentConfig) {
                    if (self.currentConfig.hasOwnProperty(key)) {
                        self.currentConfig[key] = config[key];
                    }
                }
            }
        };

        // self.newConfig --> string
        self.convertNewConfig = function() {
            self.newConfig.forwarder_port = Number(self.newConfig.forwarder_port);
            self.newConfigStr = JSON.stringify(self.newConfig);
            return JSON.stringify(self.newConfig);
        };

        self.loadConfig = function() {
            apiSrv.getForwarderConfig(function(data) {
                // success
                self.setCurrentConfig(data);
            }, function(data) {
                // error

            });
        };

        self.sendConfig = function() {
            apiSrv.setForwarderConfig(self.convertNewConfig(), function(data) {
                self.isSentSuccess = true;
                self.sentSuccessMsg = data;
                self.setCurrentConfig(data);
                broadcastSrv.sayRefreshTree();
            }, function(data) {
                self.isSentError = true;
                self.sentErrorMsg = data;
                broadcastSrv.sayRefreshTree();
            });
        };

        self.clearSuccessStat = function() {
            self.isSentSuccess = false;
        };

        self.clearErrorStat = function() {
            self.isSentError = false;
        };

        // --- Listener of broadcast

        broadcastSrv.onShowConfig(function() {
            var msg = broadcastSrv.msgs[broadcastSrv.const.SHOW_CONFIG];
            if (msg.deviceType !== broadcastSrv.const.DEVICE_FORWARDER) {
                return;
            }
            self.loadConfig();
        });
    }]);

    app.controller('ServerConfigCtrl', ['apiSrv', 'broadcastSrv', '$scope', function(apiSrv, broadcastSrv, self) {
        self.currentConfig = {
            server_host: '',
            server_port: 0,
            server_id: '',
            server_desc: '',
            forwarder_addr: '',
            forwarder_port: 0
        };

        self.newConfig = angular.copy(self.currentConfig);

        self.newConfigStr = '';

        self.serverId = '';

        self.isSentSuccess = false;
        self.sentSuccessMsg = '';
        self.isSentError = false;
        self.sentErrorMsg = '';

        // --- Function of controller

        self.setCurrentConfig = function(config, sId) {
            if (config !== null && typeof config === 'object') {
                for (var key in self.currentConfig) {
                    if (self.currentConfig.hasOwnProperty(key)) {
                        self.currentConfig[key] = config[key];
                    }
                }
                self.serverId = sId;
            }
        };

        // self.newconfig --> string
        self.convertNewConfig = function() {
            self.newConfig.server_port = Number(self.newConfig.server_port);
            self.newConfig.forwarder_port = Number(self.newConfig.forwarder_port);
            self.newConfigStr = JSON.stringify(self.newConfig);
            return JSON.stringify(self.newConfig);
        };

        // sId is server_id.
        self.loadConfig = function(sId) {
            apiSrv.getServerConfig(sId, function(data) {
                // success
                self.setCurrentConfig(data, sId);
            }, function(data) {
                // error

            });
        };

        self.sendConfig = function() {
            apiSrv.setServerConfig(self.convertNewConfig(), self.serverId, function(data) {
                self.isSentSuccess = true;
                self.sentSuccessMsg = data;
                self.setCurrentConfig(data);
                broadcastSrv.sayRefreshTree();
            }, function(data) {
                self.isSentError = true;
                self.sentErrorMsg = data;
                broadcastSrv.sayRefreshTree();
            });
        };

        self.clearSuccessStat = function() {
            self.isSentSuccess = false;
        };

        self.clearErrorStat = function() {
            self.isSentError = false;
        };

        // --- Listener of broadcast

        broadcastSrv.onShowConfig(function() {
            var msg = broadcastSrv.msgs[broadcastSrv.const.SHOW_CONFIG];
            if (msg.deviceType !== broadcastSrv.const.DEVICE_SERVER) {
                return;
            }
            self.loadConfig(msg.sId);
        });
    }]);

    app.controller('NodeConfigCtrl', ['apiSrv', 'broadcastSrv', '$scope', function(apiSrv, broadcastSrv, self) {
        self.emptySensor = {
            sensor_type: '',
            sensor_id: '',
            sensor_desc: '',
            sensor_config: {},
            sensor_interval: 2.0,
            sensors: [],
            filters: []
        };

        self.emptyFilter = {
            apply_on_sensor_type: '',
            apply_on_sensor_id: '',
            comparing_method: '',
            threshold: 0
        };

        self.currentConfig = {
            node_host: '',
            node_port: 0,
            node_id: '',
            node_desc: '',
            server_addr: '',
            server_port: '',
            sensors: [],
            filters: []
        };

        self.newConfig = angular.copy(self.currentConfig);

        self.newConfigStr = '';

        self.serverId = '';
        self.nodeId = '';

        self.isSentSuccess = false;
        self.sentSuccessMsg = '';
        self.isSentError = false;
        self.sentErrorMsg = '';

        // --- Function of controller

        self.setCurrentConfig = function(config, sId, nId) {
            if (config !== null && typeof config === 'object') {
                for (var key in self.currentConfig) {
                    if (self.currentConfig.hasOwnProperty(key)) {
                        self.currentConfig[key] = config[key];
                    }
                }
                self.serverId = sId;
                self.nodeId = nId;
            }
        };

        // self.newconfig --> string
        self.convertNewConfig = function() {
            self.newConfig.server_port = Number(self.newConfig.server_port);
            self.newConfig.node_port = Number(self.newConfig.node_port);
            self.newConfigStr = JSON.stringify(self.newConfig);
            return JSON.stringify(self.newConfig);
        };

        // sId is server_id, nId is node_id.
        self.loadConfig = function(sId, nId) {
            apiSrv.getNodeConfig(sId, nId, function(data) {
                // success
                self.setCurrentConfig(data, sId, nId)
            }, function(data) {
                // error

            });
        };

        self.sendConfig = function() {
            apiSrv.setServerConfig(self.convertNewConfig(), self.serverId, function(data) {
                self.isSentSuccess = true;
                self.sentSuccessMsg = data;
                self.setCurrentConfig(data);
                broadcastSrv.sayRefreshTree();
            }, function(data) {
                self.isSentError = true;
                self.sentErrorMsg = data;
                broadcastSrv.sayRefreshTree();
            });
        };

        self.clearSuccessStat = function() {
            self.isSentSuccess = false;
        };

        self.clearErrorStar = function() {
            self.isSentError = false;
        };

        self.addSensorFieldToNewConfig = function() {
            self.newConfig.sensors.push(angular.copy(self.emptySensor));
        };

        self.addFilterFieldToNewConfig = function() {
            self.newConfig.filters.push(angular.copy(self.emptyFilter));
        };

        // --- Listener of broadcast

        broadcastSrv.onShowConfig(function() {
            var msg = broadcastSrv.msgs[broadcastSrv.const.SHOW_CONFIG];
            if (msg.deviceType !== broadcastSrv.const.DEVICE_NODE) {
                return;
            }
            self.loadConfig(msg.sId, msg.nId);
        });

    }]);
})();