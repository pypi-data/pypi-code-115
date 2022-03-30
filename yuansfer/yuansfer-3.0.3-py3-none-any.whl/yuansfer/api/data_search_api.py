# -*- coding: utf-8 -*-
from yuansfer.api_helper import APIHelper
from yuansfer.http.api_response import ApiResponse
from yuansfer.api.base_api import BaseApi
from yuansfer.exception import InvalidParamsError
from yuansfer import constant

class DataSearchApi(BaseApi):

    """A Controller to access Endpoints in the Yuansfer API."""

    def __init__(self, config):
        super(DataSearchApi, self).__init__(config)

    def refund(self,
                  body):
        """POST Request to make refund request
        Refund a Yuansfer transaction
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
        _url_path = constant.REFUND
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        self.validation('refundAmount',body['refundAmount'],'amount')

        requiredFileds = ['currency','settleCurrency']
        self.validate_parameter(requiredFileds,body)

        transcationNo = body.get('transactionNo')
        reference = body.get('reference')
        if (transcationNo and reference and (body['transactionNo'] and body['reference']) is None) or (not transcationNo and not reference):
            raise InvalidParamsError("transactionNo and reference cannot be null at the same time")

        if transcationNo and reference and (body['transactionNo'] and body['reference']) is not None:
            raise InvalidParamsError("transactionNo and reference cannot exist at the same time")

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def reverse(self,
                  body):
        """POST Request to reverse transaction
        Reverse Yuansfer transaction
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
        _url_path = constant.REVERSE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        transcationNo = body.get('transactionNo')
        reference = body.get('reference')
        if (transcationNo and reference and (body['transactionNo'] and body['reference']) is None) or (not transcationNo and not reference):
            raise InvalidParamsError("transactionNo and reference cannot be null at the same time")

        if transcationNo and reference and (body['transactionNo'] and body['reference']) is not None:
            raise InvalidParamsError("transactionNo and reference cannot exist at the same time")

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def tran_query(self,
                  body):
        """POST Request to get transaction detail
        Get transaction detail
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
        _url_path = constant.TRAN_QUERY
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        transcationNo = body.get('transactionNo')
        reference = body.get('reference')
        if (transcationNo and reference and (body['transactionNo'] and body['reference']) is None) or (not transcationNo and not reference):
            raise InvalidParamsError("transactionNo and reference cannot be null at the same time")

        if transcationNo and reference and (body['transactionNo'] and body['reference']) is not None:
            raise InvalidParamsError("transactionNo and reference cannot exist at the same time")

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def mixed_query(self,
                  body):
        """POST Request to get transaction detail of mixed qrcode
        Get transaction detail of mixed qrcode
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
        _url_path = constant.MIXED_QUERY
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        recordNo = body.get('recordNo')
        reference = body.get('reference')
        if (recordNo and reference and (body['recordNo'] and body['reference']) is None) or (not recordNo and not reference):
            raise InvalidParamsError("recordNo and reference cannot be null at the same time")

        if recordNo and reference and (body['recordNo'] and body['reference']) is not None:
            raise InvalidParamsError("recordNo and reference cannot exist at the same time")

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def mixed_cancel(self,
                  body):
        """POST Request to reverse mixed qrcode transaction
        Reverse Yuansfer transaction
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
        _url_path = constant.REVERSE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        recordNo = body.get('recordNo')
        reference = body.get('reference')
        if (recordNo and reference and (body['recordNo'] and body['reference']) is None) or (not recordNo and not reference):
            raise InvalidParamsError("recordNo and reference cannot be null at the same time")

        if recordNo and reference and (body['recordNo'] and body['reference']) is not None:
            raise InvalidParamsError("recordNo and reference cannot exist at the same time")

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result
