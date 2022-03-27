#!/usr/bin/python
#
# Copyright 2018-2021 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding: utf-8

"""
    Polyaxon SDKs and REST API specification.

    Polyaxon SDKs and REST API specification.  # noqa: E501

    The version of the OpenAPI document: 1.17.1
    Contact: contact@polyaxon.com
    Generated by: https://openapi-generator.tech
"""


try:
    from inspect import getfullargspec
except ImportError:
    from inspect import getargspec as getfullargspec
import pprint
import re  # noqa: F401
import six

from polyaxon_sdk.configuration import Configuration


class V1WasbType(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'container': 'str',
        'storage_account': 'str',
        'path': 'bool'
    }

    attribute_map = {
        'container': 'container',
        'storage_account': 'storageAccount',
        'path': 'path'
    }

    def __init__(self, container=None, storage_account=None, path=None, local_vars_configuration=None):  # noqa: E501
        """V1WasbType - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration.get_default_copy()
        self.local_vars_configuration = local_vars_configuration

        self._container = None
        self._storage_account = None
        self._path = None
        self.discriminator = None

        if container is not None:
            self.container = container
        if storage_account is not None:
            self.storage_account = storage_account
        if path is not None:
            self.path = path

    @property
    def container(self):
        """Gets the container of this V1WasbType.  # noqa: E501


        :return: The container of this V1WasbType.  # noqa: E501
        :rtype: str
        """
        return self._container

    @container.setter
    def container(self, container):
        """Sets the container of this V1WasbType.


        :param container: The container of this V1WasbType.  # noqa: E501
        :type container: str
        """

        self._container = container

    @property
    def storage_account(self):
        """Gets the storage_account of this V1WasbType.  # noqa: E501


        :return: The storage_account of this V1WasbType.  # noqa: E501
        :rtype: str
        """
        return self._storage_account

    @storage_account.setter
    def storage_account(self, storage_account):
        """Sets the storage_account of this V1WasbType.


        :param storage_account: The storage_account of this V1WasbType.  # noqa: E501
        :type storage_account: str
        """

        self._storage_account = storage_account

    @property
    def path(self):
        """Gets the path of this V1WasbType.  # noqa: E501


        :return: The path of this V1WasbType.  # noqa: E501
        :rtype: bool
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this V1WasbType.


        :param path: The path of this V1WasbType.  # noqa: E501
        :type path: bool
        """

        self._path = path

    def to_dict(self, serialize=False):
        """Returns the model properties as a dict"""
        result = {}

        def convert(x):
            if hasattr(x, "to_dict"):
                args = getfullargspec(x.to_dict).args
                if len(args) == 1:
                    return x.to_dict()
                else:
                    return x.to_dict(serialize)
            else:
                return x

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            attr = self.attribute_map.get(attr, attr) if serialize else attr
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: convert(x),
                    value
                ))
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], convert(item[1])),
                    value.items()
                ))
            else:
                result[attr] = convert(value)

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, V1WasbType):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1WasbType):
            return True

        return self.to_dict() != other.to_dict()
