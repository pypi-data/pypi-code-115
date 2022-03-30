# -*- coding: utf-8 -*-
from datetime import datetime

from tests.api.test_api_base import ApiTestBase

class CustomerApiTests(ApiTestBase):

    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(CustomerApiTests, cls).setUpClass()

    # Make Create Customer Account request.
    def test_create_account(self):
        # Parameters for the API call
        params = {
            "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "countryCode": "US",

            "email": "202105101111@shawn.yuansfer",
            "firstName": "ShuPian",
            "lastName": "Sun",
        }

        # Perform the API call through the SDK function
        response = self.client.customer.create_account(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Retrieve Customer Account request.
    def test_retrieve_account(self):
        # Parameters for the API call
        params = {
            "customerCode": "20210419190001",
            "timestamp": "2021-04-19T11:40:02Z",
            "customerNo": "2000305228245724354226"
        }

        # Perform the API call through the SDK function
        response = self.client.customer.retrieve_account(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

    # Make Update Customer Account request.
    def test_update_account(self):
        # Parameters for the API call
        params = {
            "timestamp": "2021-04-19T11:48:18Z",
            "customerNo": "2000305228245724354226",
            "city": "New York city"
        }

        # Perform the API call through the SDK function
        response = self.client.customer.update_account(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = CustomerApiTests()
unittest.setUpClass()
unittest.test_create_account()
unittest.test_retrieve_account()
unittest.test_update_account()
