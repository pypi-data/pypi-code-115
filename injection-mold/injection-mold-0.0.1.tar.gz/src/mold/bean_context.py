import abc
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from mold.bean_registry import BeanRegistry
from mold.bean_registry import BeanDefinition

logger = logging.getLogger(__name__)


class BeanContext:

    _bean_instances: Dict[BeanDefinition, Any]
    _bean_dep_cache: Dict[str, Dict[str, Any]]

    _context_stack: List['BeanContext'] = list()

    def __init__(self):
        self._bean_instances = dict()
        self._bean_dep_cache = dict()

    @classmethod
    def __enter__(cls):
        top = BeanContext()
        cls._context_stack.append(top)
        return top

    @classmethod
    def __exit__(cls, exc_type, exc_val, exc_tb):
        cls._context_stack.pop()

    @classmethod
    def is_valid(cls):
        return len(cls._context_stack) > 0

    @classmethod
    def get(cls) -> 'BeanContext':
        if len(cls._context_stack) == 0:
            raise Exception('Unable to get BeanContext because we\'re not in a context')

        return cls._context_stack[-1]

    def resolve_deps(self, resolve_bean: BeanDefinition, passed_args=None) -> Optional[Dict[str, Any]]:
        if resolve_bean.name in self._bean_dep_cache:
            return self._bean_dep_cache[resolve_bean.name]

        registry = BeanRegistry.get()

        mapped_deps: Dict[str, BeanDefinition] = dict()

        for key, req in resolve_bean.types_required.items():
            if passed_args is not None and key in passed_args:
                continue

            options: List[BeanDefinition] = list()
            for bean in registry.beans():
                provided_strings = [str(t) for t in bean.types_provided]
                if str(req) in provided_strings:
                    recursive_deps = self.resolve_deps(bean)
                    if recursive_deps is not None:
                        options.append(bean)

            if len(options) == 0:
                return None

            elif len(options) == 1:
                mapped_deps[key] = options[0]

            else:
                try:
                    primary_dep = next(d for d in options if d.is_primary)
                    mapped_deps[key] = primary_dep
                except StopIteration:
                    mapped_deps[key] = options[0]

        resolved_deps = dict()
        for k, bean in mapped_deps.items():
            if bean not in self._bean_instances or self._bean_instances[bean] is None:
                self._bean_instances[bean] = bean.factory()

            resolved_deps[k] = self._bean_instances[bean]

        self._bean_dep_cache[resolve_bean.name] = resolved_deps

        return resolved_deps






