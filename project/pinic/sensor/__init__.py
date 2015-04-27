# -*- coding: utf-8 -*-

"""
这个Python包中，含有和传感器工作相关的类。

类说明
======

* basesensor.BaseSensor类是所有传感器驱动类的基类。

* sensor_stub.Sensor是测试所用的虚拟传感器驱动类。

* sensor_tlc1549.Sensor是TLC1549传感器的驱动类。

* sensordata.SensorData类包装一份传感器数据。该模块还含有从文本解析传感数据的方法。

如果要……
==========

* 要增添一个传感器，请编写名为sensor_(type).py的Python模块，其中(type)为传感器的种类（即代码中type变量的值），
并继承basesensor.BaseSensor类。示例见sensor_tlc1549.py和sensor_stub.py。

* 要处理传感器数据，请参考sensordata.SensorData.get_json_dumps()方法和sensordata.parse_from_string(str)方法。
"""

__author__ = 'tgmerge'
