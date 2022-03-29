"""Generated implementation of access_control."""

# WARNING DO NOT EDIT
# This code was generated from access-control.mcn

from __future__ import annotations

import abc  # noqa: F401
import dataclasses  # noqa: F401
import datetime  # noqa: F401
import enum  # noqa: F401
import isodate  # noqa: F401
import json  # noqa: F401
import jsonschema  # noqa: F401
import logging  # noqa: F401
import typing  # noqa: F401
import uuid  # noqa: F401
try:
    from anaml_client.utils.serialisation import JsonObject  # noqa: F401
except ImportError:
    pass


@dataclasses.dataclass(frozen=True)
class PolicyVersionId:
    """Unique identifier for versions of the policy.
    
    Args:
        value (uuid.UUID): A data field.
    """
    
    value: uuid.UUID
    
    def __str__(self) -> str:
        """Return a str of the wrapped value."""
        return str(self.value)
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for PolicyVersionId data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "string",
            "format": "uuid"
        }
    
    @classmethod
    def from_json(cls, data: dict) -> PolicyVersionId:
        """Validate and parse JSON data into an instance of PolicyVersionId.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of PolicyVersionId.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return PolicyVersionId(uuid.UUID(hex=data))
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug("Invalid JSON data received while parsing PolicyVersionId", exc_info=ex)
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return str(self.value)
    
    @classmethod
    def from_json_key(cls, data: str) -> PolicyVersionId:
        """Parse a JSON string such as a dictionary key."""
        return PolicyVersionId((lambda s: uuid.UUID(hex=s))(data))
    
    def to_json_key(self) -> str:
        """Serialise as a JSON string suitable for use as a dictionary key."""
        return str(self.value)


@dataclasses.dataclass(frozen=True)
class Policy:
    """Anaml access control policy.
    
    The access control policy enforce by an Anaml server is a list of rules.
    Each rule allows or forbids a collection of user principals the permission
    to perform some action/s on a collection resource/s.
    
    Rules are evaluated in order and the first match determines the outcome of
    the check. If no rule matches the request, it is denied.
    
    Args:
        rules (typing.List[Rule]): A data field.
        version (PolicyVersionId): A data field.
    """
    
    rules: typing.List[Rule]
    version: PolicyVersionId
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for Policy data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "rules": {
                    "type": "array",
                    "item": Rule.json_schema()
                },
                "version": PolicyVersionId.json_schema()
            },
            "required": [
                "rules",
                "version",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> Policy:
        """Validate and parse JSON data into an instance of Policy.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of Policy.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return Policy(
                rules=[Rule.from_json(v) for v in data["rules"]],
                version=PolicyVersionId.from_json(data["version"]),
            )
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug(
                "Invalid JSON data received while parsing Policy",
                exc_info=ex
            )
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return {
            "rules": [v.to_json() for v in self.rules],
            "version": self.version.to_json()
        }


