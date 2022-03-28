from abc import ABC, abstractmethod

from .schemas import Insight
from .schemas.result import Result


class AioChannel(ABC):

    @abstractmethod
    async def connect(self): ...

    @abstractmethod
    async def write(self, insight: Insight) -> Result: ...
