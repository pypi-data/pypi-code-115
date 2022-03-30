# -*- coding: utf-8 -*-
import json
from datetime import datetime
import random
from time import strftime

from tests.api.test_api_base import ApiTestBase
from tests.test_helper import TestHelper
from yuansfer.api_helper import APIHelper
from yuansfer.api.online_api import OnlineApi


class OnlineApiTests(ApiTestBase):

    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(OnlineApiTests, cls).setUpClass()

    # Make Secure Pay request.
    def test_secure_pay(self):
        # Parameters for the API call
        params = {
            'amount':'50',
            'currency':'USD',
            'settleCurrency':'USD',
            'vendor':'paypal',
            'terminal':'ONLINE',
            'reference': random.randint(0,100000000),
            'ipnUrl':"http://zk-tys.yunkeguan.com/ttest/test",
            'callbackUrl':"http://zk-tys.yunkeguan.com/ttest/test",
            'description':'descrip',
            'note':'note'
        }

        # Perform the API call through the SDK function
        response = self.client.online.secure_pay(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Process request.
    def test_process(self):
        # Parameters for the API call
        params = {
            'transactionNo':'11111',
            'paymentMethod':'creditcard',
            'paymentMethodNonce':'****',
        }

        # Perform the API call through the SDK function
        response = self.client.online.process(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = OnlineApiTests()
unittest.setUpClass()
unittest.test_secure_pay()
