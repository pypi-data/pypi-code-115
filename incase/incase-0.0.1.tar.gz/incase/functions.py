import enum
import functools
import typing as t

from incase.classes import Case, Caseless


def _incase_iterable(case: t.Iterable, value: t.Iterable) -> t.Iterable:
    return (Caseless(target)[case] for case, target in zip(case, value))


def _incase_single(case: str | Case, value: str | Case | dict | t.Iterable) -> str:
    if not value:
        return value
    if isinstance(value, (str, Case)):
        return Caseless(value)[case]
    elif isinstance(value, dict):
        return {k: _incase_single(case, v) for k, v in value.items()}
    else:
        try:
            if iter(value):
                generator = (_incase_single(case, v) for v in value)
                if isinstance(value, (list, tuple, set)):
                    return type(value)(generator)
                else:
                    return generator
        except TypeError:
            return value

@functools.singledispatch
def incase(case: t.Any, value: t.Any) -> t.Callable:
    if not value:
        return value
    # Enum is not a class and so single dispatch doesn't work on it...
    if isinstance(case, enum.Enum):
        return _incase_single(case.name, value)
    else:
        raise NotImplementedError(f"incase does not support type: {type(case)}")


@incase.register
def _(case: str, value: str | Case) -> dict:
    return _incase_single(case, value)


@incase.register
def _(case: list, incaseable: t.Iterable) -> t.List:
    return list(_incase_iterable(case, incaseable))


@incase.register
def _(case: dict, value: dict) -> dict:
    return {k: Caseless(v)[case[k]] for k, v in value.items()}


def case_modifier(
    args_case: t.Sequence | str | Case | None = None,
    kwargs_case: dict | str | Case | None = None,
    keywords_case: str | Case | None = None,
    output_case: t.Sequence | str | Case | dict | None = None,
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            args = incase(args_case, args) if args_case else args
            kwargs = incase(kwargs_case, kwargs) if kwargs_case else kwargs
            kwargs = (
                {incase(keywords_case, k): v for k, v in kwargs.items()}
                if keywords_case
                else kwargs
            )
            return incase(output_case, func(*args, **kwargs))

        return functools.wraps(func)(wrapper)

    return decorator
