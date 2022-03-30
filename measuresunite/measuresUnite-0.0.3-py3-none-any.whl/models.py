from typing import List, Iterable, Union
from .unit import Unit

ValueLike = Union[int, float, Iterable[int], Iterable[float], Iterable[Union[int, float]]]
UnitLike = Union[str, Unit]