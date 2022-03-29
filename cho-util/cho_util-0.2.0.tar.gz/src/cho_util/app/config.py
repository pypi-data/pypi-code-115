#!/usr/bin/env python3

import re
from enum import Enum
from simple_parsing.helpers.serialization import (encode, register_decoding_fn)
from simple_parsing import Serializable, choice
from functools import partial
from typing import Tuple, Union, Iterable, List
from dataclasses import (
    dataclass,
    is_dataclass,
    make_dataclass,
    field)


def _encode_enum(o: 'EnumBase'):
    return o.name


def _decode_enum(cls: 'EnumBase', name: str):
    return getattr(cls, name)


def _encode_one_of(o):
    return encode({'which': o.which, 'value': o.value})


def _decode_one_of(cls, data):
    inst = cls(which=data['which'])
    inst.value = data['value']


class EnumBase(Enum):
    def __init_subclass__(cls):
        super().__init_subclass__()
        encode.register(cls, _encode_enum)
        register_decoding_fn(cls, partial(_decode_enum, cls))


def _clean(s: str):
    """cleanup invalid characters in `s`"""
    # Replace invalid characters with _.
    s = re.sub('[^0-9a-zA-Z_]', '_', s)
    # Remove leading characters until we find a letter or underscore
    s = re.sub('^[^a-zA-Z_]+', '', s)
    return s.lower()


def _unique(seq: Iterable) -> List:
    """order-preserving unique elements in `seq`."""
    out = []
    seen = set()
    for x in seq:
        if x in seen:
            continue
        out.append(x)
        seen.add(x)
    return out


def one_of(*clss: Tuple[Union[dataclass, Tuple[dataclass, str]], ...],
           typename: str = None) -> dataclass:
    """Creates a variant(cls...) where a particular option is selectable
    amongst many."""

    if len(clss) <= 0:
        raise IndexError(F'len(clss) must be > 0!')

    # Reduce to single `cls`
    if len(clss) == 1:
        cls = clss[0]
        if is_dataclass(cls):
            return cls

    # NOTE(ycho): Handle case where `typename` was not given as a kwd.
    if isinstance(clss[-1], str) and typename is None:
        clss = clss[:-1]
        typename = clss[-1]

    # Account for Tuple[dataclass,str]
    def _sanitize(clss):
        out_clss = []
        out_names = {}
        defaults = {}

        for cls in clss:
            try:
                cls, name = cls
                if not isinstance(cls, type):
                    inst = cls
                    cls = type(inst)
                    defaults[cls] = inst
                out_clss.append(cls)
                out_names[cls] = name
            except TypeError:
                if not isinstance(cls, type):
                    inst = cls
                    cls = type(inst)
                    defaults[cls] = inst
                out_clss.append(cls)
        return out_clss, out_names, defaults

    clss, cls_name, defaults = _sanitize(clss)

    # Make unique ...
    clss = tuple(_unique(clss))

    # Generate mapping between class and string-based valid identifier.
    for cls in clss:
        if cls in cls_name:
            continue
        cls_name[cls] = _clean(cls.__qualname__)

    if typename is None:
        typename = 'one_of_' + '_'.join(cls_name[cls] for cls in clss)
        typename = _clean(typename)

    Which = EnumBase('Which', {cls_name[cls]: i
                               for i, cls in enumerate(clss)})
    fields = [
        ('value', Union[clss], field(init=False)),
        # FIXME(ycho): choice doesn't appear to work ... for now.
        # ('which', Which, choice(Which, default=Which(0))),
        ('which', Which, Which(0))
    ]
    for cls in clss:
        default = None
        # Resolve defaults either from
        # passed-in instance or nullary-arg initialization.
        if cls in defaults:
            default = defaults[cls]
        else:
            try:
                default = cls()
            except TypeError:
                default = None

        if default is None:
            fields.append((cls_name[cls], cls))
        else:
            fields.append(
                (cls_name[cls], cls, field(
                    default=default)))

    def _set_value(self):
        name = cls_name[clss[self.which.value]]
        self.value = getattr(self, name)

    def _getattr(self, name):
        """propagate self.value.{name}"""
        return getattr(self.value, name)

    cls = make_dataclass(typename, fields,
                         bases=(Serializable,),
                         namespace={
                             '__post_init__': _set_value,
                             '__getattr__': _getattr,
                         })

    # encode.register(cls, _encode_one_of)
    # register_decoding_fn(cls, partial(_decode_one_of, cls))
    return cls
