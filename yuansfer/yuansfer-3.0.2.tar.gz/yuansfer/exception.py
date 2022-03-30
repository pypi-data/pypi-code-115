# -*- coding: utf-8 -*-

class YuansferException(Exception):
    def __init__(self,
                 message=None,
                 params=None,
                 http_status=None
    ):
        super(YuansferException, self).__init__(message)

        self._message = message
        self.params = params
        self.http_status = http_status

    def __str__(self):
        msg = self._message or "<empty message>"
        if msg is not None:
            return msg
        else:
            return "Something Wrong"

    def user_message(self):
        return self._message

class APIConnectionError(YuansferException):
    def __init__(
        self,
        ret_code=None,
        ret_msg=None,
        should_retry=False,
    ):
        super(APIConnectionError, self).__init__(
            ret_code,ret_msg
        )
        self.should_retry = should_retry

class RequireParamsError(YuansferException):
    def __str__(self):
        return (
            '%s is missing!' % (self.params)
        )

class InvalidParamsError(YuansferException):
    def __str__(self):
        return (
            self._message
        )
