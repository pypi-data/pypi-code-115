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


class V1Hyperopt(object):
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
        'algorithm': 'V1HyperoptAlgorithms',
        'params': 'dict(str, object)',
        'num_runs': 'int',
        'max_iterations': 'int',
        'metric': 'V1OptimizationMetric',
        'seed': 'int',
        'concurrency': 'int',
        'tuner': 'V1Tuner',
        'early_stopping': 'list[object]'
    }

    attribute_map = {
        'kind': 'kind',
        'algorithm': 'algorithm',
        'params': 'params',
        'num_runs': 'numRuns',
        'max_iterations': 'maxIterations',
        'metric': 'metric',
        'seed': 'seed',
        'concurrency': 'concurrency',
        'tuner': 'tuner',
        'early_stopping': 'earlyStopping'
    }

    def __init__(self, kind='hyperopt', algorithm=None, params=None, num_runs=None, max_iterations=None, metric=None, seed=None, concurrency=None, tuner=None, early_stopping=None, local_vars_configuration=None):  # noqa: E501
        """V1Hyperopt - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration.get_default_copy()
        self.local_vars_configuration = local_vars_configuration

        self._kind = None
        self._algorithm = None
        self._params = None
        self._num_runs = None
        self._max_iterations = None
        self._metric = None
        self._seed = None
        self._concurrency = None
        self._tuner = None
        self._early_stopping = None
        self.discriminator = None

        if kind is not None:
            self.kind = kind
        if algorithm is not None:
            self.algorithm = algorithm
        if params is not None:
            self.params = params
        if num_runs is not None:
            self.num_runs = num_runs
        if max_iterations is not None:
            self.max_iterations = max_iterations
        if metric is not None:
            self.metric = metric
        if seed is not None:
            self.seed = seed
        if concurrency is not None:
            self.concurrency = concurrency
        if tuner is not None:
            self.tuner = tuner
        if early_stopping is not None:
            self.early_stopping = early_stopping

    @property
    def kind(self):
        """Gets the kind of this V1Hyperopt.  # noqa: E501


        :return: The kind of this V1Hyperopt.  # noqa: E501
        :rtype: str
        """
        return self._kind

    @kind.setter
    def kind(self, kind):
        """Sets the kind of this V1Hyperopt.


        :param kind: The kind of this V1Hyperopt.  # noqa: E501
        :type kind: str
        """

        self._kind = kind

    @property
    def algorithm(self):
        """Gets the algorithm of this V1Hyperopt.  # noqa: E501


        :return: The algorithm of this V1Hyperopt.  # noqa: E501
        :rtype: V1HyperoptAlgorithms
        """
        return self._algorithm

    @algorithm.setter
    def algorithm(self, algorithm):
        """Sets the algorithm of this V1Hyperopt.


        :param algorithm: The algorithm of this V1Hyperopt.  # noqa: E501
        :type algorithm: V1HyperoptAlgorithms
        """

        self._algorithm = algorithm

    @property
    def params(self):
        """Gets the params of this V1Hyperopt.  # noqa: E501


        :return: The params of this V1Hyperopt.  # noqa: E501
        :rtype: dict(str, object)
        """
        return self._params

    @params.setter
    def params(self, params):
        """Sets the params of this V1Hyperopt.


        :param params: The params of this V1Hyperopt.  # noqa: E501
        :type params: dict(str, object)
        """

        self._params = params

    @property
    def num_runs(self):
        """Gets the num_runs of this V1Hyperopt.  # noqa: E501


        :return: The num_runs of this V1Hyperopt.  # noqa: E501
        :rtype: int
        """
        return self._num_runs

    @num_runs.setter
    def num_runs(self, num_runs):
        """Sets the num_runs of this V1Hyperopt.


        :param num_runs: The num_runs of this V1Hyperopt.  # noqa: E501
        :type num_runs: int
        """

        self._num_runs = num_runs

    @property
    def max_iterations(self):
        """Gets the max_iterations of this V1Hyperopt.  # noqa: E501


        :return: The max_iterations of this V1Hyperopt.  # noqa: E501
        :rtype: int
        """
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, max_iterations):
        """Sets the max_iterations of this V1Hyperopt.


        :param max_iterations: The max_iterations of this V1Hyperopt.  # noqa: E501
        :type max_iterations: int
        """

        self._max_iterations = max_iterations

    @property
    def metric(self):
        """Gets the metric of this V1Hyperopt.  # noqa: E501


        :return: The metric of this V1Hyperopt.  # noqa: E501
        :rtype: V1OptimizationMetric
        """
        return self._metric

    @metric.setter
    def metric(self, metric):
        """Sets the metric of this V1Hyperopt.


        :param metric: The metric of this V1Hyperopt.  # noqa: E501
        :type metric: V1OptimizationMetric
        """

        self._metric = metric

    @property
    def seed(self):
        """Gets the seed of this V1Hyperopt.  # noqa: E501


        :return: The seed of this V1Hyperopt.  # noqa: E501
        :rtype: int
        """
        return self._seed

    @seed.setter
    def seed(self, seed):
        """Sets the seed of this V1Hyperopt.


        :param seed: The seed of this V1Hyperopt.  # noqa: E501
        :type seed: int
        """

        self._seed = seed

    @property
    def concurrency(self):
        """Gets the concurrency of this V1Hyperopt.  # noqa: E501


        :return: The concurrency of this V1Hyperopt.  # noqa: E501
        :rtype: int
        """
        return self._concurrency

    @concurrency.setter
    def concurrency(self, concurrency):
        """Sets the concurrency of this V1Hyperopt.


        :param concurrency: The concurrency of this V1Hyperopt.  # noqa: E501
        :type concurrency: int
        """

        self._concurrency = concurrency

    @property
    def tuner(self):
        """Gets the tuner of this V1Hyperopt.  # noqa: E501


        :return: The tuner of this V1Hyperopt.  # noqa: E501
        :rtype: V1Tuner
        """
        return self._tuner

    @tuner.setter
    def tuner(self, tuner):
        """Sets the tuner of this V1Hyperopt.


        :param tuner: The tuner of this V1Hyperopt.  # noqa: E501
        :type tuner: V1Tuner
        """

        self._tuner = tuner

    @property
    def early_stopping(self):
        """Gets the early_stopping of this V1Hyperopt.  # noqa: E501


        :return: The early_stopping of this V1Hyperopt.  # noqa: E501
        :rtype: list[object]
        """
        return self._early_stopping

    @early_stopping.setter
    def early_stopping(self, early_stopping):
        """Sets the early_stopping of this V1Hyperopt.


        :param early_stopping: The early_stopping of this V1Hyperopt.  # noqa: E501
        :type early_stopping: list[object]
        """

        self._early_stopping = early_stopping

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
        if not isinstance(other, V1Hyperopt):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1Hyperopt):
            return True

        return self.to_dict() != other.to_dict()
