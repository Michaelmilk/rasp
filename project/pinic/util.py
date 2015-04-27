# coding=utf-8

"""
本Python模块包含通用的工具方法和异常等。

* 异常 ServerError 被各Web服务器抛出，可包含其他异常。
* 异常 TimeoutError 用于超时处理。
* 方法 generate_500 生成一个HTTP 500服务器响应，用于表示服务器错误。
"""

__author__ = "tgmerge"


from bottle import HTTPResponse
from json import dumps


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


class TimeoutError(Exception):

    pass


def generate_500(desc, err=None):
    """
    生成带信息的HTTP 500响应，用于服务器错误。
    返回一个HTTPResponse，含有Json表示的说明信息(desc)和异常(err)。

    :param str desc: 错误信息
    :param Exception err: 要包含的异常
    :rtype: HTTPResponse
    """
    return HTTPResponse(status=500, body=dumps({
        "status": 500,
        "desc": desc,
        "exception": str(err)
    }))