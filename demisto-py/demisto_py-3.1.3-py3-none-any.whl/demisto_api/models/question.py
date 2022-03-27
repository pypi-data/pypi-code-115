# coding: utf-8

"""
    Demisto API

    This is the public REST API to integrate with the demisto server. HTTP request can be sent using any HTTP-client.  For an example dedicated client take a look at: https://github.com/demisto/demisto-py.  Requests must include API-key that can be generated in the Demisto web client under 'Settings' -> 'Integrations' -> 'API keys'   Optimistic Locking and Versioning\\:  When using Demisto REST API, you will need to make sure to work on the latest version of the item (incident, entry, etc.), otherwise, you will get a DB version error (which not allow you to override a newer item). In addition, you can pass 'version\\: -1' to force data override (make sure that other users data might be lost).  Assume that Alice and Bob both read the same data from Demisto server, then they both changed the data, and then both tried to write the new versions back to the server. Whose changes should be saved? Alice’s? Bob’s? To solve this, each data item in Demisto has a numeric incremental version. If Alice saved an item with version 4 and Bob trying to save the same item with version 3, Demisto will rollback Bob request and returns a DB version conflict error. Bob will need to get the latest item and work on it so Alice work will not get lost.  Example request using 'curl'\\:  ``` curl 'https://hostname:443/incidents/search' -H 'content-type: application/json' -H 'accept: application/json' -H 'Authorization: <API Key goes here>' --data-binary '{\"filter\":{\"query\":\"-status:closed -category:job\",\"period\":{\"by\":\"day\",\"fromValue\":7}}}' --compressed ```  # noqa: E501

    OpenAPI spec version: 2.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


import pprint
import re  # noqa: F401

import six

from demisto_client.demisto_api.models.advance_arg import AdvanceArg  # noqa: F401,E501
from demisto_client.demisto_api.models.grid_column import GridColumn  # noqa: F401,E501


class Question(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'columns': 'list[GridColumn]',
        'default_rows': 'list[dict(str, object)]',
        'field_associated': 'str',
        'id': 'str',
        'label': 'str',
        'label_arg': 'AdvanceArg',
        'options': 'list[str]',
        'placeholder': 'str',
        'required': 'bool',
        'tooltip': 'str',
        'type': 'str'
    }

    attribute_map = {
        'columns': 'columns',
        'default_rows': 'defaultRows',
        'field_associated': 'fieldAssociated',
        'id': 'id',
        'label': 'label',
        'label_arg': 'labelArg',
        'options': 'options',
        'placeholder': 'placeholder',
        'required': 'required',
        'tooltip': 'tooltip',
        'type': 'type'
    }

    def __init__(self, columns=None, default_rows=None, field_associated=None, id=None, label=None, label_arg=None, options=None, placeholder=None, required=None, tooltip=None, type=None):  # noqa: E501
        """Question - a model defined in Swagger"""  # noqa: E501

        self._columns = None
        self._default_rows = None
        self._field_associated = None
        self._id = None
        self._label = None
        self._label_arg = None
        self._options = None
        self._placeholder = None
        self._required = None
        self._tooltip = None
        self._type = None
        self.discriminator = None

        if columns is not None:
            self.columns = columns
        if default_rows is not None:
            self.default_rows = default_rows
        if field_associated is not None:
            self.field_associated = field_associated
        if id is not None:
            self.id = id
        if label is not None:
            self.label = label
        if label_arg is not None:
            self.label_arg = label_arg
        if options is not None:
            self.options = options
        if placeholder is not None:
            self.placeholder = placeholder
        if required is not None:
            self.required = required
        if tooltip is not None:
            self.tooltip = tooltip
        if type is not None:
            self.type = type

    @property
    def columns(self):
        """Gets the columns of this Question.  # noqa: E501


        :return: The columns of this Question.  # noqa: E501
        :rtype: list[GridColumn]
        """
        return self._columns

    @columns.setter
    def columns(self, columns):
        """Sets the columns of this Question.


        :param columns: The columns of this Question.  # noqa: E501
        :type: list[GridColumn]
        """

        self._columns = columns

    @property
    def default_rows(self):
        """Gets the default_rows of this Question.  # noqa: E501


        :return: The default_rows of this Question.  # noqa: E501
        :rtype: list[dict(str, object)]
        """
        return self._default_rows

    @default_rows.setter
    def default_rows(self, default_rows):
        """Sets the default_rows of this Question.


        :param default_rows: The default_rows of this Question.  # noqa: E501
        :type: list[dict(str, object)]
        """

        self._default_rows = default_rows

    @property
    def field_associated(self):
        """Gets the field_associated of this Question.  # noqa: E501


        :return: The field_associated of this Question.  # noqa: E501
        :rtype: str
        """
        return self._field_associated

    @field_associated.setter
    def field_associated(self, field_associated):
        """Sets the field_associated of this Question.


        :param field_associated: The field_associated of this Question.  # noqa: E501
        :type: str
        """

        self._field_associated = field_associated

    @property
    def id(self):
        """Gets the id of this Question.  # noqa: E501


        :return: The id of this Question.  # noqa: E501
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this Question.


        :param id: The id of this Question.  # noqa: E501
        :type: str
        """

        self._id = id

    @property
    def label(self):
        """Gets the label of this Question.  # noqa: E501


        :return: The label of this Question.  # noqa: E501
        :rtype: str
        """
        return self._label

    @label.setter
    def label(self, label):
        """Sets the label of this Question.


        :param label: The label of this Question.  # noqa: E501
        :type: str
        """

        self._label = label

    @property
    def label_arg(self):
        """Gets the label_arg of this Question.  # noqa: E501


        :return: The label_arg of this Question.  # noqa: E501
        :rtype: AdvanceArg
        """
        return self._label_arg

    @label_arg.setter
    def label_arg(self, label_arg):
        """Sets the label_arg of this Question.


        :param label_arg: The label_arg of this Question.  # noqa: E501
        :type: AdvanceArg
        """

        self._label_arg = label_arg

    @property
    def options(self):
        """Gets the options of this Question.  # noqa: E501


        :return: The options of this Question.  # noqa: E501
        :rtype: list[str]
        """
        return self._options

    @options.setter
    def options(self, options):
        """Sets the options of this Question.


        :param options: The options of this Question.  # noqa: E501
        :type: list[str]
        """

        self._options = options

    @property
    def placeholder(self):
        """Gets the placeholder of this Question.  # noqa: E501


        :return: The placeholder of this Question.  # noqa: E501
        :rtype: str
        """
        return self._placeholder

    @placeholder.setter
    def placeholder(self, placeholder):
        """Sets the placeholder of this Question.


        :param placeholder: The placeholder of this Question.  # noqa: E501
        :type: str
        """

        self._placeholder = placeholder

    @property
    def required(self):
        """Gets the required of this Question.  # noqa: E501


        :return: The required of this Question.  # noqa: E501
        :rtype: bool
        """
        return self._required

    @required.setter
    def required(self, required):
        """Sets the required of this Question.


        :param required: The required of this Question.  # noqa: E501
        :type: bool
        """

        self._required = required

    @property
    def tooltip(self):
        """Gets the tooltip of this Question.  # noqa: E501


        :return: The tooltip of this Question.  # noqa: E501
        :rtype: str
        """
        return self._tooltip

    @tooltip.setter
    def tooltip(self, tooltip):
        """Sets the tooltip of this Question.


        :param tooltip: The tooltip of this Question.  # noqa: E501
        :type: str
        """

        self._tooltip = tooltip

    @property
    def type(self):
        """Gets the type of this Question.  # noqa: E501


        :return: The type of this Question.  # noqa: E501
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this Question.


        :param type: The type of this Question.  # noqa: E501
        :type: str
        """

        self._type = type

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(Question, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, Question):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
