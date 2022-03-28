from abc import ABC, abstractmethod

from .schemas import Insight
from .schemas.result import Result


class Channel(ABC):
    
    @abstractmethod
    def connect(self): ...

    @abstractmethod
    def write(self, insight: Insight) -> Result: ...
