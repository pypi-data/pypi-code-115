# -*- coding: utf-8 -*-
from datetime import datetime

from tests.api.test_api_base import ApiTestBase

class MobileApiTests(ApiTestBase):

    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(MobileApiTests, cls).setUpClass()

    # Make Mobile Express Pay request.
    def test_express_pay(self):
        # Parameters for the API call
        params = {
            'amount':'0.01',
            'currency':'USD',
            'settleCurrency':'USD',
            'reference': datetime.now,
            'cardNumber': '4111111111111111',
            'cardExpYear': '2021',
            'cardExpMonth': '12',
            'cardCvv': '999',
            'clientIp': '192.168.1.1'
        }

        # Perform the API call through the SDK function
        response = self.client.mobile.express_pay(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

     # Make Mobile Express Pay request.
    def test_mobile_prepay(self):
        # Parameters for the API call
        params = {
            'amount':'0.01',
            'currency':'USD',
            'settleCurrency':'USD',
            'reference': datetime.now,
            'vendor':'alipay',
            'terminal':'APP'
        }

        # Perform the API call through the SDK function
        response = self.client.mobile.mobile_prepay(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = MobileApiTests()
unittest.setUpClass()
unittest.test_express_pay()
unittest.test_mobile_prepay()
