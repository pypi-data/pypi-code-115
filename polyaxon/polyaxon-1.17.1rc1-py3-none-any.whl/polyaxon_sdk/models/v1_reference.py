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


class V1Reference(object):
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
        'hub_ref': 'V1HubRef',
        'dag_ref': 'V1DagRef',
        'url_ref': 'V1UrlRef',
        'path_ref': 'V1PathRef'
    }

    attribute_map = {
        'hub_ref': 'hubRef',
        'dag_ref': 'dagRef',
        'url_ref': 'urlRef',
        'path_ref': 'pathRef'
    }

    def __init__(self, hub_ref=None, dag_ref=None, url_ref=None, path_ref=None, local_vars_configuration=None):  # noqa: E501
        """V1Reference - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration.get_default_copy()
        self.local_vars_configuration = local_vars_configuration

        self._hub_ref = None
        self._dag_ref = None
        self._url_ref = None
        self._path_ref = None
        self.discriminator = None

        if hub_ref is not None:
            self.hub_ref = hub_ref
        if dag_ref is not None:
            self.dag_ref = dag_ref
        if url_ref is not None:
            self.url_ref = url_ref
        if path_ref is not None:
            self.path_ref = path_ref

    @property
    def hub_ref(self):
        """Gets the hub_ref of this V1Reference.  # noqa: E501


        :return: The hub_ref of this V1Reference.  # noqa: E501
        :rtype: V1HubRef
        """
        return self._hub_ref

    @hub_ref.setter
    def hub_ref(self, hub_ref):
        """Sets the hub_ref of this V1Reference.


        :param hub_ref: The hub_ref of this V1Reference.  # noqa: E501
        :type hub_ref: V1HubRef
        """

        self._hub_ref = hub_ref

    @property
    def dag_ref(self):
        """Gets the dag_ref of this V1Reference.  # noqa: E501


        :return: The dag_ref of this V1Reference.  # noqa: E501
        :rtype: V1DagRef
        """
        return self._dag_ref

    @dag_ref.setter
    def dag_ref(self, dag_ref):
        """Sets the dag_ref of this V1Reference.


        :param dag_ref: The dag_ref of this V1Reference.  # noqa: E501
        :type dag_ref: V1DagRef
        """

        self._dag_ref = dag_ref

    @property
    def url_ref(self):
        """Gets the url_ref of this V1Reference.  # noqa: E501


        :return: The url_ref of this V1Reference.  # noqa: E501
        :rtype: V1UrlRef
        """
        return self._url_ref

    @url_ref.setter
    def url_ref(self, url_ref):
        """Sets the url_ref of this V1Reference.


        :param url_ref: The url_ref of this V1Reference.  # noqa: E501
        :type url_ref: V1UrlRef
        """

        self._url_ref = url_ref

    @property
    def path_ref(self):
        """Gets the path_ref of this V1Reference.  # noqa: E501


        :return: The path_ref of this V1Reference.  # noqa: E501
        :rtype: V1PathRef
        """
        return self._path_ref

    @path_ref.setter
    def path_ref(self, path_ref):
        """Sets the path_ref of this V1Reference.


        :param path_ref: The path_ref of this V1Reference.  # noqa: E501
        :type path_ref: V1PathRef
        """

        self._path_ref = path_ref

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
        if not isinstance(other, V1Reference):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1Reference):
            return True

        return self.to_dict() != other.to_dict()
