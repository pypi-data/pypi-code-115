# -*- coding: utf-8 -*-
from yuansfer.api_helper import APIHelper
from yuansfer.http.api_response import ApiResponse
from yuansfer.api.base_api import BaseApi
from yuansfer.exception import InvalidParamsError
from yuansfer import constant


class OfflineApi(BaseApi):

    """A Controller to access Endpoints in the Yuansfer API."""

    def __init__(self, config):
        super(OfflineApi, self).__init__(config)

    def instore_add(self,
                  body):
        """POST Request make In Store add transaction request
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
        _url_path = constant.INSTORE_ADD
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        self.validation('amount',body['amount'],'amount')
        requiredFileds = ['currency','settleCurrency','reference']
        self.validate_parameter(requiredFileds,body)

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def instore_cashier_add(self,
                  body):
        """POST Request to InstoreCashierAdd
        Create Yuansfer transaction
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
        _url_path = constant.INSTORE_CASHIER_ADD
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        requiredFileds = ['currency','settleCurrency','reference','ipnUrl','storeAdminNo']
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

    def instore_create_tran_qrcode(self,
                  body):
        """POST Request to InstoreCreateTranQRCode
        Create Yuansfer transaction and generate qr code
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
        _url_path = constant.INSTORE_TRAN_QRCODE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        self.validation('amount',body['amount'],'amount')
        requiredFileds = ['currency','settleCurrency','reference']
        self.validate_parameter(requiredFileds,body)

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def instore_pay(self,
                  body):
        """POST Request to InstorePay
        Process a instore qrc payment
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
        _url_path = constant.INSTORE_PAY
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        transcationNo = body.get('transactionNo')
        reference = body.get('reference')
        if (transcationNo and reference and (body['transactionNo'] and body['reference']) is None) or (not transcationNo and not reference):
            raise InvalidParamsError("transaction and reference cannot be null at the same time")

        if transcationNo and reference and (body['transactionNo'] and body['reference']) is not None:
            raise InvalidParamsError("transaction and reference cannot exist at the same time")

        requiredFileds = ['paymentBarcode','vendor']
        self.validate_parameter(requiredFileds,body)

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def third_party_acquire_create(self,
                  body):
        """POST Request to ThirdPartyAcquireCreate

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
        _url_path = constant.THIRDPART_ACQUIRE_CREATE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        self.validation('amount',body['amount'],'amount')
        requiredFileds = ['reference','currency','settleCurrency','vendor','alipayUserId']
        self.validate_parameter(requiredFileds,body)

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

    def generate_mixed_qrcode(self,
                  body):
        """POST Request to Instore Gennerate Mixed QRC
        Create Yuansfer transaction and generate qr code
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
        _url_path = constant.GENERATE_MIXED_QRCODE
        _query_builder = self.config.get_base_uri()
        _query_url = _query_builder+_url_path

        # Parameters validation
        self.validation('saleAmount',body['saleAmount'],'amount')
        requiredFileds = ['currency','settleCurrency','reference']
        self.validate_parameter(requiredFileds,body)

        # Prepare and execute request
        _request = self.config.http_client.post(_query_url, headers=None, parameters=body)
        _response = self.execute_request(_request)

        if type(_response.response) is not dict:
            _errors = _response.reason
        else:
            _errors = None
        _result = ApiResponse(_response, body=_response.response, errors=_errors)
        return _result

