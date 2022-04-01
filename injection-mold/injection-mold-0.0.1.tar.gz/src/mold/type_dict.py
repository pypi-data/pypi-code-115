from __future__ import annotations

from collections import UserDict

from mold.util import norm_type_name


class TypeDict(UserDict):

    def __init__(self, __dict=None, default=None, **kwargs) -> None:
        self._name_to_type = dict()
        self._default = default
        super().__init__(__dict, **kwargs)

    def __setitem__(self, key, value):
        if type(key) == str:
            key = norm_type_name(key)
        elif isinstance(key, type):
            self._name_to_type[norm_type_name(key.__name__)] = key

        super().__setitem__(key, value)

    def __getitem__(self, item):

        if type(item) == str:
            item = norm_type_name(item)

        try:
            if item in self.data:
                return self.data.__getitem__(item)

            if isinstance(item, type):
                return self.data.__getitem__(norm_type_name(item.__name__))

            if item in self._name_to_type:
                return self.data.__getitem__(self._name_to_type[item])

            raise KeyError()

        except KeyError:

            if callable(self._default):
                return self._default()
            elif self._default is not None:
                return self._default

            raise

    def __contains__(self, item):
        if type(item) == str:
            item = norm_type_name(item)

        if item in self.data:
            return True

        if isinstance(item, type):
            return norm_type_name(item.__name__) in self.data

        if item in self._name_to_type:
            return self._name_to_type[item] in self.data

        return False
