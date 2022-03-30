# -*- coding: utf-8 -*-
from yuansfer.api_helper import APIHelper
from yuansfer.http.api_response import ApiResponse
from yuansfer.api.base_api import BaseApi
from yuansfer.exception import InvalidParamsError
from yuansfer import constant

class AuthApi(BaseApi):

    """A Controller to access Endpoints in the Yuansfer API."""

    def __init__(self, config):
        super(AuthApi, self).__init__(config)

    def auth_capture(self,
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
        _url_path = constant.AUTH_CAPTURE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        outAuthInfoNo = body.get('outAuthInfoNo')
        authInfoNo = body.get('authInfoNo')
        if (outAuthInfoNo and authInfoNo and (body['outAuthInfoNo'] and body['authInfoNo']) is None) or (not outAuthInfoNo and not authInfoNo):
            raise InvalidParamsError("outAuthInfoNo and authInfoNo cannot be null at the same time")

        if outAuthInfoNo and authInfoNo and (body['outAuthInfoNo'] and body['authInfoNo']) is not None:
            raise InvalidParamsError("outAuthInfoNo and authInfoNo cannot exist at the same time")

        requiredFileds = ['currency','settleCurrency','outAuthDetailNo','reference']
        self.validate_parameter(requiredFileds,body)

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

    def auth_detail_query(self,
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
        _url_path = constant.AUTH_DETAIL_QUERY
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        outAuthInfoNo = body.get('outAuthInfoNo')
        authInfoNo = body.get('authInfoNo')
        if (outAuthInfoNo and authInfoNo and (body['outAuthInfoNo'] and body['authInfoNo']) is None) or (not outAuthInfoNo and not authInfoNo):
            raise InvalidParamsError("outAuthInfoNo and authInfoNo cannot be null at the same time")

        if outAuthInfoNo and authInfoNo and (body['outAuthInfoNo'] and body['authInfoNo']) is not None:
            raise InvalidParamsError("outAuthInfoNo and authInfoNo cannot exist at the same time")

        outAuthDetailNo = body.get('outAuthDetailNo')
        authDetailNo = body.get('authDetailNo')
        if (outAuthDetailNo and authDetailNo and (body['outAuthDetailNo'] and body['authDetailNo']) is None) or (not outAuthDetailNo and not authDetailNo):
            raise InvalidParamsError("outAuthDetailNo and authDetailNo cannot be null at the same time")

        if outAuthDetailNo and authDetailNo and (body['outAuthDetailNo'] and body['authDetailNo']) is not None:
            raise InvalidParamsError("outAuthDetailNo and authDetailNo cannot exist at the same time")

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def auth_unfreeze(self,
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
        _url_path = constant.AUTH_FREEAE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        outAuthInfoNo = body.get('outAuthInfoNo')
        authInfoNo = body.get('authInfoNo')
        if (outAuthInfoNo and authInfoNo and (body['outAuthInfoNo'] and body['authInfoNo']) is None) or (not outAuthInfoNo and not authInfoNo):
            raise InvalidParamsError("outAuthInfoNo and authInfoNo cannot be null at the same time")

        if outAuthInfoNo and authInfoNo and (body['outAuthInfoNo'] and body['authInfoNo']) is not None:
            raise InvalidParamsError("outAuthInfoNo and authInfoNo cannot exist at the same time")

        requiredFileds = ['outAuthDetailNo','currency','settleCurrency']
        self.validate_parameter(requiredFileds,body)

        self.validation('unfreezeAmount',body['unfreezeAmount'],'amount')

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def auth_freeze(self,
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
        _url_path = constant.AUTH_UNFREEZE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        requiredFileds = ['outAuthInfoNo','outAuthDetailNo','vendor','currency','settleCurrency']
        self.validate_parameter(requiredFileds,body)

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

    def auth_voucher_create(self,
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
        _url_path = constant.AUTH_VOUCHER_CREATE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        requiredFileds = ['outAuthInfoNo','outAuthDetailNo','vendor']
        self.validate_parameter(requiredFileds,body)
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
