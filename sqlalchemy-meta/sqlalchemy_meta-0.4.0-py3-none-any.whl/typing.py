from typing import Callable, TYPE_CHECKING, TypeVar, Union

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import BooleanClauseList, ColumnClause, \
    UnaryExpression

__all__ = [
    'OrderByType',
    'JointType',
    'DeclarativeModelType',
]

OrderByType = Union[
    str,
    UnaryExpression,
    InstrumentedAttribute,
    ColumnClause,
]

JointType = Union[str, bool, Callable[..., BooleanClauseList]]


if TYPE_CHECKING:
    from .session import SessionDeclarativeMeta

    class _DeclarativeModel(metaclass=SessionDeclarativeMeta):
        pass


DeclarativeModelType = TypeVar('DeclarativeModelType',
                               bound='_DeclarativeModel')
