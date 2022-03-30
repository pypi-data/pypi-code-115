# -*- coding: utf-8 -*-
from yuansfer.api_helper import APIHelper
from yuansfer.exception import RequireParamsError
from yuansfer.exception import InvalidParamsError
import hashlib
import re

class BaseApi(object):

    def global_headers(self):
        return{
            'Content-Type': 'application/json',
            'accept': 'application/json',

        }

    def __init__(self, config):
        self._config = config

    @property
    def config(self):
        return self._config

    def validation(self,param, value, validationType):
        # Check if params exist
        if value is None:
            raise RequireParamsError(params = param)

        if validationType == "timestamp":
            reg = r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z$"
        elif validationType == "date":
            reg = r"^\\d{4}\\d{2}\\d{2}$"
        elif validationType == "number":
            reg = r"^[0-9]*[1-9][0-9]*$"
        elif validationType == "amount":
            reg = r"(?=.*?\d)^\$?(([1-9]\d{0,2}(,\d{3})*)|\d+)?(\.\d{1,2})?$"

        if not re.match(reg, value):
            raise InvalidParamsError("data error: " + param)

    def validate_parameter(self, requiredFileds, body):
        for name in requiredFileds:
            if name not in body:
                raise RequireParamsError(params=name)
            else:
                if body[name] is None:
                    raise RequireParamsError(params=name)

    def execute_request(self, request, binary=False):
        # Invoke the API call to fetch the response.
        if request.headers is None:
            request.headers = self.global_headers()

        request.parameters['verifySign'] = self.verify_sign_method(request.parameters)
        func = self.config.http_client.execute
        response = func(request)

        return response

    def verify_sign_method(self, parameters):
        """Convert object to request params
        Args:
            parameters (object): The parameters to convert.
        Returns:
            str: string with appended parameters.
        """
        # Parameter validation
        if self.config is None:
            raise InvalidParamsError('Configs are missing')

        parameters['merchantNo'] = self.config.merchantNo
        parameters['storeNo'] = self.config.storeNo
        dictionaryParams = APIHelper.to_dictionary(parameters)
        stringParams = APIHelper.append_parameters(dictionaryParams)
        md5TokenStr =hashlib.md5(self.config.token.encode("utf-8")).hexdigest()
        res = hashlib.md5((stringParams + '&' + md5TokenStr).encode("utf-8")).hexdigest()

        return res
