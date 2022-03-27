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

from demisto_client.demisto_api.models.investigation_status import InvestigationStatus  # noqa: F401,E501
from demisto_client.demisto_api.models.investigation_type import InvestigationType  # noqa: F401,E501
from demisto_client.demisto_api.models.run_status import RunStatus  # noqa: F401,E501
from demisto_client.demisto_api.models.system import System  # noqa: F401,E501


class Investigation(object):
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
        'shard_id': 'int',
        'category': 'str',
        'child_investigations': 'list[str]',
        'closed': 'datetime',
        'closing_user_id': 'str',
        'created': 'datetime',
        'creating_user_id': 'str',
        'details': 'str',
        'entitlements': 'list[str]',
        'entry_users': 'list[str]',
        'has_role': 'bool',
        'id': 'str',
        'is_child_investigation': 'bool',
        'last_open': 'datetime',
        'mirror_auto_close': 'dict(str, bool)',
        'mirror_types': 'dict(str, str)',
        'modified': 'datetime',
        'name': 'str',
        'open_duration': 'int',
        'parent_investigation': 'str',
        'persistent_entitlements': 'dict(str, str)',
        'previous_roles': 'list[str]',
        'raw_category': 'str',
        'reason': 'dict(str, str)',
        'roles': 'list[str]',
        'run_status': 'RunStatus',
        'slack_mirror_auto_close': 'bool',
        'slack_mirror_type': 'str',
        'sort_values': 'list[str]',
        'status': 'InvestigationStatus',
        'systems': 'list[System]',
        'tags': 'list[str]',
        'type': 'InvestigationType',
        'users': 'list[str]',
        'version': 'int'
    }

    attribute_map = {
        'shard_id': 'ShardID',
        'category': 'category',
        'child_investigations': 'childInvestigations',
        'closed': 'closed',
        'closing_user_id': 'closingUserId',
        'created': 'created',
        'creating_user_id': 'creatingUserId',
        'details': 'details',
        'entitlements': 'entitlements',
        'entry_users': 'entryUsers',
        'has_role': 'hasRole',
        'id': 'id',
        'is_child_investigation': 'isChildInvestigation',
        'last_open': 'lastOpen',
        'mirror_auto_close': 'mirrorAutoClose',
        'mirror_types': 'mirrorTypes',
        'modified': 'modified',
        'name': 'name',
        'open_duration': 'openDuration',
        'parent_investigation': 'parentInvestigation',
        'persistent_entitlements': 'persistentEntitlements',
        'previous_roles': 'previousRoles',
        'raw_category': 'rawCategory',
        'reason': 'reason',
        'roles': 'roles',
        'run_status': 'runStatus',
        'slack_mirror_auto_close': 'slackMirrorAutoClose',
        'slack_mirror_type': 'slackMirrorType',
        'sort_values': 'sortValues',
        'status': 'status',
        'systems': 'systems',
        'tags': 'tags',
        'type': 'type',
        'users': 'users',
        'version': 'version'
    }

    def __init__(self, shard_id=None, category=None, child_investigations=None, closed=None, closing_user_id=None, created=None, creating_user_id=None, details=None, entitlements=None, entry_users=None, has_role=None, id=None, is_child_investigation=None, last_open=None, mirror_auto_close=None, mirror_types=None, modified=None, name=None, open_duration=None, parent_investigation=None, persistent_entitlements=None, previous_roles=None, raw_category=None, reason=None, roles=None, run_status=None, slack_mirror_auto_close=None, slack_mirror_type=None, sort_values=None, status=None, systems=None, tags=None, type=None, users=None, version=None):  # noqa: E501
        """Investigation - a model defined in Swagger"""  # noqa: E501

        self._shard_id = None
        self._category = None
        self._child_investigations = None
        self._closed = None
        self._closing_user_id = None
        self._created = None
        self._creating_user_id = None
        self._details = None
        self._entitlements = None
        self._entry_users = None
        self._has_role = None
        self._id = None
        self._is_child_investigation = None
        self._last_open = None
        self._mirror_auto_close = None
        self._mirror_types = None
        self._modified = None
        self._name = None
        self._open_duration = None
        self._parent_investigation = None
        self._persistent_entitlements = None
        self._previous_roles = None
        self._raw_category = None
        self._reason = None
        self._roles = None
        self._run_status = None
        self._slack_mirror_auto_close = None
        self._slack_mirror_type = None
        self._sort_values = None
        self._status = None
        self._systems = None
        self._tags = None
        self._type = None
        self._users = None
        self._version = None
        self.discriminator = None

        if shard_id is not None:
            self.shard_id = shard_id
        if category is not None:
            self.category = category
        if child_investigations is not None:
            self.child_investigations = child_investigations
        if closed is not None:
            self.closed = closed
        if closing_user_id is not None:
            self.closing_user_id = closing_user_id
        if created is not None:
            self.created = created
        if creating_user_id is not None:
            self.creating_user_id = creating_user_id
        if details is not None:
            self.details = details
        if entitlements is not None:
            self.entitlements = entitlements
        if entry_users is not None:
            self.entry_users = entry_users
        if has_role is not None:
            self.has_role = has_role
        if id is not None:
            self.id = id
        if is_child_investigation is not None:
            self.is_child_investigation = is_child_investigation
        if last_open is not None:
            self.last_open = last_open
        if mirror_auto_close is not None:
            self.mirror_auto_close = mirror_auto_close
        if mirror_types is not None:
            self.mirror_types = mirror_types
        if modified is not None:
            self.modified = modified
        if name is not None:
            self.name = name
        if open_duration is not None:
            self.open_duration = open_duration
        if parent_investigation is not None:
            self.parent_investigation = parent_investigation
        if persistent_entitlements is not None:
            self.persistent_entitlements = persistent_entitlements
        if previous_roles is not None:
            self.previous_roles = previous_roles
        if raw_category is not None:
            self.raw_category = raw_category
        if reason is not None:
            self.reason = reason
        if roles is not None:
            self.roles = roles
        if run_status is not None:
            self.run_status = run_status
        if slack_mirror_auto_close is not None:
            self.slack_mirror_auto_close = slack_mirror_auto_close
        if slack_mirror_type is not None:
            self.slack_mirror_type = slack_mirror_type
        if sort_values is not None:
            self.sort_values = sort_values
        if status is not None:
            self.status = status
        if systems is not None:
            self.systems = systems
        if tags is not None:
            self.tags = tags
        if type is not None:
            self.type = type
        if users is not None:
            self.users = users
        if version is not None:
            self.version = version

    @property
    def shard_id(self):
        """Gets the shard_id of this Investigation.  # noqa: E501


        :return: The shard_id of this Investigation.  # noqa: E501
        :rtype: int
        """
        return self._shard_id

    @shard_id.setter
    def shard_id(self, shard_id):
        """Sets the shard_id of this Investigation.


        :param shard_id: The shard_id of this Investigation.  # noqa: E501
        :type: int
        """

        self._shard_id = shard_id

    @property
    def category(self):
        """Gets the category of this Investigation.  # noqa: E501

        Category of the investigation  # noqa: E501

        :return: The category of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._category

    @category.setter
    def category(self, category):
        """Sets the category of this Investigation.

        Category of the investigation  # noqa: E501

        :param category: The category of this Investigation.  # noqa: E501
        :type: str
        """

        self._category = category

    @property
    def child_investigations(self):
        """Gets the child_investigations of this Investigation.  # noqa: E501

        ChildInvestigations id's  # noqa: E501

        :return: The child_investigations of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._child_investigations

    @child_investigations.setter
    def child_investigations(self, child_investigations):
        """Sets the child_investigations of this Investigation.

        ChildInvestigations id's  # noqa: E501

        :param child_investigations: The child_investigations of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._child_investigations = child_investigations

    @property
    def closed(self):
        """Gets the closed of this Investigation.  # noqa: E501

        When was this closed  # noqa: E501

        :return: The closed of this Investigation.  # noqa: E501
        :rtype: datetime
        """
        return self._closed

    @closed.setter
    def closed(self, closed):
        """Sets the closed of this Investigation.

        When was this closed  # noqa: E501

        :param closed: The closed of this Investigation.  # noqa: E501
        :type: datetime
        """

        self._closed = closed

    @property
    def closing_user_id(self):
        """Gets the closing_user_id of this Investigation.  # noqa: E501

        The user ID that closed this investigation  # noqa: E501

        :return: The closing_user_id of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._closing_user_id

    @closing_user_id.setter
    def closing_user_id(self, closing_user_id):
        """Sets the closing_user_id of this Investigation.

        The user ID that closed this investigation  # noqa: E501

        :param closing_user_id: The closing_user_id of this Investigation.  # noqa: E501
        :type: str
        """

        self._closing_user_id = closing_user_id

    @property
    def created(self):
        """Gets the created of this Investigation.  # noqa: E501

        When was this created  # noqa: E501

        :return: The created of this Investigation.  # noqa: E501
        :rtype: datetime
        """
        return self._created

    @created.setter
    def created(self, created):
        """Sets the created of this Investigation.

        When was this created  # noqa: E501

        :param created: The created of this Investigation.  # noqa: E501
        :type: datetime
        """

        self._created = created

    @property
    def creating_user_id(self):
        """Gets the creating_user_id of this Investigation.  # noqa: E501

        The user ID that created this investigation  # noqa: E501

        :return: The creating_user_id of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._creating_user_id

    @creating_user_id.setter
    def creating_user_id(self, creating_user_id):
        """Sets the creating_user_id of this Investigation.

        The user ID that created this investigation  # noqa: E501

        :param creating_user_id: The creating_user_id of this Investigation.  # noqa: E501
        :type: str
        """

        self._creating_user_id = creating_user_id

    @property
    def details(self):
        """Gets the details of this Investigation.  # noqa: E501

        User defined free text details  # noqa: E501

        :return: The details of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._details

    @details.setter
    def details(self, details):
        """Sets the details of this Investigation.

        User defined free text details  # noqa: E501

        :param details: The details of this Investigation.  # noqa: E501
        :type: str
        """

        self._details = details

    @property
    def entitlements(self):
        """Gets the entitlements of this Investigation.  # noqa: E501

        One time entitlements  # noqa: E501

        :return: The entitlements of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._entitlements

    @entitlements.setter
    def entitlements(self, entitlements):
        """Sets the entitlements of this Investigation.

        One time entitlements  # noqa: E501

        :param entitlements: The entitlements of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._entitlements = entitlements

    @property
    def entry_users(self):
        """Gets the entry_users of this Investigation.  # noqa: E501

        EntryUsers  # noqa: E501

        :return: The entry_users of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._entry_users

    @entry_users.setter
    def entry_users(self, entry_users):
        """Sets the entry_users of this Investigation.

        EntryUsers  # noqa: E501

        :param entry_users: The entry_users of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._entry_users = entry_users

    @property
    def has_role(self):
        """Gets the has_role of this Investigation.  # noqa: E501

        Internal field to make queries on role faster  # noqa: E501

        :return: The has_role of this Investigation.  # noqa: E501
        :rtype: bool
        """
        return self._has_role

    @has_role.setter
    def has_role(self, has_role):
        """Sets the has_role of this Investigation.

        Internal field to make queries on role faster  # noqa: E501

        :param has_role: The has_role of this Investigation.  # noqa: E501
        :type: bool
        """

        self._has_role = has_role

    @property
    def id(self):
        """Gets the id of this Investigation.  # noqa: E501


        :return: The id of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this Investigation.


        :param id: The id of this Investigation.  # noqa: E501
        :type: str
        """

        self._id = id

    @property
    def is_child_investigation(self):
        """Gets the is_child_investigation of this Investigation.  # noqa: E501

        IsChildInvestigation  # noqa: E501

        :return: The is_child_investigation of this Investigation.  # noqa: E501
        :rtype: bool
        """
        return self._is_child_investigation

    @is_child_investigation.setter
    def is_child_investigation(self, is_child_investigation):
        """Sets the is_child_investigation of this Investigation.

        IsChildInvestigation  # noqa: E501

        :param is_child_investigation: The is_child_investigation of this Investigation.  # noqa: E501
        :type: bool
        """

        self._is_child_investigation = is_child_investigation

    @property
    def last_open(self):
        """Gets the last_open of this Investigation.  # noqa: E501


        :return: The last_open of this Investigation.  # noqa: E501
        :rtype: datetime
        """
        return self._last_open

    @last_open.setter
    def last_open(self, last_open):
        """Sets the last_open of this Investigation.


        :param last_open: The last_open of this Investigation.  # noqa: E501
        :type: datetime
        """

        self._last_open = last_open

    @property
    def mirror_auto_close(self):
        """Gets the mirror_auto_close of this Investigation.  # noqa: E501

        MirrorAutoClose will tell us to close the Chat Module channel if we close investigation  # noqa: E501

        :return: The mirror_auto_close of this Investigation.  # noqa: E501
        :rtype: dict(str, bool)
        """
        return self._mirror_auto_close

    @mirror_auto_close.setter
    def mirror_auto_close(self, mirror_auto_close):
        """Sets the mirror_auto_close of this Investigation.

        MirrorAutoClose will tell us to close the Chat Module channel if we close investigation  # noqa: E501

        :param mirror_auto_close: The mirror_auto_close of this Investigation.  # noqa: E501
        :type: dict(str, bool)
        """

        self._mirror_auto_close = mirror_auto_close

    @property
    def mirror_types(self):
        """Gets the mirror_types of this Investigation.  # noqa: E501

        MirrorTypes holds info about mirror direction and message type to be mirrored message type can be either 'all' or 'chat' direction can be either 'FromDemisto', 'ToDemisto' or 'Both' if this investigation is mirrored  # noqa: E501

        :return: The mirror_types of this Investigation.  # noqa: E501
        :rtype: dict(str, str)
        """
        return self._mirror_types

    @mirror_types.setter
    def mirror_types(self, mirror_types):
        """Sets the mirror_types of this Investigation.

        MirrorTypes holds info about mirror direction and message type to be mirrored message type can be either 'all' or 'chat' direction can be either 'FromDemisto', 'ToDemisto' or 'Both' if this investigation is mirrored  # noqa: E501

        :param mirror_types: The mirror_types of this Investigation.  # noqa: E501
        :type: dict(str, str)
        """

        self._mirror_types = mirror_types

    @property
    def modified(self):
        """Gets the modified of this Investigation.  # noqa: E501


        :return: The modified of this Investigation.  # noqa: E501
        :rtype: datetime
        """
        return self._modified

    @modified.setter
    def modified(self, modified):
        """Sets the modified of this Investigation.


        :param modified: The modified of this Investigation.  # noqa: E501
        :type: datetime
        """

        self._modified = modified

    @property
    def name(self):
        """Gets the name of this Investigation.  # noqa: E501

        The name of the investigation, which is unique to the project  # noqa: E501

        :return: The name of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this Investigation.

        The name of the investigation, which is unique to the project  # noqa: E501

        :param name: The name of this Investigation.  # noqa: E501
        :type: str
        """

        self._name = name

    @property
    def open_duration(self):
        """Gets the open_duration of this Investigation.  # noqa: E501

        Duration from open to close time  # noqa: E501

        :return: The open_duration of this Investigation.  # noqa: E501
        :rtype: int
        """
        return self._open_duration

    @open_duration.setter
    def open_duration(self, open_duration):
        """Sets the open_duration of this Investigation.

        Duration from open to close time  # noqa: E501

        :param open_duration: The open_duration of this Investigation.  # noqa: E501
        :type: int
        """

        self._open_duration = open_duration

    @property
    def parent_investigation(self):
        """Gets the parent_investigation of this Investigation.  # noqa: E501

        ParentInvestigation - parent id, in case this is a child investigation of another investigation  # noqa: E501

        :return: The parent_investigation of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._parent_investigation

    @parent_investigation.setter
    def parent_investigation(self, parent_investigation):
        """Sets the parent_investigation of this Investigation.

        ParentInvestigation - parent id, in case this is a child investigation of another investigation  # noqa: E501

        :param parent_investigation: The parent_investigation of this Investigation.  # noqa: E501
        :type: str
        """

        self._parent_investigation = parent_investigation

    @property
    def persistent_entitlements(self):
        """Gets the persistent_entitlements of this Investigation.  # noqa: E501

        Persistent entitlement per tag. Empty tag will also return an entitlement  # noqa: E501

        :return: The persistent_entitlements of this Investigation.  # noqa: E501
        :rtype: dict(str, str)
        """
        return self._persistent_entitlements

    @persistent_entitlements.setter
    def persistent_entitlements(self, persistent_entitlements):
        """Sets the persistent_entitlements of this Investigation.

        Persistent entitlement per tag. Empty tag will also return an entitlement  # noqa: E501

        :param persistent_entitlements: The persistent_entitlements of this Investigation.  # noqa: E501
        :type: dict(str, str)
        """

        self._persistent_entitlements = persistent_entitlements

    @property
    def previous_roles(self):
        """Gets the previous_roles of this Investigation.  # noqa: E501

        PreviousRoleName - do not change this field manually  # noqa: E501

        :return: The previous_roles of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._previous_roles

    @previous_roles.setter
    def previous_roles(self, previous_roles):
        """Sets the previous_roles of this Investigation.

        PreviousRoleName - do not change this field manually  # noqa: E501

        :param previous_roles: The previous_roles of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._previous_roles = previous_roles

    @property
    def raw_category(self):
        """Gets the raw_category of this Investigation.  # noqa: E501


        :return: The raw_category of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._raw_category

    @raw_category.setter
    def raw_category(self, raw_category):
        """Sets the raw_category of this Investigation.


        :param raw_category: The raw_category of this Investigation.  # noqa: E501
        :type: str
        """

        self._raw_category = raw_category

    @property
    def reason(self):
        """Gets the reason of this Investigation.  # noqa: E501

        The reason for the status (resolve)  # noqa: E501

        :return: The reason of this Investigation.  # noqa: E501
        :rtype: dict(str, str)
        """
        return self._reason

    @reason.setter
    def reason(self, reason):
        """Sets the reason of this Investigation.

        The reason for the status (resolve)  # noqa: E501

        :param reason: The reason of this Investigation.  # noqa: E501
        :type: dict(str, str)
        """

        self._reason = reason

    @property
    def roles(self):
        """Gets the roles of this Investigation.  # noqa: E501

        The role assigned to this investigation  # noqa: E501

        :return: The roles of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._roles

    @roles.setter
    def roles(self, roles):
        """Sets the roles of this Investigation.

        The role assigned to this investigation  # noqa: E501

        :param roles: The roles of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._roles = roles

    @property
    def run_status(self):
        """Gets the run_status of this Investigation.  # noqa: E501


        :return: The run_status of this Investigation.  # noqa: E501
        :rtype: RunStatus
        """
        return self._run_status

    @run_status.setter
    def run_status(self, run_status):
        """Sets the run_status of this Investigation.


        :param run_status: The run_status of this Investigation.  # noqa: E501
        :type: RunStatus
        """

        self._run_status = run_status

    @property
    def slack_mirror_auto_close(self):
        """Gets the slack_mirror_auto_close of this Investigation.  # noqa: E501

        DEPRECATED - DeprecatedSlackMirrorAutoClose will tell us to close the Slack channel if we close investigation  # noqa: E501

        :return: The slack_mirror_auto_close of this Investigation.  # noqa: E501
        :rtype: bool
        """
        return self._slack_mirror_auto_close

    @slack_mirror_auto_close.setter
    def slack_mirror_auto_close(self, slack_mirror_auto_close):
        """Sets the slack_mirror_auto_close of this Investigation.

        DEPRECATED - DeprecatedSlackMirrorAutoClose will tell us to close the Slack channel if we close investigation  # noqa: E501

        :param slack_mirror_auto_close: The slack_mirror_auto_close of this Investigation.  # noqa: E501
        :type: bool
        """

        self._slack_mirror_auto_close = slack_mirror_auto_close

    @property
    def slack_mirror_type(self):
        """Gets the slack_mirror_type of this Investigation.  # noqa: E501

        DEPRECATED - DeprecatedSlackMirrorType holds info about mirror direction and message type to be mirror message type can be either 'all' or 'chat' direction can be either 'demisto2Slack', 'slack2Demisto' or 'both' if this investigation is mirrored to Slack  # noqa: E501

        :return: The slack_mirror_type of this Investigation.  # noqa: E501
        :rtype: str
        """
        return self._slack_mirror_type

    @slack_mirror_type.setter
    def slack_mirror_type(self, slack_mirror_type):
        """Sets the slack_mirror_type of this Investigation.

        DEPRECATED - DeprecatedSlackMirrorType holds info about mirror direction and message type to be mirror message type can be either 'all' or 'chat' direction can be either 'demisto2Slack', 'slack2Demisto' or 'both' if this investigation is mirrored to Slack  # noqa: E501

        :param slack_mirror_type: The slack_mirror_type of this Investigation.  # noqa: E501
        :type: str
        """

        self._slack_mirror_type = slack_mirror_type

    @property
    def sort_values(self):
        """Gets the sort_values of this Investigation.  # noqa: E501


        :return: The sort_values of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._sort_values

    @sort_values.setter
    def sort_values(self, sort_values):
        """Sets the sort_values of this Investigation.


        :param sort_values: The sort_values of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._sort_values = sort_values

    @property
    def status(self):
        """Gets the status of this Investigation.  # noqa: E501


        :return: The status of this Investigation.  # noqa: E501
        :rtype: InvestigationStatus
        """
        return self._status

    @status.setter
    def status(self, status):
        """Sets the status of this Investigation.


        :param status: The status of this Investigation.  # noqa: E501
        :type: InvestigationStatus
        """

        self._status = status

    @property
    def systems(self):
        """Gets the systems of this Investigation.  # noqa: E501

        The systems involved  # noqa: E501

        :return: The systems of this Investigation.  # noqa: E501
        :rtype: list[System]
        """
        return self._systems

    @systems.setter
    def systems(self, systems):
        """Sets the systems of this Investigation.

        The systems involved  # noqa: E501

        :param systems: The systems of this Investigation.  # noqa: E501
        :type: list[System]
        """

        self._systems = systems

    @property
    def tags(self):
        """Gets the tags of this Investigation.  # noqa: E501

        Tags  # noqa: E501

        :return: The tags of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._tags

    @tags.setter
    def tags(self, tags):
        """Sets the tags of this Investigation.

        Tags  # noqa: E501

        :param tags: The tags of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._tags = tags

    @property
    def type(self):
        """Gets the type of this Investigation.  # noqa: E501


        :return: The type of this Investigation.  # noqa: E501
        :rtype: InvestigationType
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this Investigation.


        :param type: The type of this Investigation.  # noqa: E501
        :type: InvestigationType
        """

        self._type = type

    @property
    def users(self):
        """Gets the users of this Investigation.  # noqa: E501

        The users who share this investigation  # noqa: E501

        :return: The users of this Investigation.  # noqa: E501
        :rtype: list[str]
        """
        return self._users

    @users.setter
    def users(self, users):
        """Sets the users of this Investigation.

        The users who share this investigation  # noqa: E501

        :param users: The users of this Investigation.  # noqa: E501
        :type: list[str]
        """

        self._users = users

    @property
    def version(self):
        """Gets the version of this Investigation.  # noqa: E501


        :return: The version of this Investigation.  # noqa: E501
        :rtype: int
        """
        return self._version

    @version.setter
    def version(self, version):
        """Sets the version of this Investigation.


        :param version: The version of this Investigation.  # noqa: E501
        :type: int
        """

        self._version = version

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
        if issubclass(Investigation, dict):
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
        if not isinstance(other, Investigation):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
