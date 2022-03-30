# -*- coding: utf-8 -*-
from yuansfer.api_helper import APIHelper
from yuansfer.http.api_response import ApiResponse
from yuansfer.api.base_api import BaseApi
from yuansfer.exception import InvalidParamsError
from yuansfer.exception import RequireParamsError
from yuansfer import constant

class MobileApi(BaseApi):

    """A Controller to access Endpoints in the Yuansfer API."""

    def __init__(self, config):
        super(MobileApi, self).__init__(config)

    def express_pay(self,
                  body):
        """POST Request

        Args:
            body: An object containing the fields to
                POST for the request.  See the corresponding object definition
                for field details.
        Returns:
            ApiResponse: An object with the response value as well as other
                useful information such as status codes and headers. Success
        Raises:
            APIException: When an error occurs while fetching the data from
                the remote API. This exception includes the HTTP Response
                code, an error message, and the HTTP body that was received in
                the request.
        """

        # Prepare query URL
        _url_path = constant.EXPRESS_PAY
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        requiredFileds = ['cardNumber','cardExpYear','cardExpMonth','cardCvv','currency','settleCurrency','reference','clientIp']
        self.validate_parameter(requiredFileds,body)

        self.validation('cardNumber',body['cardNumber'],'number')
        self.validation('cardExpYear',body['cardExpYear'],'number')
        self.validation('cardExpMonth',body['cardExpMonth'],'number')
        self.validation('cardCvv',body['cardCvv'],'number')

        self.validation('amount',body['amount'],'amount')

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def mobile_prepay(self,
                  body):
        """POST Request

        Args:
            body: An object containing the fields to
                POST for the request.  See the corresponding object definition
                for field details.
        Returns:
            ApiResponse: An object with the response value as well as other
                useful information such as status codes and headers. Success
        Raises:
            APIException: When an error occurs while fetching the data from
                the remote API. This exception includes the HTTP Response
                code, an error message, and the HTTP body that was received in
                the request.
        """

        # Prepare query URL
        _url_path = constant.MOBILE_PREPAY
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        self.validation('amount',body['amount'],'amount')

        requiredFileds = ['reference','currency','settleCurrency','vendor','terminal']
        self.validate_parameter(requiredFileds,body)

        if body['vendor'] == 'wechatpay':
            if body['terminal'] == 'MINIPROGRAM' and body['openid'] is None:
                raise RequireParamsError('openid')

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result
