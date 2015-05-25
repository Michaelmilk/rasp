# coding=utf-8

"""
本Python模块包含通用的工具方法和异常等。
"""

__author__ = "tgmerge"


from bottle import HTTPResponse
from json import dumps


class ServerError(Exception):
    """
    本异常继承Exception，可包含其他异常。
    本异常被各Web服务器抛出，表示服务器处理请求中出现的异常情况。
    """

    def __init__(self, value, inner_error=None):
        """
        创建一个ServerError。向inner_error传入其他异常以包含它。

        :param value: 本异常包含的文本信息。
        :param Exception inner_error: 本异常包含的其他异常。
        """
        self.value = value
        self.inner_error = inner_error
        """ :type: Exception """

    def __str__(self):
        """
        Python内置方法__str__的实现。返回一个描述本异常的字符串。

        :rtype basestring
        """
        if self.inner_error is None:
            return repr(self.value)
        else:
            return repr(self.value) + "Inner exception:" + repr(self.inner_error)


class TimeoutError(Exception):
    """
    本异常直接继承Exception，用于超时处理。
    """
    pass


def generate_500(desc, err=None):
    """
    本函数生成一个带信息的HTTP 500服务器响应，用于在bottle服务器中作为返回，表示服务器错误。
    函数将返回一个HTTPResponse对象，含有Json表示的说明信息(desc)和异常(err)。

    :param str desc: 错误信息
    :param Exception err: 要包含的异常
    :rtype: HTTPResponse
    """
    return HTTPResponse(status=500, body=dumps({
        "status": 500,
        "desc": desc,
        "exception": str(err)
    }))
