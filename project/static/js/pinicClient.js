/**
 * Created by tgmerge on 5/9.
 */

'use strict';


(function() {

    // AngularJS Rocks!

    // AngularJS应用
    var app = angular.module('pinicClient', []);

    // AngularJS模板指令：设备页
    app.directive('devicesTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/devices-tab.html'
        };
    });

    // AngularJS模板指令：设备页-Server详情区域
    app.directive('devicesTabServerDetailSection', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/devices-tab-server-detail-section.html'
        };
    });

    // AngularJS模板指令：设备页-Server树形图区域
    app.directive('devicesTabServerTreeSection', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/devices-tab-server-tree-section.html'
        };
    });

    // AngularJS模板指令：设备页-报警记录区域
    app.directive('devicesTabWarningSection', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/devices-tab-warning-section.html'
        };
    });

    // AngularJS模板指令：图表监控页
    app.directive('chartTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/chart-tab.html'
        };
    });

    // AngularJS模板指令：Forwarder配置页
    app.directive('forwarderConfigTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/forwarder-config-tab.html'
        };
    });

    // AngularJS模板指令：Server配置页
    app.directive('serverConfigTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/server-config-tab.html'
        };
    });

    // AngularJS模板指令：Node配置页
    app.directive('nodeConfigTab', function() {
        return {
            restrict: 'EA',
            templateUrl: 'html/node-config-tab.html'
        };
    });

    // AngularJS控制器：分页控制
    app.controller('tabController', ['tabSrv', '$scope', function(tabSrv, self) {

        /**
         * 控制器方法：检查当前标签页是否为指定页
         * @param checkTab 要检查的页号
         */
        self.tabIsSet = function(checkTab) {
            return tabSrv.tabIsSet(checkTab);
        };

        /**
         * 控制器方法：设置当前标签页为制定页
         * @param activeTab 要设置的页号
         */
        self.setTab = function(activeTab) {
            tabSrv.setTab(activeTab);
        };
    }]);

    // AngularJS服务：传感器值格式转换（raw value -> formatted value）
    app.service('valueConvertSrv', function() {
        var srv = {};

        /**
         * 不同类型传感器的转换函数。函数需要返回[convertedValue, unitString]。
         */
        srv.convertFunctions = {
            'tlc1549': function(value) {
                // u/v = r/(250+r), v is 5V DC, u is detected voltage
                // ->
                // raw/1024 = r/(250+r)
                // ->
                // r = 250raw/(1024-raw)
                var raw = Number(value);
                var r = ((250.0 * raw) / (1024.01 - raw)).toFixed(2);
                return [r, 'Ω'];
            },
            'stub': function(value) {
                return [value, '次'];
            },
            'random': function(value) {
                return [Math.ceil(value), ''];
            }
        };

        /**
         * 服务方法：转换一个无格式的传感器值为有格式的字符串。
         * @param type 传感器类型（String）
         * @param raw_value 要转换的传感器值
         * @returns String 转换后带格式的传感器值描述字符串。
         */
        srv.convert = function(type, raw_value) {
            if (type in srv.convertFunctions) {
                return srv.convertFunctions[type](raw_value).join('');
            } else {
                return raw_value;
            }
        };

        /**
         * 服务方法：转换一个传感器值，但仅计算转换函数，不附加格式字符串。
         * @param type 传感器类型（String）
         * @param raw_value 要转换的传感器值
         * @returns Number 转换后的传感器值
         */
        srv.convertWithoutFormat = function(type, raw_value) {
            if (type in srv.convertFunctions) {
                return srv.convertFunctions[type](raw_value)[0];
            } else {
                return raw_value;
            }
        };

        // 设置为AngularJS服务
        return srv;
    });

    /**
     *  AngularJS服务：标签页控制
     **/
    app.service('tabSrv', function() {
        var srv = {};

        srv.tab = 1;

        /**
         * 服务方法：检查当前标签页是否是指定页
         * @param checkTab 要检查的标签页号
         * @returns {boolean}
         */
        srv.tabIsSet = function(checkTab) {
            return srv.tab === checkTab;
        };

        /**
         * 服务方法：设置当前标签页为指定页
         * @param activeTab 要设置的标签页号
         */
        srv.setTab = function(activeTab) {
            srv.tab = activeTab;
        };

        // 设置为AngularJS服务
        return srv;
    });

    /**
     * AngularJS服务：API服务
     * **/
    app.service('apiSrv', ['$http', function($http) {
        var srv = {};

        /**
         * 服务方法：获取Forwarder配置
         * @param succ 成功后的回调函数，以下同
         * @param fail 失败后的回调函数，以下同
         */
        srv.getForwarderConfig = function(succ, fail) {
            $http.get('/forwarder/forwarderconfig').success(succ).error(fail);
        };

        /**
         * 服务方法：获取Server的配置
         * @param sId 要获取的Server的ID
         * @param succ
         * @param fail
         */
        srv.getServerConfig = function(sId, succ, fail) {
            $http.get('/server/serverconfig/' + sId).success(succ).error(fail);
        };

        /**
         * 服务方法：获取Node的配置
         * @param sId 要获取的Node上级Server的ID
         * @param nId 要获取的Node的ID
         * @param succ
         * @param fail
         */
        srv.getNodeConfig = function(sId, nId, succ, fail) {
            $http.get('/server/nodeconfig/' + sId + '/' + nId).success(succ).error(fail);
        };

        /**
         * 服务方法：更新（更改）Forwarder的配置
         * @param configJson 新的配置的Json字符串
         * @param succ
         * @param fail
         */
        srv.setForwarderConfig = function(configJson, succ, fail) {
            $http.post('/forwarder/forwarderconfig', configJson).success(succ).error(fail);
        };

        /**
         * 服务方法：更新Server的配置
         * @param configJson 新的配置的Json字符串
         * @param sId 要更新的Server的ID
         * @param succ
         * @param fail
         */
        srv.setServerConfig = function(configJson, sId, succ, fail) {
            $http.post('/server/serverconfig/' + sId, configJson).success(succ).error(fail);
        };

        /**
         * 服务方法：更新Node的配置
         * @param configJson 新的配置的Json字符串
         * @param sId 要更新的Node的上级Server的ID
         * @param nId 要更新的Node的ID
         * @param succ
         * @param fail
         */
        srv.setNodeConfig = function(configJson, sId, nId, succ, fail) {
            $http.post('/server/nodeconfig/' + sId + '/' + nId, configJson).success(succ).error(fail);
        };

        /**
         * 服务方法：获取传感器值
         * @param sId 要获取的传感器所连接的Node的上级Server的ID
         * @param nId 传感器所连接Node的ID
         * @param senId 传感器的ID
         * @param succ
         * @param fail
         */
        srv.getSensorData = function(sId, nId, senId, succ, fail) {
            $http.get('/server/sensordata/' + sId + '/' + nId + '/' + senId).success(succ).error(fail);
        };

        /**
         * 服务方法：获取Server的已知Node列表
         * @param sId 要获取的Server的ID
         * @param succ
         * @param fail
         */
        srv.getKnownNodesOfServer = function(sId, succ, fail) {
            $http.get('/server/knownnodes/' + sId).success(succ).error(fail);
        };

        /**
         * 服务方法：获取Forwarder的已知Server列表
         * @param succ
         * @param fail
         */
        srv.getKnownServersOfForwarder = function(succ, fail) {
            $http.get('/forwarder/knownservers').success(succ).error(fail);
        };

        // 设置AngularJS服务
        return srv;
    }]);

    /**
     * AngularJS服务：设备信息管理
     * 该服务通过API的相关方法，在网页客户端内部维护一个存放所有设备信息的树形对象。
     */
    app.service('devicesSrv', ['apiSrv', 'valueConvertSrv', 'broadcastSrv', function(apiSrv, valueConvertSrv, broadcastSrv) {
        var srv = {};

        // 设备类型常量
        srv.const = {
            TYPE_FORWARDER: 'FORWARDER',
            TYPE_SERVER: 'SERVER',
            TYPE_NODE: 'NODE',
            TYPE_SENSOR: 'SENSOR'
        };

        // 空的Sensor对象，用于表示Sensor信息，下同
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

        // 空的Node对象
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

        // 空的Server对象
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

        // 空的Forwarder对象
        srv.newForwarder = function() {
            return {
                deviceType: srv.const.TYPE_FORWARDER,
                config: {
                    id: '',
                    addr: '',
                    port: '',
                    desc: ''
                },
                servers: [],

                // 存放通过Server的server_desc位置信息建立起的Server树状结构
                serverTree: [] // UGLY HACK 233, after known servers is fetched,
                               // a TREE will be built using servers' "Description" string(as path).
            }
        };

        /**
         * 向一个Node对象（见上）的sensor列表添加一个新的Sensor
         * @param sensor 要添加的Sensor对象（见上）
         * @param node 要添加到的Node对象
         */
        srv.addSensorToNode = function(sensor, node) {
            node.sensors.push(sensor);
        };

        /**
         * 向一个Server对象（见上）的node列表添加一个新的Node
         * @param node 要添加的Node对象
         * @param server 要添加到的Server对象
         */
        srv.addNodeToServer = function(node, server) {
            server.nodes.push(node);
        };

        /**
         * 向一个Forwarder对象的Server列表添加一个新的Server
         * @param server 要添加的Server对象
         * @param forwarder 要添加到的Forwarder对象
         */
        srv.addServerToForwarder = function(server, forwarder) {
            forwarder.servers.push(server);
        };

        /**
         * 通过API刷新一个Sensor（传感器）的资料，从API获取它的值。
         * 将使用valueConvertSrv服务将传感器的无格式值转换为有格式的字符串。
         * @param server 传感器连接的Node从属的Server对象
         * @param node 传感器连接的Node对象
         * @param sensor 传感器对象
         */
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

        /**
         * 通过API刷新一个Node和它的所有下级设备的资料
         * @param server 目标Node对象从属的Server对象
         * @param node 目标Node对象
         */
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

        /**
         * 通过API刷新一个Server和它的所有下级设备的资料
         * @param server 目标Server
         */
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
                broadcastSrv.sayServerConnect();
            }, function(data) {
                // error
                broadcastSrv.sayServerDisconnect();
            });
        };

        /**
         * 通过Server的server_desc位置描述字符串和server_id，建立起Server的树形结构。
         * @param paths 含有所有server_desc+server_id的数组。
         * @returns {Array} 树形结构表示的Server信息。可能为森林。
         */
        var structurize = function(paths) {
            var items = [];
            for(var i = 0, l = paths.length; i < l; i++) {
                var path = paths[i];
                var name = path[0];
                var rest = path.slice(1);
                var item = null;
                for(var j = 0, m = items.length; j < m; j++) {
                    if(items[j].name === name) {
                        item = items[j];
                        break;
                    }
                }
                if(item === null) {
                    item = {name: name, children: []};
                    items.push(item);
                }
                if(rest.length > 0) {
                    item.children.push(rest);
                }
            }
            for(i = 0, l = items.length; i < l; i++) {
                item = items[i];
                item.children = structurize(item.children);
            }
            return items;
        };

        /**
         * 将Forwarder对象的Server，拼接server_desc和server_id，建立树形结构。
         * @param forwarder 要处理的Forwarder对象
         */
        srv.buildServerTree = function(forwarder) {
            var paths = [];
            for (var i = 0; i < forwarder.servers.length; i ++){
                var server = forwarder.servers[i];
                paths.push((server.config.desc + '/' + server.config.id).split('/'));
            }
            forwarder.serverTree = structurize(paths);
        };

        /**
         * 通过API刷新一个Forwarder和它所有下级设备的资料
         * @param forwarder 要刷新的Forwarder
         */
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
                // Now we have all known servers(although update process of which is still running).
                // Let's build a tree using servers' "description" string,
                // And store that tree into forwarder.serverTree prop!
                srv.buildServerTree(forwarder);
                ddtreemenu.createTree('server-tree', true, 5);
            }, function(data) {
                // error

            });
        };

        /**
         * 供其他Controller调用的、本服务的主要方法。
         * 传入一个对象（obj），本方法将获取整个系统的所有设备信息，作为Forwarder对象，存放在对象的"forwarder"属性中。
         * @param obj 传入的对象。
         */
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

        // 配置AngularJS服务对象
        return srv;
    }]);

    /**
     * AngularJS服务：广播服务
     * 提供多种类型的事件广播的发送和监听方法。
     * 监听方可以在broadcastSrv.msgs[EVENT_TYPE]中获取到事件的附加数据。
     * 如，JUMP_PAGE的附加数据，在broadcastSrv.msgs[broadcastSrv.const[JUMP_PAGE]中。
     */
    app.service('broadcastSrv', ['$rootScope', function($rootScope) {
        var srv = {};

        // 存放事件的附加数据
        srv.msgs = {};

        // 常量和事件类型
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
            REFRESH_TREE: 'REFRESH_TREE',

            FORWARDER_CONNECT: 'FORWARDER_CONNECT',
            FORWARDER_DISCONNECT: 'FORWARDER_DISCONNECT',
            SERVER_CONNECT: 'FORWARDER_CONNECT',
            SERVER_DISCONNECT: 'FORWARDER_DISCONNECT',

            CANCEL_WARNING: 'CANCEL_WARNING'
        };

        /**
         * 发送FORWARDER_CONNECT广播
         * 指示Forwarder已经正常连接
         */
        srv.sayForwarderConnect = function() {
            $rootScope.$broadcast(srv.const.FORWARDER_CONNECT);
        };

        /**
         * 监听FORWARDER_CONNECT广播
         * @param callback 收到广播后的回调函数，下同
         */
        srv.onForwarderConnect = function(callback) {
            $rootScope.$on(srv.const.FORWARDER_CONNECT, callback);
        };

        /**
         * 发送FORWARDER_DISCONNECT广播
         * 指示Forwarder已经断开连接（网络异常等）
         */
        srv.sayForwarderDisconnect = function() {
            $rootScope.$broadcast(srv.const.FORWARDER_DISCONNECT);
        };

        srv.onForwarderDisconnect = function(callback) {
            $rootScope.$on(srv.const.FORWARDER_DISCONNECT, callback);
        };

        /**
         * 发送SERVER_CONNECT广播
         * 指示Server已经正常更新，状态正常
         */
        srv.sayServerConnect = function() {
            $rootScope.$broadcast(srv.const.SERVER_CONNECT);
        };

        srv.onServerConnect = function(callback) {
            $rootScope.$on(srv.const.SERVER_CONNECT, callback);
        };

        /**
         * 发送SERVER_DISCONNECT广播
         * 指示Server更新或状态异常，无法连接
         */
        srv.sayServerDisconnect = function() {
            $rootScope.$broadcast(srv.const.SERVER_DISCONNECT);
        };

        srv.onServerDisconnect = function(callback) {
            $rootScope.$on(srv.const.SERVER_DISCONNECT, callback);
        };

        /**
         * 发送CANCEL_WARNING广播
         * 指示要求取消警报。
         */
        srv.sayCancelWarning = function() {
            $rootScope.$broadcast(srv.const.CANCEL_WARNING);
        };

        srv.onCancelWarning = function(callback) {
            $rootScope.$on(srv.const.CANCEL_WARNING, callback);
        };

        /**
         * 发送JUMP_PAGE广播
         * 指示要求页面跳转
         * @param toPageNo 要跳转到的页面
         */
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

        /**
         * 发送SHOW_SUBTREE广播
         * 要求在Server详情区域显示一个Server的详情（下属Node、Sensor等）
         * @param server 要显示详情的Server对象
         */
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

        /**
         * 发送SHOW_CONFIG广播
         * 要求显示一个设备的配置页面
         * @param deviceType 设备信息，可以是broadcastSrv.const中的几种
         * @param fId Forwarder ID，可选
         * @param sId Server ID，可选。如果设备类型是Forwarder则不需要设置。
         * @param nId Node ID，可选。如果设备类型是Forwarder或Server则不需要设置。
         * @param senId Sensor ID，可选。如果设备类型是Forwarder、Server或Node则不需要设置。
         */
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

        /**
         * 发送SHOW_CHART广播
         * 要求在曲线监控区域显示传感器的监控曲线
         * @param sId 传感器相连的Node从属的Server ID
         * @param nId 传感器相连的Node的ID
         * @param senId 传感器的Sensor ID
         * @param timeInterval 毫秒数，曲线刷新间隔
         */
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

        /**
         * 发送SHOW_WARNING广播
         * 要求高亮警报一个传感器值。
         * @param deviceType 高亮的设备类型
         * @param fId Forwarder ID，可选
         * @param sId Server ID，可选
         * @param nId Node ID，可选
         * @param senId Sensor ID，可选
         * @param value 报警的传感器值。
         */
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

        /**
         * 发送REFRESH_TREE广播
         * 要求刷新整个系统的所有设备信息。
         */
        srv.sayRefreshTree = function() {
            srv.msgs[srv.const.REFRESH_TREE] = {};
            $rootScope.$broadcast(srv.const.REFRESH_TREE);
        };

        srv.onRefreshTree = function(callback) {
            $rootScope.$on(srv.const.REFRESH_TREE, callback);
        };

        // 配置AngularJS对象
        return srv;
    }]);

    // AngularJS服务：SocketIO服务
    // 封装SocketIO的几个接口，供AngularJS的Controller调用
    app.service('socketIO', ['$rootScope', 'broadcastSrv', function($rootScope, broadcastSrv) {
        var socket = io.connect('/warning');

        // 在SocketIO连接成功时发送“Forwarder成功连接”的广播
        socket.on('connect', function() {
            broadcastSrv.sayForwarderConnect();
        });

        // 在SoceketIO连接断开时发送“Forwarder断开连接”的广播
        socket.on('disconnect', function() {
            broadcastSrv.sayForwarderDisconnect();
        });

        return {
            /**
             * 服务方法：设置SocketIO时间的回调函数
             * @param eventName 事件名
             * @param callback 回调函数
             */
            on: function(eventName, callback) {
                socket.on(eventName, function() {
                    var args = arguments;
                    $rootScope.$apply(function() {
                        callback.apply(socket, args);
                    });
                });
            },

            /**
             * 服务方法：向SocketIO的Socket发送数据
             * @param eventName 事件名
             * @param data 数据
             * @param callback 发送成功后的回调函数
             */
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
    }]);

    /**
     * AngularJS控制器：Server树形图控制器
     * 维护页面中的Server树形图部分，即指令devicesTabServerTreeSection的部分。
     */
    app.controller('DeviceTreeCtrl', ['tabSrv', 'devicesSrv', 'broadcastSrv', '$interval', '$scope', function(tabSrv, devicesSrv, broadcastSrv, $interval, self) {

        // 要交给devicesSrv服务的对象，存放系统设备数据
        self.deviceData = {};

        // Forwarder的目标主机名，从window.location获取
        self.hostName = window.location.hostname;

        // 自动刷新系统设备的定时器
        self.refreshTimer = null;

        // --- 控制器方法：

        /**
         * 辅助方法，传入一个对象，生成它的Hash值
         * 用于在HTML中为每个Server的<input>和<label>生成唯一的id和for属性
         * @param obj 要Hash的对象
         * @returns {number} 得到的唯一Hash值
         */
        self.objHashKey = function(obj) {
            var str = JSON.stringify(obj);
            var hash = 0;
            if (str.length == 0) return hash;
            for (var i = 0; i < str.length; i++) {
                var character = str.charCodeAt(i);
                hash = ((hash<<5)-hash)+character;
                hash = hash & hash; // Convert to 32bit integer
            }
            return hash;
        };

        /**
         * 刷新deviceData中的系统设备数据。
         */
        self.refreshTree = function() {
            devicesSrv.updateDevices(self.deviceData);
        };

        self.lastShownServerId = '';

        /**
         * 在树形图右边的Server详情区域(devicesTabServerDetailSection指令)显示一个Server的详情
         * @param server 要显示的Server对象
         */
        self.showServerInDeviceList = function(server) {
            self.lastShownServerId = server.config.id;
            broadcastSrv.sayShowSubtree(server);
        };

        /**
         * 和showServerInDeviceList类似，但用server id而不是server对象来指定Server。
         * @param serverId 要显示的Server的ID
         */
        self.showServerInDeviceListById = function(serverId) {
            for (var i in self.deviceData.forwarder.servers) {
                var server = self.deviceData.forwarder.servers[i];
                if (serverId === server.config.id) {
                    self.showServerInDeviceList(server);
                    break;
                }
            }
        };

        /**
         * 刷新Server详情区域的Server详情。
         */
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

        /**
         * 点击“显示Forwarder配置”后，跳转到Forwarder的配置页面
         */
        self.showForwarderConfig = function() {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_FORWARDER);
            tabSrv.setTab(3);
        };

        /**
         * 点击“显示Server配置”后，跳转到相应Server的配置页面
         * @param sId 要配置的Server的ID
         */
        self.showServerConfig = function(sId) {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_SERVER, null, sId);
            tabSrv.setTab(4);
        };

        // --- 监听的广播

        /**
         * 监听REFRESH_TREE广播，收到该广播后刷新系统设备数据。
         */
        broadcastSrv.onRefreshTree(function() {
            self.refreshTree();
        });

        // --- 控制器初始化

        // 刷新一下系统设备的数据
        self.refreshTree();

        // 定期刷新系统设备数据（15秒）
        self.refreshTimer = $interval(function() {
            self.refreshServerInDeviceList();
            self.refreshTree();
        }, 15000);
    }]);

    /**
     * AngularJS控制器：Server详情控制器
     * 维护页面中的Server详情部分，即指令devicesTabServerDetailSection的部分。
     */
    app.controller('DeviceListCtrl', ['tabSrv', 'broadcastSrv', 'valueConvertSrv', '$scope', function(tabSrv, broadcastSrv, valueConvertSrv, self) {

        // DeviceTreeCtrl中deviceData的一小部分，只有一个Server和它以下设备的信息
        self.server = {};

        // --- 控制器方法

        /**
         * 加载一个Server的详情并显示。
         * @param server 要显示的Server对象
         */
        self.loadSubTree = function(server) {
            self.server = {};
            self.server = server;
        };

        /**
         * 移除一个设备的警报高亮。
         * 警报通过设备对象的isWarning属性为true来设置。
         * @param device 要处理的设备对象。它的isWarning将被设置为false。
         */
        self.removeWarning = function(device) {
            if (device != undefined) {
                device.isWarning = false;
            }
        };

        /**
         * 移除一个设备和它之下所有设备的警报高亮。
         * @param device 要处理的设备对象。
         */
        self.removeNodeAndSubDeviceWarning = function(device) {
            if (device != undefined) {
                for (var sensor in device.sensors) {
                    device.sensors[sensor].isWarning = false;
                }
                device.isWarning = false;
            }
        };

        /**
         * 在图表标签页里显示传感器的监控曲线
         * @param sId 要监控的传感器上级的Server ID
         * @param nId 要监控的传感器上级的Node ID
         * @param senId 要监控的传感器的Sensor ID
         */
        self.toSensorChart = function(sId, nId, senId) {
            tabSrv.setTab(2);
            broadcastSrv.sayShowChart(sId, nId, senId, 500);
        };

        /**
         * 显示一个Server的配置页面
         * @param sId 要显示的Server的ID
         */
        self.showServerConfig = function(sId) {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_SERVER, null, sId);
            tabSrv.setTab(4);
        };

        /**
         * 显示一个Node的配置页面
         * @param sId 要显示的Node的上级Server ID
         * @param nId 要显示的Node的ID
         */
        self.showNodeConfig = function(sId, nId) {
            broadcastSrv.sayShowConfig(broadcastSrv.const.DEVICE_NODE, null, sId, nId);
            tabSrv.setTab(5);
        };

        // --- 事件广播监听方法

        /**
         * 监听SHOW_SUBTREE广播
         * 收到广播后载入广播附加数据的Server并显示出来
         */
        broadcastSrv.onShowSubtree(function() {
            self.loadSubTree(broadcastSrv.msgs[broadcastSrv.const.SHOW_SUBTREE].server);
        });

        /**
         * 监听SHOW_WARNING广播
         * 收到广播后，将广播附加数据中指定的设备对象的isWarning设为true，显示警报高亮
         */
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

    /**
     * AngularJS控制器：警报记录区域控制器
     * 对应AngularJS指令：devicesTabWarningSection
     */
    app.controller('WarningCtrl', ['socketIO', 'broadcastSrv', 'valueConvertSrv', '$scope', function(socketIO, broadcastSrv, valueConvertSrv, self) {

        // 当前的警告信息列表
        self.warningItems = [];

        // 警告列表最大长度
        self.maxWarningNum = 6;

        // --- 控制器方法

        /**
         * 高亮一个设备，发送SHOW_WARNING广播
         * @param sId
         * @param nId
         * @param senId
         * @param value
         */
        self.highlightDevice = function(sId, nId, senId, value) {
            broadcastSrv.sayShowWarning(null, null, sId, nId, senId, value)
        };

        /**
         * 添加一个警报到警报列表中
         * @param date 警报时间
         * @param deviceName 设备名称（路径+ID）
         * @param sensorName 传感器名称
         * @param sensorType 传感器类型
         * @param infoType 消息类型（默认为“警报”）
         * @param value 警报值
         */
        self.addWarningItem = function(date, deviceName, sensorName, sensorType, infoType, value) {
            var warningItem = {
                timeString: date.toString().split(' ')[4],
                deviceName: deviceName,
                sensorName: sensorName,
                sensorType: sensorType,
                infoType: infoType,
                value: valueConvertSrv.convert(sensorType, value)
            };

            // 添加到warningItems列表
            self.warningItems.unshift(warningItem);

            // 如果添加后超过maxWarningNum长度，则清除最旧的
            if (self.warningItems.length > self.maxWarningNum) {
                self.warningItems.splice(self.maxWarningNum, self.warningItems.length-self.maxWarningNum);
            }
        };

        /**
         * 监听SocketIO的警报事件，收到警报后高亮设备并添加到警报列表中显示
         */
        socketIO.on('warning', function(data) {
            var info = JSON.parse(data.data);
            var time = new Date(info.timestamp * 1000);
            self.highlightDevice(info.server, info.node.id, info.sensor_id, info.raw_value);
            self.addWarningItem(time, info.server + '/' + info.node.id, info.sensor_id, info.sensor_type, '警报', info.raw_value);
        });
    }]);

    /**
     * AngularJS控制器：图表控制器
     * 对应AngularJS指令：chartTab
     */
    app.controller('ChartCtrl', ['apiSrv', 'broadcastSrv', 'valueConvertSrv', '$interval', '$timeout', '$scope', function(apiSrv, broadcastSrv, valueConvertSrv, $interval, $timeout, self) {

        // 图线颜色
        self.colorSet = ['#97BBCD'];

        // 图表设置
        self.chartOptions = {
            drawPoints: true,
            labels: ['时间', '传感器'],
            legend: 'follow',
            drawGrid: false,
            fillGraph: true,
            strokeWidth: 2.0,
            colors: self.colorSet
        };

        self.chart = null;  // 图表对象（DyGraph）
        self.chartDOM = null;  // 要绘图的DOM元素
        self.isInitialized = false;  // 图表是否已经初始化
        self.isChartRunning = false;  // 图表是否正在动态更新
        self.chartTimer = null;  // 图表更新计时器
        self.chartData = [[new Date(), 0]];  // 图表的数据列表
        self.chartInterval = 500;  // 图表更新间隔

        self.serverId = '';  // 正在绘制的传感器的Server的ID
        self.nodeId = '';  // 正在绘制的传感器的Node的ID
        self.sensorId = '';  // 正在绘制的传感器的Sensor ID

        // --- 控制器方法

        /**
         * 从传感器获取一个数据点到图表并绘制。
         */
        self.addChartPoint = function() {
            apiSrv.getSensorData(self.serverId, self.nodeId, self.sensorId, function(data) {
                // success

                // 使用valueConvertSrv转换直接值到有格式的值
                var x = new Date(data.timestamp * 1000);
                var y = valueConvertSrv.convertWithoutFormat(data.sensor_type, data.raw_value);

                // 添加数据到chartData数组
                self.chartData.push([x, y]);
                if (self.chartData.length > 40) {
                    self.chartData.shift();
                }

                // 重绘DyGraph图表
                self.chart.updateOptions({
                    'file': self.chartData
                });
            }, function(data) {
                // fail

            });
        };

        /**
         * 初始化DyGraph图表。
         * @param serverId 要绘图的传感器所属的Server的ID
         * @param nodeId 要绘图的传感器所属的Node的ID
         * @param sensorId 要绘图的传感器的Sensor ID
         * @param timeInterval 绘图时间间隔，以毫秒计
         */
        self.initChart = function(serverId, nodeId, sensorId, timeInterval) {

            // 设置Controller的各个成员变量
            self.serverId = serverId;
            self.nodeId = nodeId;
            self.sensorId = sensorId;
            self.chartInterval = timeInterval;

            // 初始化DyGraph
            self.chartDOM = document.getElementById('sensor-chart');
            if (self.chart != null) {
                self.chart.destroy();
            }
            self.chartData = [[new Date(), 0]];
            self.chart = new Dygraph(self.chartDOM, self.chartData, self.chartOptions);

            // 设置坐标轴文本为Sensor ID
            self.chartOptions.labels[1] = self.sensorId;
            self.isInitialized = true;
        };

        /**
         * 开始绘图，需要先初始化图表（initChart）。
         */
        self.startChart = function() {
            if (self.isInitialized !== true) {
                return;
            }
            if (self.chartTimer != null) {
                self.stopChart();
            }

            // 设置刷新图表的计时器
            self.chartTimer = $interval(self.addChartPoint, self.chartInterval);
            self.isChartRunning = true;
        };

        /**
         * 停止绘图，需要先初始化图表(initChart)。
         */
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

        /**
         * 清除现有的数据和图像，需要先初始化图表(initChart)。
         */
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

        // --- 广播监听方法

        /**
         * 监听到SHOW_CHART广播后，开始绘制广播附加数据中指定的传感器的曲线
         */
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

    // AngularJS控制器：Forwarder配置控制器
    // 对应AngularJS模板指令：forwarderConfigTab
    app.controller('ForwarderConfigCtrl', ['apiSrv', 'broadcastSrv', '$scope', function(apiSrv, broadcastSrv, self) {

        // 当前配置
        self.currentConfig = {
            forwarder_host: '',
            forwarder_port: 0,
            forwarder_id: '',
            forwarder_desc: ''
        };

        // 新配置，最初复制一下“当前配置”即可
        self.newConfig = angular.copy(self.currentConfig);

        // 新配置转换为Json以后的字符串，调试用
        self.newConfigStr = '';

        // 配置是否已经成功发送
        self.isSentSuccess = false;

        // 成功发送后的Forwarder响应内容
        self.sentSuccessMsg = '';

        // 配置是否发送失败
        self.isSentError = false;

        // 发送失败后的Forwarder响应
        self.sentErrorMsg = '';

        // --- 控制器方法

        /**
         * 将ForwarderConfig（Object，从JSON解析而来）存储在控制器的currentConfig中。
         * @param config 从JSON解析而来的Object，是ForwarderConfig，即Forwarder的配置。
         */
        self.setCurrentConfig = function(config) {
            if (config !== null && typeof config === 'object') {
                for (var key in self.currentConfig) {
                    if (self.currentConfig.hasOwnProperty(key)) {
                        self.currentConfig[key] = config[key];
                    }
                }
                self.newConfig = angular.copy(self.currentConfig);
            }
        };

        /**
         * 将控制器的newConfig转换为JSON字符串，以供发送HTTP请求，修改Forwarder的配置。
         * 返回一个字符串。
         */
        self.convertNewConfig = function() {
            self.newConfig.forwarder_port = Number(self.newConfig.forwarder_port);
            self.newConfigStr = JSON.stringify(self.newConfig);
            return JSON.stringify(self.newConfig);
        };

        /**
         * 从Forwarder提供的API获取Forwarder的配置，并使用setCurrentConfig存储在控制器中，以便显示
         */
        self.loadConfig = function() {
            apiSrv.getForwarderConfig(function(data) {
                // success
                self.setCurrentConfig(data);
            }, function(data) {
                // error

            });
        };

        /**
         * 通过API发送新的Forwarder配置。
         * 配置成功后，刷新本页面中的配置信息。
         */
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

        // 清除“已成功配置”的标志，暂时没有作用。
        self.clearSuccessStat = function() {
            self.isSentSuccess = false;
        };

        // 清除“配置错误”的标志，暂时没有作用。
        self.clearErrorStat = function() {
            self.isSentError = false;
        };

        // --- 广播监听方法

        /**
         * 监听SHOW_CONFIG广播，如果设备是Forwarder则处理这个广播，显示配置页面。
         */
        broadcastSrv.onShowConfig(function() {
            var msg = broadcastSrv.msgs[broadcastSrv.const.SHOW_CONFIG];
            if (msg.deviceType !== broadcastSrv.const.DEVICE_FORWARDER) {
                return;
            }
            self.loadConfig();
        });
    }]);

    // AngularJS控制器：Server配置控制器
    // 对应的AngularJS模板指令：serverConfigTab
    app.controller('ServerConfigCtrl', ['apiSrv', 'broadcastSrv', '$scope', function(apiSrv, broadcastSrv, self) {

        // 当前配置
        self.currentConfig = {
            server_host: '',
            server_port: 0,
            server_id: '',
            server_desc: '',
            forwarder_addr: '',
            forwarder_port: 0
        };

        // 新配置，最初复制一下“当前配置”即可
        self.newConfig = angular.copy(self.currentConfig);

        // 新配置转换为Json以后的字符串，调试用
        self.newConfigStr = '';

        // 当前设置中的Server的ID
        self.serverId = '';

        // 配置是否已经成功发送
        self.isSentSuccess = false;

        // 成功发送后的Forwarder响应内容
        self.sentSuccessMsg = '';

        // 配置是否发送失败
        self.isSentError = false;

        // 发送失败后的Forwarder响应
        self.sentErrorMsg = '';

        // --- 控制器方法

        /**
         * 将ServerConfig（Object，从JSON解析而来）存储在控制器的currentConfig中。
         * @param config 从JSON解析而来的Object，是ServerConfig，即Server的配置。
         */
        self.setCurrentConfig = function(config, sId) {
            if (config !== null && typeof config === 'object') {
                for (var key in self.currentConfig) {
                    if (self.currentConfig.hasOwnProperty(key)) {
                        self.currentConfig[key] = config[key];
                    }
                }
                self.serverId = sId;
                self.newConfig = angular.copy(self.currentConfig);
            }
        };

        /**
         * 将控制器的newConfig转换为JSON字符串，以供发送HTTP请求，修改Server的配置。
         * 返回一个字符串。
         */
        self.convertNewConfig = function() {
            self.newConfig.server_port = Number(self.newConfig.server_port);
            self.newConfig.forwarder_port = Number(self.newConfig.forwarder_port);
            self.newConfigStr = JSON.stringify(self.newConfig);
            return JSON.stringify(self.newConfig);
        };

        /**
         * 从Forwarder提供的API获取Server的配置，并使用setCurrentConfig存储在控制器中，以便显示
         * @param sId 目标Server的ID
         */
        self.loadConfig = function(sId) {
            apiSrv.getServerConfig(sId, function(data) {
                // success
                self.setCurrentConfig(data, sId);
            }, function(data) {
                // error

            });
        };

        /**
         * 通过API发送新的Server配置。
         * 配置成功后，刷新本页面中的配置信息。
         */
        self.sendConfig = function() {
            apiSrv.setServerConfig(self.convertNewConfig(), self.serverId, function(data) {
                self.isSentSuccess = true;
                self.sentSuccessMsg = data;
                self.setCurrentConfig(data, self.serverId);
                broadcastSrv.sayRefreshTree();
            }, function(data) {
                self.isSentError = true;
                self.sentErrorMsg = data;
                broadcastSrv.sayRefreshTree();
            });
        };

        // 清除“已成功配置”的标志，暂时没有作用。
        self.clearSuccessStat = function() {
            self.isSentSuccess = false;
        };

        // 清除“配置错误”的标志，暂时没有作用。
        self.clearErrorStat = function() {
            self.isSentError = false;
        };

        // --- 广播监听方法

        /**
         * 监听SHOW_CONFIG广播，如果设备是Server则处理这个广播，显示配置页面。
         */
        broadcastSrv.onShowConfig(function() {
            var msg = broadcastSrv.msgs[broadcastSrv.const.SHOW_CONFIG];
            if (msg.deviceType !== broadcastSrv.const.DEVICE_SERVER) {
                return;
            }
            self.loadConfig(msg.sId);
        });
    }]);

    // AngularJS控制器：Node配置控制器
    // 对应的AngularJS模板指令：nodeConfigTab
    app.controller('NodeConfigCtrl', ['apiSrv', 'broadcastSrv', '$scope', function(apiSrv, broadcastSrv, self) {

        // 空白的传感器信息对象
        self.emptySensor = {
            sensor_type: '',
            sensor_id: '',
            sensor_desc: '',
            sensor_config: {}
        };

        // 空白的过滤器信息对象
        self.emptyFilter = {
            apply_on_sensor_type: '',
            apply_on_sensor_id: '',
            comparing_method: '',
            threshold: 0
        };

        // 当前配置
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

        // 新配置，最初复制一下“当前配置”即可
        self.newConfig = angular.copy(self.currentConfig);

        // 新配置转换为Json以后的字符串，调试用
        self.newConfigStr = '';

        // 当前设置中的Server的ID和Node的ID
        self.serverId = '';
        self.nodeId = '';

        // 配置是否已经成功发送
        self.isSentSuccess = false;

        // 成功发送后的Forwarder响应内容
        self.sentSuccessMsg = '';

        // 配置是否发送失败
        self.isSentError = false;

        // 发送失败后的Forwarder响应
        self.sentErrorMsg = '';

         // --- 控制器方法

        /**
         * 将NodeConfig（Object，从JSON解析而来）存储在控制器的currentConfig中。
         * @param config 从JSON解析而来的Object，是NodeConfig，即Node的配置。
         */
        self.setCurrentConfig = function(config, sId, nId) {
            if (config !== null && typeof config === 'object') {
                for (var key in self.currentConfig) {
                    if (self.currentConfig.hasOwnProperty(key)) {
                        self.currentConfig[key] = config[key];
                    }
                }
                self.serverId = sId;
                self.nodeId = nId;
                self.newConfig = angular.copy(self.currentConfig);
            }
        };

        /**
         * 将控制器的newConfig转换为JSON字符串，以供发送HTTP请求，修改Node的配置。
         * 返回一个字符串。
         */
        self.convertNewConfig = function() {
            self.newConfig.server_port = Number(self.newConfig.server_port);
            self.newConfig.node_port = Number(self.newConfig.node_port);
            self.newConfigStr = JSON.stringify(self.newConfig);
            return JSON.stringify(self.newConfig);
        };

        /**
         * 从Forwarder提供的API获取Node的配置，并使用setCurrentConfig存储在控制器中，以便显示
         * @param sId 目标Server的ID
         * @param nId 目标Node的ID
         */
        self.loadConfig = function(sId, nId) {
            apiSrv.getNodeConfig(sId, nId, function(data) {
                // success
                self.setCurrentConfig(data, sId, nId)
            }, function(data) {
                // error

            });
        };

        /**
         * 通过API发送新的Node配置。
         * 配置成功后，刷新本页面中的配置信息。
         */
        self.sendConfig = function() {
            console.log("S" + self.serverId + " N" + self.nodeId);
            apiSrv.setNodeConfig(self.convertNewConfig(), self.serverId, self.nodeId, function(data) {
                self.isSentSuccess = true;
                self.sentSuccessMsg = data;
                self.setCurrentConfig(data, self.serverId, self.nodeId);
                broadcastSrv.sayRefreshTree();
            }, function(data) {
                self.isSentError = true;
                self.sentErrorMsg = data;
                broadcastSrv.sayRefreshTree();
            });
        };

        // 清除“已成功配置”的标志，暂时没有作用。
        self.clearSuccessStat = function() {
            self.isSentSuccess = false;
        };

        // 清除“配置错误”的标志，暂时没有作用。
        self.clearErrorStar = function() {
            self.isSentError = false;
        };

        /**
         * 为新配置添加一个传感器对象，供填写
         */
        self.addSensorFieldToNewConfig = function() {
            self.newConfig.sensors.push(angular.copy(self.emptySensor));
        };

        /**
         * 为新配置添加一个过滤器对象，供填写
         */
        self.addFilterFieldToNewConfig = function() {
            self.newConfig.filters.push(angular.copy(self.emptyFilter));
        };

        /**
         * 从新配置中移除一个传感器对象
         * @param sensor 要移除的传感器对象
         */
        self.removeSensorFieldFromNewConfig = function(sensor) {
            var index = self.newConfig.sensors.indexOf(sensor);
            if (index !== -1) {
                self.newConfig.sensors.splice(index, 1);
            }
        };

        /**
         * 从新配置中移除一个过滤器对象
         * @param filter 要移除的过滤器对象
         */
        self.removeFilterFieldFromNewConfig = function(filter) {
            var index = self.newConfig.filters.indexOf(filter);
            if (index !== -1) {
                self.newConfig.filters.splice(index, 1);
            }
        };

        // --- 广播监听方法

        /**
         * 监听SHOW_CONFIG广播，如果设备是Node则处理这个广播，显示配置页面。
         */
        broadcastSrv.onShowConfig(function() {
            var msg = broadcastSrv.msgs[broadcastSrv.const.SHOW_CONFIG];
            if (msg.deviceType !== broadcastSrv.const.DEVICE_NODE) {
                return;
            }
            self.loadConfig(msg.sId, msg.nId);
        });

    }]);

    // AngularJS控制器：状态指示控制器
    // 是页面顶端的Forwarder、Server和警告指示。
    app.controller('StatusCtrl', ['broadcastSrv', '$scope', function(broadcastSrv, self) {

        self.forwarderStat = true;

        self.serverStat = false;

        self.warningStat = false;

        self.willSoundAlert = false;

        self.cancelWarning = function() {
            broadcastSrv.sayCancelWarning();
        };

        broadcastSrv.onForwarderConnect(function() {
            self.forwarderStat = true;
        });

        broadcastSrv.onForwarderDisconnect(function() {
            self.forwarderStat = false;
        });

        broadcastSrv.onServerConnect(function() {
            self.serverStat = true;
        });

        broadcastSrv.onServerDisconnect(function() {
            self.serverStat = false;
        });

        broadcastSrv.onShowWarning(function() {
            self.warningStat = true;
            if (self.willSoundAlert) {
                document.getElementById('alert-audio').play();
            }
        });

        broadcastSrv.onCancelWarning(function() {
            self.warningStat = false;
        });

    }]);
})();