__author__ = 'tgmerge'


class ServerError(Exception):

    def __init__(self, value, inner_error=None):
        """
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
