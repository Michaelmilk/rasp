# coding=utf-8

"""
本Python模块包含pinic可能抛出的自定义异常。

* ServerError: 被各Web服务器抛出，可包含其他异常。
"""

__author__ = "tgmerge"


class ServerError(Exception):

    def __init__(self, value, inner_error=None):
        """
        创建一个ServerError。向inner_error传入其他异常以包含它。
        :type inner_error: Exception
        """
        self.value = value
        self.inner_error = inner_error
        """ :type: Exception """

    def __str__(self):
        if self.inner_error is None:
            return repr(self.value)
        else:
            return repr(self.value) + "Inner exception:" + repr(self.inner_error)
