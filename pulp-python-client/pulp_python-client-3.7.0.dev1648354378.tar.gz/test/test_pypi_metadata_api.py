# coding: utf-8

"""
    Pulp 3 API

    Fetch, Upload, Organize, and Distribute Software Packages  # noqa: E501

    The version of the OpenAPI document: v3
    Contact: pulp-list@redhat.com
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest

import pulpcore.client.pulp_python
from pulpcore.client.pulp_python.api.pypi_metadata_api import PypiMetadataApi  # noqa: E501
from pulpcore.client.pulp_python.rest import ApiException


class TestPypiMetadataApi(unittest.TestCase):
    """PypiMetadataApi unit test stubs"""

    def setUp(self):
        self.api = pulpcore.client.pulp_python.api.pypi_metadata_api.PypiMetadataApi()  # noqa: E501

    def tearDown(self):
        pass

    def test_read(self):
        """Test case for read

        Get package metadata  # noqa: E501
        """
        pass


if __name__ == '__main__':
    unittest.main()
