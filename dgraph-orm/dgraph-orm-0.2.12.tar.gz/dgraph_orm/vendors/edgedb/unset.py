from pydantic import BaseModel


class Unset(BaseModel):
    unset: bool = True


def is_unset(val: Unset) -> bool:
    return isinstance(val, Unset)


class ComputedPropertyException(Exception):
    pass
