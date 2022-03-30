# -*- coding: utf-8 -*-
import json
from datetime import datetime

from tests.api.test_api_base import ApiTestBase
from tests.test_helper import TestHelper
from yuansfer.api_helper import APIHelper
from yuansfer.api.payout_api import PayoutApi


class PayoutApiTests(ApiTestBase):
    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(PayoutApiTests, cls).setUpClass()

    # Make Payout Payment request.
    def test_pay(self):
        # Parameters for the API call
        params = {
            "customerNo": self.customerNo,
            "accountToken": self.accountToken,
            "amount": "0.01",
            "currency": "USD",
            "description": "Thank You",
            "invoiceId": self.invoiceId,
            "ipnUrl": "https://yuansferdev.com/callback",
            "note": "Payouts, Thanks",
            "subject": "Payouts"
        }

        # Perform the API call through the SDK function
        response = self.client.payout.pay(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Payout Inquiry request.
    def test_inquiry(self):
        # Parameters for the API call
        params = {
            'invoiceId':self.invoiceId,
        }

        # Perform the API call through the SDK function
        response = self.client.payout.inquiry(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Payout Create Account request.
    def test_create_account(self):
        # Parameters for the API call
        params = {
            "accountType":"PAYPAL",
            "accountTag":"20210421001002",
            "clientIp":"114,114,114,114",
            "customerNo":"2000305228245812947930",
            "callbackUrl": "https://yuansferdev.com/callback",

        }

        # Perform the API call through the SDK function
        response = self.client.payout.create_account(params)
        data = response.body
        self.customerNo = data['result']['customerNo']
        self.accountToken = data['result']['accountToken']
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = PayoutApiTests()
unittest.setUpClass()
unittest.test_create_account()
unittest.test_pay()
unittest.test_inquiry()