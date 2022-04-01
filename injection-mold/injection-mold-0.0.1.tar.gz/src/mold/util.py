from typing import Union


class Singleton:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    @classmethod
    def clear(cls):
        cls._instance = None


def norm_type_name(event: str):
    dot_idx = event.rfind('.') + 1
    return event[dot_idx:]


def norm_type(t: Union[type, str]) -> str:
    if type(t) == str:
        return norm_type_name(t)
    else:
        return norm_type_name(t.__name__)
