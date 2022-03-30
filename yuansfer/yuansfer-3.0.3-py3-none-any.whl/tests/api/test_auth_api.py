# -*- coding: utf-8 -*-
from datetime import datetime
from tests.api.test_api_base import ApiTestBase

class AuthApiTests(ApiTestBase):

    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(AuthApiTests, cls).setUpClass()

    # Make Auth Capture request.
    def test_auth_capture(self):
        # Parameters for the API call
        params = {
            'amount': '0.01',
            'outAuthInfoNo': '298217806906830305',
            'currency': 'USD',
            'settleCurrency': 'USD',
            'reference': datetime.now(),
            'outAuthDetailNo': '0000'
        }

        # Perform the API call through the SDK function
        response = self.client.auth.auth_capture(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Auth Detail Query request.
    def test_auth_detail_query(self):
        # Parameters for the API call
        params = {
            'outAuthInfoNo': '298217806906830305',
            'outAuthDetailNo': '0000'
        }

        # Perform the API call through the SDK function
        response = self.client.auth.auth_detail_query(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Auth Unfreeze request.
    def test_auth_unfreeze(self):
        # Parameters for the API call
        params = {
            'unfreezeAmount': '0.01',
            'outAuthInfoNo': '298217806906830305',
            'currency': 'USD',
            'settleCurrency': 'USD',
            'outAuthDetailNo': '0000'
        }

        # Perform the API call through the SDK function
        response = self.client.auth.auth_unfreeze(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Auth Freeze request.
    def test_auth_freeze(self):
        # Parameters for the API call
        params = {
            'amount': '0.01',
            'outAuthInfoNo': '298217806906830305',
            'currency': 'USD',
            'settleCurrency': 'USD',
            'outAuthDetailNo': '0000',
            'vendor': 'alipay'
        }

        # Perform the API call through the SDK function
        response = self.client.auth.auth_freeze(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Auth Voucher Create request.
    def test_auth_voucher_create(self):
        # Parameters for the API call
        params = {
            'amount': '0.01',
            'outAuthInfoNo': '298217806906830305',
            'outAuthDetailNo': '0000',
            'vendor': 'alipay'
        }

        # Perform the API call through the SDK function
        response = self.client.auth.auth_voucher_create(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = AuthApiTests()
unittest.setUpClass()
unittest.test_auth_capture()
unittest.test_auth_detail_query()
unittest.test_auth_freeze()
unittest.test_auth_unfreeze()
unittest.test_auth_voucher_create()

