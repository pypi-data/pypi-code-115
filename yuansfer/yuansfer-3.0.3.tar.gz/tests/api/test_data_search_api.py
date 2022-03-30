# -*- coding: utf-8 -*-
from tests.api.test_api_base import ApiTestBase

class DataSearchApiTests(ApiTestBase):

    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(DataSearchApiTests, cls).setUpClass()

    # Make Refund request.
    def test_refund(self):
        # Parameters for the API call
        params = {
            "refundAmount": "0.01",
            "currency": "USD",
            "settleCurrency": "USD",
            "transactionNo": "297553638301777927",
            "refundReference": "refund2020101305"
        }

        # Perform the API call through the SDK function
        response = self.client.data_search.refund(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Reverse request.
    def test_reverse(self):
        # Parameters for the API call
        params = {
            "transactionNo": "297553638301777927",
        }

        # Perform the API call through the SDK function
        response = self.client.data_search.reverse(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Transaction Query request.
    def test_tran_query(self):
        # Parameters for the API call
        params = {
            "transactionNo": "297553638301777927"
        }

        # Perform the API call through the SDK function
        response = self.client.data_search.tran_query(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = DataSearchApiTests()
unittest.setUpClass()
unittest.test_refund()
unittest.test_reverse()
unittest.test_tran_query()
