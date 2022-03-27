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

import pulpcore.client.pulp_ostree
from pulpcore.client.pulp_ostree.api.remotes_ostree_api import RemotesOstreeApi  # noqa: E501
from pulpcore.client.pulp_ostree.rest import ApiException


class TestRemotesOstreeApi(unittest.TestCase):
    """RemotesOstreeApi unit test stubs"""

    def setUp(self):
        self.api = pulpcore.client.pulp_ostree.api.remotes_ostree_api.RemotesOstreeApi()  # noqa: E501

    def tearDown(self):
        pass

    def test_create(self):
        """Test case for create

        Create an ostree remote  # noqa: E501
        """
        pass

    def test_delete(self):
        """Test case for delete

        Delete an ostree remote  # noqa: E501
        """
        pass

    def test_list(self):
        """Test case for list

        List ostree remotes  # noqa: E501
        """
        pass

    def test_partial_update(self):
        """Test case for partial_update

        Update an ostree remote  # noqa: E501
        """
        pass

    def test_read(self):
        """Test case for read

        Inspect an ostree remote  # noqa: E501
        """
        pass

    def test_update(self):
        """Test case for update

        Update an ostree remote  # noqa: E501
        """
        pass


if __name__ == '__main__':
    unittest.main()