@dataclasses.dataclass(frozen=True)
class PolicyCreationRequest:
    """Args:
        rules (typing.List[Rule]): A data field."""
    
    rules: typing.List[Rule]
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for PolicyCreationRequest data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "rules": {
                    "type": "array",
                    "item": Rule.json_schema()
                }
            },
            "required": [
                "rules",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> PolicyCreationRequest:
        """Validate and parse JSON data into an instance of PolicyCreationRequest.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of PolicyCreationRequest.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return PolicyCreationRequest(
                rules=[Rule.from_json(v) for v in data["rules"]],
            )
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug(
                "Invalid JSON data received while parsing PolicyCreationRequest",
                exc_info=ex
            )
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return {
            "rules": [v.to_json() for v in self.rules]
        }


@dataclasses.dataclass(frozen=True)
class Principal(abc.ABC):
    """Access control policy principal name.
    
    A pattern that matches one or more users or groups. Principals must begin
    with "user:" or "group:". The rest of the principal is a pattern to be
    matched against user or group names. Patterns may contain "*" characters
    which match any zero or more characters.
    
    Examples: "user:thomas", "group:analysts", "group:level_*", "user:*"
    
    Args:
        pattern (str): A data field.
    """
    
    ADT_TYPE: typing.ClassVar[str] = ""
    adt_type: str = dataclasses.field(init=False, repr=False, default=ADT_TYPE)
    
    pattern: str
    
    @classmethod
    def json_schema(cls) -> Principal:
        """JSON schema for variant Principal.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        adt_types = [klass.ADT_TYPE for klass in cls.__subclasses__()]
        return {
            "type": "object",
            "properties": {
                "adt_type": {
                    "type": "string",
                    "enum": adt_types
                }
            },
            "required": [
                "adt_type",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> Principal:
        """Validate and parse JSON data into an instance of Principal.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of Principal.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            adt_type = data.get("adt_type", None)
            for klass in cls.__subclasses__():
                if klass.ADT_TYPE == adt_type:
                    return klass.from_json(data)
            raise ValueError("Unknown adt_type: '{ty}'".format(ty=adt_type))
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug("Invalid JSON data received while parsing Principal", exc_info=ex)
            raise
    
    @abc.abstractmethod
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class UserPrincipal(Principal):
    """Match against users.
    
    Args:
        pattern (str): A data field.
    """
    
    ADT_TYPE: typing.ClassVar[str] = "user"
    adt_type: str = dataclasses.field(init=False, repr=False, default=ADT_TYPE)
    
    pattern: str
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for UserPrincipal data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "adt_type": {
                    "type": "string",
                    "enum": [cls.ADT_TYPE]
                },
                "pattern": {
                    "type": "string"
                }
            },
            "required": [
                "adt_type",
                "pattern",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> UserPrincipal:
        """Validate and parse JSON data into an instance of UserPrincipal.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of UserPrincipal.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return UserPrincipal(
                pattern=str(data["pattern"]),
            )
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug(
                "Invalid JSON data received while parsing UserPrincipal",
                exc_info=ex
            )
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return {
            "adt_type": self.ADT_TYPE,
            "pattern": str(self.pattern)
        }


@dataclasses.dataclass(frozen=True)
class GroupPrincipal(Principal):
    """Match against user groups.
    
    Args:
        pattern (str): A data field.
    """
    
    ADT_TYPE: typing.ClassVar[str] = "group"
    adt_type: str = dataclasses.field(init=False, repr=False, default=ADT_TYPE)
    
    pattern: str
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for GroupPrincipal data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "adt_type": {
                    "type": "string",
                    "enum": [cls.ADT_TYPE]
                },
                "pattern": {
                    "type": "string"
                }
            },
            "required": [
                "adt_type",
                "pattern",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> GroupPrincipal:
        """Validate and parse JSON data into an instance of GroupPrincipal.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of GroupPrincipal.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return GroupPrincipal(
                pattern=str(data["pattern"]),
            )
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug(
                "Invalid JSON data received while parsing GroupPrincipal",
                exc_info=ex
            )
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return {
            "adt_type": self.ADT_TYPE,
            "pattern": str(self.pattern)
        }


@dataclasses.dataclass(frozen=True)
class RolePrincipal(Principal):
    """Match against roles.
    
    Args:
        pattern (str): A data field.
    """
    
    ADT_TYPE: typing.ClassVar[str] = "role"
    adt_type: str = dataclasses.field(init=False, repr=False, default=ADT_TYPE)
    
    pattern: str
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for RolePrincipal data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "adt_type": {
                    "type": "string",
                    "enum": [cls.ADT_TYPE]
                },
                "pattern": {
                    "type": "string"
                }
            },
            "required": [
                "adt_type",
                "pattern",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> RolePrincipal:
        """Validate and parse JSON data into an instance of RolePrincipal.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of RolePrincipal.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return RolePrincipal(
                pattern=str(data["pattern"]),
            )
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug(
                "Invalid JSON data received while parsing RolePrincipal",
                exc_info=ex
            )
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return {
            "adt_type": self.ADT_TYPE,
            "pattern": str(self.pattern)
        }


@dataclasses.dataclass(frozen=True)
class Resource:
    """Access control policy resource name.
    
    Args:
        value (str): A data field.
    """
    
    value: str
    
    def __str__(self) -> str:
        """Return a str of the wrapped value."""
        return str(self.value)
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for Resource data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "string"
        }
    
    @classmethod
    def from_json(cls, data: dict) -> Resource:
        """Validate and parse JSON data into an instance of Resource.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of Resource.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return Resource(str(data))
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug("Invalid JSON data received while parsing Resource", exc_info=ex)
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return str(self.value)
    
    @classmethod
    def from_json_key(cls, data: str) -> Resource:
        """Parse a JSON string such as a dictionary key."""
        return Resource(str(data))
    
    def to_json_key(self) -> str:
        """Serialise as a JSON string suitable for use as a dictionary key."""
        return str(self.value)


@dataclasses.dataclass(frozen=True)
class Action:
    """Access control policy action name.
    
    Args:
        value (str): A data field.
    """
    
    value: str
    
    def __str__(self) -> str:
        """Return a str of the wrapped value."""
        return str(self.value)
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for Action data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "string"
        }
    
    @classmethod
    def from_json(cls, data: dict) -> Action:
        """Validate and parse JSON data into an instance of Action.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of Action.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return Action(str(data))
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug("Invalid JSON data received while parsing Action", exc_info=ex)
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return str(self.value)
    
    @classmethod
    def from_json_key(cls, data: str) -> Action:
        """Parse a JSON string such as a dictionary key."""
        return Action(str(data))
    
    def to_json_key(self) -> str:
        """Serialise as a JSON string suitable for use as a dictionary key."""
        return str(self.value)


class Outcome(enum.Enum):
    """Access control policy outcome."""
    Allow = "allow"
    """Permission granted."""
    Deny = "deny"
    """Permission denied."""
    
    @classmethod
    def json_schema(cls) -> dict:
        """JSON schema for 'Outcome'.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "adt_type": {
                    "type": "string",
                    "enum": [
                        "allow",
                        "deny",
                    ]
                }
            },
            "required": [
                "adt_type",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> Outcome:
        """Validate and parse JSON data into an instance of Outcome.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of Outcome.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return Outcome(str(data['adt_type']))
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug("Invalid JSON data received while parsing Outcome", exc_info=ex)
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            JSON data ready to be serialised.
        """
        return {'adt_type': self.value}
    
    @classmethod
    def from_json_key(cls, data: str) -> Outcome:
        """Validate and parse a value from a JSON dictionary key.
        
        Args:
            data (str): JSON data to validate and parse.
        
        Returns:
            An instance of Outcome.
        """
        return Outcome(str(data))
    
    def to_json_key(self) -> str:
        """Serialised this instanse as a JSON string for use as a dictionary key.
        
        Returns:
            A JSON string ready to be used as a key.
        """
        return str(self.value)


@dataclasses.dataclass(frozen=True)
class Rule:
    """Access control rule.
    
    Each access control rule four fields:
    
    1. patterns to match user principals
    2. patterns to match against resource identifiers
    3. actions
    4. an outcome: allow or deny
    
    Args:
        principals (typing.List[Principal]): A data field.
        resources (typing.List[Resource]): A data field.
        actions (typing.List[Action]): A data field.
        outcome (Outcome): A data field.
    """
    
    principals: typing.List[Principal]
    resources: typing.List[Resource]
    actions: typing.List[Action]
    outcome: Outcome
    
    @classmethod
    def json_schema(cls) -> dict:
        """Return the JSON schema for Rule data.
        
        Returns:
            A Python dictionary describing the JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "principals": {
                    "type": "array",
                    "item": Principal.json_schema()
                },
                "resources": {
                    "type": "array",
                    "item": Resource.json_schema()
                },
                "actions": {
                    "type": "array",
                    "item": Action.json_schema()
                },
                "outcome": Outcome.json_schema()
            },
            "required": [
                "principals",
                "resources",
                "actions",
                "outcome",
            ]
        }
    
    @classmethod
    def from_json(cls, data: dict) -> Rule:
        """Validate and parse JSON data into an instance of Rule.
        
        Args:
            data (dict): JSON data to validate and parse.
        
        Returns:
            An instance of Rule.
        
        Raises:
            ValidationError: When schema validation fails.
            KeyError: When a required field is missing from the JSON.
        """
        try:
            jsonschema.validate(data, cls.json_schema())
            return Rule(
                principals=[Principal.from_json(v) for v in data["principals"]],
                resources=[Resource.from_json(v) for v in data["resources"]],
                actions=[Action.from_json(v) for v in data["actions"]],
                outcome=Outcome.from_json(data["outcome"]),
            )
        except jsonschema.exceptions.ValidationError as ex:
            logging.debug(
                "Invalid JSON data received while parsing Rule",
                exc_info=ex
            )
            raise
    
    def to_json(self) -> dict:
        """Serialise this instance as JSON.
        
        Returns:
            Data ready to serialise as JSON.
        """
        return {
            "principals": [v.to_json() for v in self.principals],
            "resources": [v.to_json() for v in self.resources],
            "actions": [v.to_json() for v in self.actions],
            "outcome": self.outcome.to_json()
        }
