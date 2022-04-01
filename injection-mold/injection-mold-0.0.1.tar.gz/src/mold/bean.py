import abc
import inspect
from typing import Callable
from typing import Dict
from typing import Set
from typing import Union

from mold.util import norm_type

SYSTEM_TYPES = [abc.ABC, object, inspect._empty]


def get_provided(f) -> Set[str]:
    if type(f) in SYSTEM_TYPES or f in SYSTEM_TYPES:
        return set()

    provided = set()
    if isinstance(f, type):
        provided.add(norm_type(f))
        for parent in f.__bases__:
            provided = provided.union(get_provided(parent))
    elif callable(f):
        provided = get_provided(inspect.signature(f).return_annotation)
    else:
        raise ValueError()

    return provided


def get_required(f, ignored) -> Dict[str, str]:
    required = dict()

    if not ignored:
        ignored = []

    for name, p in inspect.signature(f).parameters.items():
        if name not in ignored:
            required[name] = norm_type(p.annotation)

    return required


class BeanDefinition:
    name: str
    factory: Callable
    types_required: Dict[str, str]
    types_provided: Set[str]
    is_primary:bool = False

    def __init__(self, f: Union[type, Callable], wrapped, ignored=None, primary=False):
        self.name = f.__name__
        self.factory = wrapped
        self.types_provided = get_provided(f)
        self.types_required = get_required(f, ignored)
        self.is_primary = primary

    def __repr__(self):
        return f'BeanDef({self.name}, provided={self.types_provided}, required={self.types_required}), is_primary={self.is_primary} '

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return self.name.__hash__()