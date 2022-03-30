# -*- coding: utf-8 -*-
from datetime import datetime

from tests.api.test_api_base import ApiTestBase

class OfflineApiTests(ApiTestBase):

    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(OfflineApiTests, cls).setUpClass()

    # Make Instore Add Transaction request.
    def test_instore_add(self):
        # Parameters for the API call
        params = {
            'amount':'0.01',
            'currency':'USD',
            'settleCurrency':'USD',
            'reference': datetime.now
        }

        # Perform the API call through the SDK function
        response = self.client.offline.instore_add(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Instore Cashier Add request.
    def test_instore_cashier_add(self):
        # Parameters for the API call
        params = {
            'amount':'0.01',
            'currency':'USD',
            'settleCurrency':'USD',
            'reference': datetime.now,
            'ipnUrl':"http://zk-tys.yunkeguan.com/ttest/test",
            'storeAdminNo':'testNo'
        }

        # Perform the API call through the SDK function
        response = self.client.offline.instore_cashier_add(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Instore Create Tran QR Code request.
    def test_instore_create_tran_qrcode(self):
        # Parameters for the API call
        params = {
            'amount':'0.01',
            'currency':'USD',
            'settleCurrency':'USD',
            'reference': datetime.now
        }

        # Perform the API call through the SDK function
        response = self.client.offline.instore_create_tran_qrcode(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Instore Payment request.
    def test_instore_pay(self):
        # Parameters for the API call
        params = {
            'reference': datetime.now,
            'paymentBarcode':'test',
            'vendor':'wechat'
        }

        # Perform the API call through the SDK function
        response = self.client.offline.instore_pay(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Third Party Acquire request.
    def test_third_party_acquire_create(self):
        # Parameters for the API call
        params = {
            'amount':'0.01',
            'currency':'USD',
            'settleCurrency':'USD',
            'vendor':'alipay',
            'alipayUserId':"shawnTest",
        }

        # Perform the API call through the SDK function
        response = self.client.offline.third_party_acquire_create(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = OfflineApiTests()
unittest.setUpClass()
unittest.test_instore_add()
unittest.test_instore_cashier_add()
unittest.test_instore_pay()
unittest.test_instore_create_tran_qrcode
unittest.test_third_party_acquire_create
