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


class V1MXJob(object):
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
        'clean_pod_policy': 'V1CleanPodPolicy',
        'scheduling_policy': 'V1SchedulingPolicy',
        'mode': 'MXJobMode',
        'scheduler': 'V1KFReplica',
        'server': 'V1KFReplica',
        'worker': 'V1KFReplica',
        'tuner_tracker': 'V1KFReplica',
        'tuner_server': 'V1KFReplica',
        'tuner': 'V1KFReplica'
    }

    attribute_map = {
        'kind': 'kind',
        'clean_pod_policy': 'cleanPodPolicy',
        'scheduling_policy': 'schedulingPolicy',
        'mode': 'mode',
        'scheduler': 'scheduler',
        'server': 'server',
        'worker': 'worker',
        'tuner_tracker': 'tuner_tracker',
        'tuner_server': 'tuner_server',
        'tuner': 'tuner'
    }

    def __init__(self, kind='mxjob', clean_pod_policy=None, scheduling_policy=None, mode=None, scheduler=None, server=None, worker=None, tuner_tracker=None, tuner_server=None, tuner=None, local_vars_configuration=None):  # noqa: E501
        """V1MXJob - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration.get_default_copy()
        self.local_vars_configuration = local_vars_configuration

        self._kind = None
        self._clean_pod_policy = None
        self._scheduling_policy = None
        self._mode = None
        self._scheduler = None
        self._server = None
        self._worker = None
        self._tuner_tracker = None
        self._tuner_server = None
        self._tuner = None
        self.discriminator = None

        if kind is not None:
            self.kind = kind
        if clean_pod_policy is not None:
            self.clean_pod_policy = clean_pod_policy
        if scheduling_policy is not None:
            self.scheduling_policy = scheduling_policy
        if mode is not None:
            self.mode = mode
        if scheduler is not None:
            self.scheduler = scheduler
        if server is not None:
            self.server = server
        if worker is not None:
            self.worker = worker
        if tuner_tracker is not None:
            self.tuner_tracker = tuner_tracker
        if tuner_server is not None:
            self.tuner_server = tuner_server
        if tuner is not None:
            self.tuner = tuner

    @property
    def kind(self):
        """Gets the kind of this V1MXJob.  # noqa: E501


        :return: The kind of this V1MXJob.  # noqa: E501
        :rtype: str
        """
        return self._kind

    @kind.setter
    def kind(self, kind):
        """Sets the kind of this V1MXJob.


        :param kind: The kind of this V1MXJob.  # noqa: E501
        :type kind: str
        """

        self._kind = kind

    @property
    def clean_pod_policy(self):
        """Gets the clean_pod_policy of this V1MXJob.  # noqa: E501


        :return: The clean_pod_policy of this V1MXJob.  # noqa: E501
        :rtype: V1CleanPodPolicy
        """
        return self._clean_pod_policy

    @clean_pod_policy.setter
    def clean_pod_policy(self, clean_pod_policy):
        """Sets the clean_pod_policy of this V1MXJob.


        :param clean_pod_policy: The clean_pod_policy of this V1MXJob.  # noqa: E501
        :type clean_pod_policy: V1CleanPodPolicy
        """

        self._clean_pod_policy = clean_pod_policy

    @property
    def scheduling_policy(self):
        """Gets the scheduling_policy of this V1MXJob.  # noqa: E501


        :return: The scheduling_policy of this V1MXJob.  # noqa: E501
        :rtype: V1SchedulingPolicy
        """
        return self._scheduling_policy

    @scheduling_policy.setter
    def scheduling_policy(self, scheduling_policy):
        """Sets the scheduling_policy of this V1MXJob.


        :param scheduling_policy: The scheduling_policy of this V1MXJob.  # noqa: E501
        :type scheduling_policy: V1SchedulingPolicy
        """

        self._scheduling_policy = scheduling_policy

    @property
    def mode(self):
        """Gets the mode of this V1MXJob.  # noqa: E501


        :return: The mode of this V1MXJob.  # noqa: E501
        :rtype: MXJobMode
        """
        return self._mode

    @mode.setter
    def mode(self, mode):
        """Sets the mode of this V1MXJob.


        :param mode: The mode of this V1MXJob.  # noqa: E501
        :type mode: MXJobMode
        """

        self._mode = mode

    @property
    def scheduler(self):
        """Gets the scheduler of this V1MXJob.  # noqa: E501


        :return: The scheduler of this V1MXJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._scheduler

    @scheduler.setter
    def scheduler(self, scheduler):
        """Sets the scheduler of this V1MXJob.


        :param scheduler: The scheduler of this V1MXJob.  # noqa: E501
        :type scheduler: V1KFReplica
        """

        self._scheduler = scheduler

    @property
    def server(self):
        """Gets the server of this V1MXJob.  # noqa: E501


        :return: The server of this V1MXJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._server

    @server.setter
    def server(self, server):
        """Sets the server of this V1MXJob.


        :param server: The server of this V1MXJob.  # noqa: E501
        :type server: V1KFReplica
        """

        self._server = server

    @property
    def worker(self):
        """Gets the worker of this V1MXJob.  # noqa: E501


        :return: The worker of this V1MXJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._worker

    @worker.setter
    def worker(self, worker):
        """Sets the worker of this V1MXJob.


        :param worker: The worker of this V1MXJob.  # noqa: E501
        :type worker: V1KFReplica
        """

        self._worker = worker

    @property
    def tuner_tracker(self):
        """Gets the tuner_tracker of this V1MXJob.  # noqa: E501


        :return: The tuner_tracker of this V1MXJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._tuner_tracker

    @tuner_tracker.setter
    def tuner_tracker(self, tuner_tracker):
        """Sets the tuner_tracker of this V1MXJob.


        :param tuner_tracker: The tuner_tracker of this V1MXJob.  # noqa: E501
        :type tuner_tracker: V1KFReplica
        """

        self._tuner_tracker = tuner_tracker

    @property
    def tuner_server(self):
        """Gets the tuner_server of this V1MXJob.  # noqa: E501


        :return: The tuner_server of this V1MXJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._tuner_server

    @tuner_server.setter
    def tuner_server(self, tuner_server):
        """Sets the tuner_server of this V1MXJob.


        :param tuner_server: The tuner_server of this V1MXJob.  # noqa: E501
        :type tuner_server: V1KFReplica
        """

        self._tuner_server = tuner_server

    @property
    def tuner(self):
        """Gets the tuner of this V1MXJob.  # noqa: E501


        :return: The tuner of this V1MXJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._tuner

    @tuner.setter
    def tuner(self, tuner):
        """Sets the tuner of this V1MXJob.


        :param tuner: The tuner of this V1MXJob.  # noqa: E501
        :type tuner: V1KFReplica
        """

        self._tuner = tuner

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
        if not isinstance(other, V1MXJob):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1MXJob):
            return True

        return self.to_dict() != other.to_dict()
