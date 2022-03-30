from sqlalchemy import or_
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnClause, UnaryExpression

__all__ = [
    'ORDER_BY_ALLOWED_TYPE',
    'JOINT_OR_ALLOWED_VALUE',
]

ORDER_BY_ALLOWED_TYPE = (
    str,
    UnaryExpression,
    InstrumentedAttribute,
    ColumnClause,
)

JOINT_OR_ALLOWED_VALUE = frozenset({or_, False, 'or', 'OR'})
