import unittest

from the_one_api_sdk import TheOneApi


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.api = TheOneApi(api_key='test-token')
