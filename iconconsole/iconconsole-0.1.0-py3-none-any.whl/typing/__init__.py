# -*- coding: utf-8 -*-

__all__ = (
    "is_base_type",
    "name_to_type",
    "get_origin",
    "get_args",
    "is_struct",
    "get_annotations",
)

from typing import Tuple, Union, Type, Dict, Any, Optional

from iconconsole.base.address import Address

BaseObject = Union[bool, bytes, int, str, 'Address']
BaseObjectType = Type[BaseObject]

BASE_TYPES = {bool, bytes, int, str, Address}
TYPE_NAME_TO_TYPE = {_type.__name__: _type for _type in BASE_TYPES}


def is_base_type(value: type) -> bool:
    try:
        return value in BASE_TYPES
    except:
        return False


def name_to_type(type_name: str) -> BaseObjectType:
    return TYPE_NAME_TO_TYPE[type_name]


def get_origin(type_hint: type) -> Optional[type]:
    """
    Dict[str, int] -> dict
    List[str] -> list
    subclass of type -> itself
    subclass of TypedDict -> itself

    :param type_hint:
    :return:
    """
    if type_hint == "Address":
        type_hint = Address

    if isinstance(type_hint, type):
        return type_hint

    return getattr(type_hint, "__origin__", None)


def get_args(type_hint: type) -> Tuple[type]:
    return getattr(type_hint, "__args__", ())


def is_struct(type_hint) -> bool:
    try:
        return type_hint.__class__.__name__ == "_TypedDictMeta"
    except:
        return False


def get_annotations(obj: Any, default: Any) -> Dict[str, type]:
    return getattr(obj, "__annotations__", default)


def isinstance_ex(value: Any, _type: type) -> bool:
    if not isinstance(value, _type):
        return False

    if type(value) is bool and _type is not bool:
        return False

    return True
