import unittest

from src.__main__ import MainClass


class TestAccessToken(unittest.TestCase):

    # Initiate Asset Controller Class
    def setUp(self):
        self.main = MainClass("./src/tests/test_controller_config.yml")

    def test_get_access_token(self):
        self.main.get_access_token()
