# -*- coding: utf-8 -*-

"""本Python模块含有传感器驱动的基类。要编写新的传感器驱动，你需要继承BaseSensor类。"""

__author__ = "tgmerge"


from pinic.sensor.sensordata import SensorData


class BaseSensor(object):
    """
    传感器驱动的基类。要编写新的传感器驱动，继承这个类，并实现其中的所有方法。

    范例可参见sensor_stub.py。
    """

    def __init__(self, sensor_type, sensor_id, sensor_desc, sensor_config):
        """
        :param str sensor_type:    传感器的种类。这个值被用来载入驱动模块文件。
        :param str sensor_id:      在系统中识别传感器用的ID值。
        :param str sensor_desc:    传感器的描述。例如，被放置在某地。
        :param dict sensor_config: 初始化传感器所需的配置。如果不需要可以为空。
        """
        self.sensor_type = sensor_type
        self.sensor_id = sensor_id
        self.sensor_desc = sensor_desc
        self.sensor_config = sensor_config
        self.last_data = None            # Last successfully gathered data.
        """ :type: SensorData """
        self.is_initialized = False      # Flag, indicating if the sensor is initialized.
        """ :type: bool"""               # Call initialize() and close() to set this.

    def initialize(self):
        """
        使用sensor_config的配置初始化传感器。

        编写传感器驱动模块时，请覆盖这个方法，并在方法中设置is_initialized为true。
        """
        self.is_initialized = True

    def get_data(self):
        """
        从传感器读取传感值，返回包含传感值的SensorData对象。

        编写传感器驱动模块时，请覆盖这个方法，并在读取值之前检查is_initialized。

        :rtype: SensorData
        """
        if not self.is_initialized:
            raise Exception("Sensor(type=%s, id=%s, desc=%s) is not initialized." % (self.sensor_type, self.sensor_id, self.sensor_desc))

        self.last_data = SensorData(sensor_type="BaseSensor: fake data", raw_value=0)
        return self.last_data

    def get_json_dumps_data(self):
        """
        从传感器读取传感值，返回包含传感值的JSON字符串。

        编写传感器驱动模块时，如需要可以覆盖这个方法。

        :rtype: str
        """
        return self.get_data().get_json_dumps()

    def close(self):
        """
        安全地停止传感器的工作。

        编写传感器驱动模块时，请覆盖这个方法，并在方法中设置is_initialized为false。
        """
        self.is_initialized = False
