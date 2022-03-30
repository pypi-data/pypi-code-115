from functools import partialmethod
from operator import attrgetter
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterator, List, Mapping, \
    Optional, Sequence, Tuple, Type, Union

from sqlalchemy import Column, and_, inspect, or_, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeMeta, InstrumentedAttribute, Mapper, \
    Query, scoped_session
from sqlalchemy.sql import Selectable
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, \
    UnaryExpression

from .constant import JOINT_OR_ALLOWED_VALUE, ORDER_BY_ALLOWED_TYPE
from .typing import DeclarativeModelType, JointType, OrderByType

__all__ = [
    'SessionDeclarativeMeta',
]


def _get_abs_int(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None

    return abs(int(value))


def _select_joint(
    value: Optional[JointType],
) -> Callable[..., BooleanClauseList]:
    """Get joint expression of sqlalchemy by marker."""
    return or_ if value in JOINT_OR_ALLOWED_VALUE else and_


def _normalize_order_by(value: Any) -> Tuple[OrderByType, ...]:
    """Get order_by tuple of expressions."""
    # Check for strings or sqlalchemy allowed structures
    if isinstance(value, ORDER_BY_ALLOWED_TYPE):
        return value,  # pylint: disable=trailing-comma-tuple

    # Check for sequences becides strings
    if isinstance(value, Sequence):
        return tuple(value)

    raise ValueError(
        'order_by should be ordered sequence or suitable '
        'sqlalchemy order_by expression.',
    )


def _compile_primary_key_filter(
    primary_key: Tuple[Column, ...],
    *identities: Any,
) -> Iterator[Union[BooleanClauseList, BinaryExpression]]:
    """Compile sqlalchemy compalible filter expression for primary key
    columns."""
    single_primary_key = len(primary_key) == 1

    for identity in identities:

        if not isinstance(identity, Mapping):

            if not single_primary_key:
                raise ValueError(
                    'For multi primary key it must be declared '
                    'dict-like identity.',
                )

            yield primary_key[0] == identity
            continue

        # identity is Mapping
        if single_primary_key and len(identity) > 1:
            raise ValueError(
                'Primary key identity must be a string or '
                'single-key Mapping.',
            )

        yield and_(
            *(column == identity[column.key] for column in primary_key),
        )


def _get_setable_unique_hybrid_keys(
    data: Mapping[str, Any],
    mapper: Mapper,
) -> Iterator[str]:
    """Filter sqlalchemy hybrid_property keys, which can be setted by input
    data."""
    class_ = mapper.class_

    for key, descriptor in mapper.all_orm_descriptors.items():

        if not isinstance(
            descriptor, hybrid_property,
        ) or getattr(
            descriptor, 'fset', None,
        ) is None:
            # descriptor is not setable ``hybrid_property``
            continue

        original_key = getattr(class_, key).property.class_attribute.key

        if original_key not in data:
            # original column not in unput data, so, we can use hybrid key
            yield key


def _filter_kwargs(mapper: Mapper, kwargs: Any) -> Dict[str, Any]:
    """Filter input kwargs with allowed columns or hybdir_property keys of
    model."""

    # Hybrid properties may represent actual column for backward
    # compatibility.
    hybrid_property_keys = frozenset(
        _get_setable_unique_hybrid_keys(
            kwargs,
            mapper,
        ),
    )
    column_keys = frozenset(mapper.columns.keys())
    allowed_keys = hybrid_property_keys | column_keys

    return {
        k: v for k, v in kwargs.items() if k in allowed_keys
    }


def _delete_method(self: DeclarativeModelType, silent: bool = False) -> None:
    """Delete method for child class of metaclass."""
    db_session = type(self).db_session

    try:
        with db_session.begin_nested():
            db_session.delete(self)
            db_session.flush()

    except SQLAlchemyError:
        if not silent:
            raise


_delete_method.__name__ = 'delete'


def _edit_method(
    self: DeclarativeModelType,
    *args: Any,
    **kwargs: Any,
) -> DeclarativeModelType:
    """Edit method for child class of metaclass."""
    self.__init__(  # type: ignore[misc]
        *args,
        **_filter_kwargs(self.__class__.mapper, kwargs),
    )
    return self


_edit_method.__name__ = 'edit'


def _get_primary_key_dict_method(
    self: DeclarativeModelType,
) -> Mapping[str, InstrumentedAttribute]:
    """Calculate read-only dict value for primary key columns."""
    return MappingProxyType({
        key: getattr(self, key) for key in map(
            attrgetter('key'), self.__class__.mapper.primary_key,
        )
    })


class SessionDeclarativeMeta(DeclarativeMeta):
    """
    Declarative metaclass for sqlalchemy models, that required incapsulation
    of sqlalchemy database scoped session methods for session-based model
    operations.
    """

    def __new__(  # pylint: disable=bad-mcs-classmethod-argument
        mcs,
        classname: str,
        bases: Tuple[Type[object], ...],
        namespace: Dict[str, Any],
    ) -> 'SessionDeclarativeMeta':
        # Set additional methods during type construction.
        namespace.setdefault('delete', _delete_method)
        namespace.setdefault('edit', _edit_method)
        namespace.setdefault(
            'primary_key',
            property(_get_primary_key_dict_method),
        )
        return super().__new__(mcs, classname, bases, namespace)

    def __init__(
        cls,
        classname: str,
        bases: Tuple[Type[object], ...],
        namespace: Dict[str, Any],
    ) -> None:
        super().__init__(classname, bases, namespace)

        if not hasattr(cls, '_db_session'):
            # session could be setted already in any parent class
            cls._db_session = None

        cls._mapper = None

    @property
    def db_session(cls) -> scoped_session:
        """Sqlalchemy database scoped session."""
        if cls._db_session is None:
            raise RuntimeError(
                f'"db_session" is not defined for {cls.__name__}',
            )
        return cls._db_session

    @db_session.setter
    def db_session(cls, value: Any) -> None:
        assert isinstance(value, scoped_session), \
            'An instance of sqlalchemy.orm.scoped_session is required.'
        cls._db_session = value

    @db_session.deleter
    def db_session(cls) -> None:
        cls._db_session = None

    def get_query(
        cls,
        entity: Union[DeclarativeMeta, Selectable],
        *entities: Union[DeclarativeMeta, Selectable],
    ) -> Query:
        """Execution of sqlalchemy session query method."""
        return cls.db_session.query(entity, *entities)

    @property
    def query(cls) -> Query:
        return cls.get_query(cls)  # pylint: disable=no-value-for-parameter

    @property
    def mapper(cls) -> Mapper:
        """Cached property of sqlalchemy model mapper."""
        if cls._mapper is None:
            cls._mapper = inspect(cls)
        return cls._mapper

    def _build_query(
        cls,
        *conditions: Union[UnaryExpression, BinaryExpression],
        joint: Optional[JointType] = None,
        query: Optional[Query] = None,
        order_by: Union[
            None,
            OrderByType,
            Sequence[OrderByType],
        ] = None,
        start: Optional[int] = None,
        stop: Optional[int] = None,
    ) -> Query:
        """Build session-based query with declared filter conditions, sorting
        and slicing."""
        query = query or cls.query

        if conditions:
            query = query.filter(_select_joint(joint)(*conditions))

        if order_by is not None:
            query = query.order_by(*_normalize_order_by(order_by))

        start = _get_abs_int(start)

        if start:
            query = query.offset(start)

        stop = _get_abs_int(stop)

        if stop:
            query = query.limit(stop - (start or 0))

        return query

    def all(cls, *args, **kwargs) -> List[DeclarativeModelType]:
        """Fetching all entities with declared filter conditions, sorting and
        slicing."""
        return cls._build_query(*args, **kwargs).all()

    def first(cls, *args, **kwargs) -> Optional[DeclarativeModelType]:
        """Fetching first entity with declared filter conditions, sorting and
        slicing."""
        return cls._build_query(*args, **kwargs).first()

    def create(
        cls,
        *args,
        **kwargs,
    ) -> DeclarativeModelType:
        """Create instance and add it into session."""
        item: DeclarativeModelType = cls(*args, **kwargs)

        db_session = cls.db_session
        db_session.add(item)
        db_session.flush()

        return item

    def truncate(
        cls,
        cascade: bool = False,
        engine: Optional[Engine] = None,
    ) -> None:
        """Truncate associated with declarative class SQL table."""
        if engine is None:
            engine = cls.db_session.get_bind()

        engine.execute(
            text(
                f'TRUNCATE {cls.__table__.name}{" CASCADE" if cascade else ""}',
            ).execution_options(autocommit=True),
        )

    truncate_cascade = partialmethod(truncate, cascade=True)

    def byid(
        cls,
        *identities: Any,
        first: bool = False,
        **params: Any,
    ) -> Union[List[DeclarativeModelType], DeclarativeModelType, None]:
        """Get instances by their primary keys."""
        if not identities:
            return None

        query = cls.query.filter(
            or_(
                *_compile_primary_key_filter(
                    cls.mapper.primary_key,
                    *identities,
                ),
            ),
        )

        return cls.first(
            query=query,
            **params,
        ) if first else cls.all(
            query=query,
            **params,
        )

    def __call__(
        cls,
        *args,
        **kwargs,
    ) -> DeclarativeModelType:
        """Initialization of child class with proper filtration of input
        keyword arguments, consireding sqlalchemy hybrid properties."""
        return super().__call__(*args, **_filter_kwargs(cls.mapper, kwargs))

    def commit(cls) -> None:
        """Short link to database session commit."""
        cls.db_session.commit()

    def flush(cls) -> None:
        """Short link to database session flush."""
        cls.db_session.flush()

    def rollback(cls) -> None:
        """Short link to database session rollback."""
        cls.db_session.rollback()
