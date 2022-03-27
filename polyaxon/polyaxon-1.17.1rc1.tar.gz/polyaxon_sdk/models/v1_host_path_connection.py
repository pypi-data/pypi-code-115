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


class V1HostPathConnection(object):
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
        'host_path': 'str',
        'mount_path': 'str',
        'read_only': 'bool',
        'kind': 'object'
    }

    attribute_map = {
        'host_path': 'hostPath',
        'mount_path': 'mountPath',
        'read_only': 'readOnly',
        'kind': 'kind'
    }

    def __init__(self, host_path=None, mount_path=None, read_only=None, kind=None, local_vars_configuration=None):  # noqa: E501
        """V1HostPathConnection - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration.get_default_copy()
        self.local_vars_configuration = local_vars_configuration

        self._host_path = None
        self._mount_path = None
        self._read_only = None
        self._kind = None
        self.discriminator = None

        if host_path is not None:
            self.host_path = host_path
        if mount_path is not None:
            self.mount_path = mount_path
        if read_only is not None:
            self.read_only = read_only
        if kind is not None:
            self.kind = kind

    @property
    def host_path(self):
        """Gets the host_path of this V1HostPathConnection.  # noqa: E501


        :return: The host_path of this V1HostPathConnection.  # noqa: E501
        :rtype: str
        """
        return self._host_path

    @host_path.setter
    def host_path(self, host_path):
        """Sets the host_path of this V1HostPathConnection.


        :param host_path: The host_path of this V1HostPathConnection.  # noqa: E501
        :type host_path: str
        """

        self._host_path = host_path

    @property
    def mount_path(self):
        """Gets the mount_path of this V1HostPathConnection.  # noqa: E501


        :return: The mount_path of this V1HostPathConnection.  # noqa: E501
        :rtype: str
        """
        return self._mount_path

    @mount_path.setter
    def mount_path(self, mount_path):
        """Sets the mount_path of this V1HostPathConnection.


        :param mount_path: The mount_path of this V1HostPathConnection.  # noqa: E501
        :type mount_path: str
        """

        self._mount_path = mount_path

    @property
    def read_only(self):
        """Gets the read_only of this V1HostPathConnection.  # noqa: E501


        :return: The read_only of this V1HostPathConnection.  # noqa: E501
        :rtype: bool
        """
        return self._read_only

    @read_only.setter
    def read_only(self, read_only):
        """Sets the read_only of this V1HostPathConnection.


        :param read_only: The read_only of this V1HostPathConnection.  # noqa: E501
        :type read_only: bool
        """

        self._read_only = read_only

    @property
    def kind(self):
        """Gets the kind of this V1HostPathConnection.  # noqa: E501


        :return: The kind of this V1HostPathConnection.  # noqa: E501
        :rtype: object
        """
        return self._kind

    @kind.setter
    def kind(self, kind):
        """Sets the kind of this V1HostPathConnection.


        :param kind: The kind of this V1HostPathConnection.  # noqa: E501
        :type kind: object
        """

        self._kind = kind

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
        if not isinstance(other, V1HostPathConnection):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1HostPathConnection):
            return True

        return self.to_dict() != other.to_dict()
