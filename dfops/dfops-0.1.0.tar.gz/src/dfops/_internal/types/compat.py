import sys as _sys

if _sys.version_info < (3, 9):
    # pylint: disable-next=unused-import
    from typing import (  # noqa
        Callable,
        Container,
        Dict,
        FrozenSet,
        Generator,
        Iterable,
        Iterator,
        List,
        OrderedDict,
        Sequence,
        Set,
        Tuple,
        Type,
    )
else:
    # pylint: disable=unused-import

    from collections import OrderedDict  # noqa
    from collections.abc import (  # noqa
        Callable,
        Container,
        Generator,
        Iterable,
        Iterator,
        Sequence,
    )

    # pylint: enable=unused-import

    Type = type
    Dict = dict
    Tuple = tuple
    List = list
    FrozenSet = frozenset
    Set = set
