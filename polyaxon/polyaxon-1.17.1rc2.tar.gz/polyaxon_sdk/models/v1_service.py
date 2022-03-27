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


class V1Service(object):
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
        'kind': 'str',
        'environment': 'V1Environment',
        'connections': 'list[str]',
        'volumes': 'list[V1Volume]',
        'init': 'list[V1Init]',
        'sidecars': 'list[V1Container]',
        'container': 'V1Container',
        'ports': 'list[int]',
        'rewrite_path': 'bool',
        'is_external': 'bool',
        'replicas': 'int'
    }

    attribute_map = {
        'kind': 'kind',
        'environment': 'environment',
        'connections': 'connections',
        'volumes': 'volumes',
        'init': 'init',
        'sidecars': 'sidecars',
        'container': 'container',
        'ports': 'ports',
        'rewrite_path': 'rewritePath',
        'is_external': 'isExternal',
        'replicas': 'replicas'
    }

    def __init__(self, kind='service', environment=None, connections=None, volumes=None, init=None, sidecars=None, container=None, ports=None, rewrite_path=None, is_external=None, replicas=None, local_vars_configuration=None):  # noqa: E501
        """V1Service - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration.get_default_copy()
        self.local_vars_configuration = local_vars_configuration

        self._kind = None
        self._environment = None
        self._connections = None
        self._volumes = None
        self._init = None
        self._sidecars = None
        self._container = None
        self._ports = None
        self._rewrite_path = None
        self._is_external = None
        self._replicas = None
        self.discriminator = None

        if kind is not None:
            self.kind = kind
        if environment is not None:
            self.environment = environment
        if connections is not None:
            self.connections = connections
        if volumes is not None:
            self.volumes = volumes
        if init is not None:
            self.init = init
        if sidecars is not None:
            self.sidecars = sidecars
        if container is not None:
            self.container = container
        if ports is not None:
            self.ports = ports
        if rewrite_path is not None:
            self.rewrite_path = rewrite_path
        if is_external is not None:
            self.is_external = is_external
        if replicas is not None:
            self.replicas = replicas

    @property
    def kind(self):
        """Gets the kind of this V1Service.  # noqa: E501


        :return: The kind of this V1Service.  # noqa: E501
        :rtype: str
        """
        return self._kind

    @kind.setter
    def kind(self, kind):
        """Sets the kind of this V1Service.


        :param kind: The kind of this V1Service.  # noqa: E501
        :type kind: str
        """

        self._kind = kind

    @property
    def environment(self):
        """Gets the environment of this V1Service.  # noqa: E501


        :return: The environment of this V1Service.  # noqa: E501
        :rtype: V1Environment
        """
        return self._environment

    @environment.setter
    def environment(self, environment):
        """Sets the environment of this V1Service.


        :param environment: The environment of this V1Service.  # noqa: E501
        :type environment: V1Environment
        """

        self._environment = environment

    @property
    def connections(self):
        """Gets the connections of this V1Service.  # noqa: E501


        :return: The connections of this V1Service.  # noqa: E501
        :rtype: list[str]
        """
        return self._connections

    @connections.setter
    def connections(self, connections):
        """Sets the connections of this V1Service.


        :param connections: The connections of this V1Service.  # noqa: E501
        :type connections: list[str]
        """

        self._connections = connections

    @property
    def volumes(self):
        """Gets the volumes of this V1Service.  # noqa: E501

        Volumes is a list of volumes that can be mounted.  # noqa: E501

        :return: The volumes of this V1Service.  # noqa: E501
        :rtype: list[V1Volume]
        """
        return self._volumes

    @volumes.setter
    def volumes(self, volumes):
        """Sets the volumes of this V1Service.

        Volumes is a list of volumes that can be mounted.  # noqa: E501

        :param volumes: The volumes of this V1Service.  # noqa: E501
        :type volumes: list[V1Volume]
        """

        self._volumes = volumes

    @property
    def init(self):
        """Gets the init of this V1Service.  # noqa: E501


        :return: The init of this V1Service.  # noqa: E501
        :rtype: list[V1Init]
        """
        return self._init

    @init.setter
    def init(self, init):
        """Sets the init of this V1Service.


        :param init: The init of this V1Service.  # noqa: E501
        :type init: list[V1Init]
        """

        self._init = init

    @property
    def sidecars(self):
        """Gets the sidecars of this V1Service.  # noqa: E501


        :return: The sidecars of this V1Service.  # noqa: E501
        :rtype: list[V1Container]
        """
        return self._sidecars

    @sidecars.setter
    def sidecars(self, sidecars):
        """Sets the sidecars of this V1Service.


        :param sidecars: The sidecars of this V1Service.  # noqa: E501
        :type sidecars: list[V1Container]
        """

        self._sidecars = sidecars

    @property
    def container(self):
        """Gets the container of this V1Service.  # noqa: E501


        :return: The container of this V1Service.  # noqa: E501
        :rtype: V1Container
        """
        return self._container

    @container.setter
    def container(self, container):
        """Sets the container of this V1Service.


        :param container: The container of this V1Service.  # noqa: E501
        :type container: V1Container
        """

        self._container = container

    @property
    def ports(self):
        """Gets the ports of this V1Service.  # noqa: E501


        :return: The ports of this V1Service.  # noqa: E501
        :rtype: list[int]
        """
        return self._ports

    @ports.setter
    def ports(self, ports):
        """Sets the ports of this V1Service.


        :param ports: The ports of this V1Service.  # noqa: E501
        :type ports: list[int]
        """

        self._ports = ports

    @property
    def rewrite_path(self):
        """Gets the rewrite_path of this V1Service.  # noqa: E501

        Rewrite path to remove polyaxon base url(i.e. /v1/services/namespace/owner/project/). Default is false, the service shoud handle a base url.  # noqa: E501

        :return: The rewrite_path of this V1Service.  # noqa: E501
        :rtype: bool
        """
        return self._rewrite_path

    @rewrite_path.setter
    def rewrite_path(self, rewrite_path):
        """Sets the rewrite_path of this V1Service.

        Rewrite path to remove polyaxon base url(i.e. /v1/services/namespace/owner/project/). Default is false, the service shoud handle a base url.  # noqa: E501

        :param rewrite_path: The rewrite_path of this V1Service.  # noqa: E501
        :type rewrite_path: bool
        """

        self._rewrite_path = rewrite_path

    @property
    def is_external(self):
        """Gets the is_external of this V1Service.  # noqa: E501

        Optional flag to signal to Polyaxon that this service should not go through Polyaxon's auth Default is false, the service will be controlled by Polyaxon's auth.  # noqa: E501

        :return: The is_external of this V1Service.  # noqa: E501
        :rtype: bool
        """
        return self._is_external

    @is_external.setter
    def is_external(self, is_external):
        """Sets the is_external of this V1Service.

        Optional flag to signal to Polyaxon that this service should not go through Polyaxon's auth Default is false, the service will be controlled by Polyaxon's auth.  # noqa: E501

        :param is_external: The is_external of this V1Service.  # noqa: E501
        :type is_external: bool
        """

        self._is_external = is_external

    @property
    def replicas(self):
        """Gets the replicas of this V1Service.  # noqa: E501


        :return: The replicas of this V1Service.  # noqa: E501
        :rtype: int
        """
        return self._replicas

    @replicas.setter
    def replicas(self, replicas):
        """Sets the replicas of this V1Service.


        :param replicas: The replicas of this V1Service.  # noqa: E501
        :type replicas: int
        """

        self._replicas = replicas

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
        if not isinstance(other, V1Service):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1Service):
            return True

        return self.to_dict() != other.to_dict()
