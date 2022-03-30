from abc import ABC, abstractmethod
from typing import Callable

from arrow_bpmn.__spi__ import State


class ScriptFactory(ABC):

    @abstractmethod
    def __call__(self, state: State, language: str, script: str) -> Callable[[dict], dict]:
        pass
