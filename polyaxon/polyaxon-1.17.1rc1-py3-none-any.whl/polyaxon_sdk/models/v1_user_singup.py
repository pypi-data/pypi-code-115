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


class V1UserSingup(object):
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
        'username': 'str',
        'email': 'str',
        'organization': 'str',
        'password': 'str',
        'invitation_key': 'str'
    }

    attribute_map = {
        'username': 'username',
        'email': 'email',
        'organization': 'organization',
        'password': 'password',
        'invitation_key': 'invitation_key'
    }

    def __init__(self, username=None, email=None, organization=None, password=None, invitation_key=None, local_vars_configuration=None):  # noqa: E501
        """V1UserSingup - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration.get_default_copy()
        self.local_vars_configuration = local_vars_configuration

        self._username = None
        self._email = None
        self._organization = None
        self._password = None
        self._invitation_key = None
        self.discriminator = None

        if username is not None:
            self.username = username
        if email is not None:
            self.email = email
        if organization is not None:
            self.organization = organization
        if password is not None:
            self.password = password
        if invitation_key is not None:
            self.invitation_key = invitation_key

    @property
    def username(self):
        """Gets the username of this V1UserSingup.  # noqa: E501


        :return: The username of this V1UserSingup.  # noqa: E501
        :rtype: str
        """
        return self._username

    @username.setter
    def username(self, username):
        """Sets the username of this V1UserSingup.


        :param username: The username of this V1UserSingup.  # noqa: E501
        :type username: str
        """

        self._username = username

    @property
    def email(self):
        """Gets the email of this V1UserSingup.  # noqa: E501


        :return: The email of this V1UserSingup.  # noqa: E501
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, email):
        """Sets the email of this V1UserSingup.


        :param email: The email of this V1UserSingup.  # noqa: E501
        :type email: str
        """

        self._email = email

    @property
    def organization(self):
        """Gets the organization of this V1UserSingup.  # noqa: E501


        :return: The organization of this V1UserSingup.  # noqa: E501
        :rtype: str
        """
        return self._organization

    @organization.setter
    def organization(self, organization):
        """Sets the organization of this V1UserSingup.


        :param organization: The organization of this V1UserSingup.  # noqa: E501
        :type organization: str
        """

        self._organization = organization

    @property
    def password(self):
        """Gets the password of this V1UserSingup.  # noqa: E501


        :return: The password of this V1UserSingup.  # noqa: E501
        :rtype: str
        """
        return self._password

    @password.setter
    def password(self, password):
        """Sets the password of this V1UserSingup.


        :param password: The password of this V1UserSingup.  # noqa: E501
        :type password: str
        """

        self._password = password

    @property
    def invitation_key(self):
        """Gets the invitation_key of this V1UserSingup.  # noqa: E501


        :return: The invitation_key of this V1UserSingup.  # noqa: E501
        :rtype: str
        """
        return self._invitation_key

    @invitation_key.setter
    def invitation_key(self, invitation_key):
        """Sets the invitation_key of this V1UserSingup.


        :param invitation_key: The invitation_key of this V1UserSingup.  # noqa: E501
        :type invitation_key: str
        """

        self._invitation_key = invitation_key

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
        if not isinstance(other, V1UserSingup):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1UserSingup):
            return True

        return self.to_dict() != other.to_dict()
