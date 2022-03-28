from abc import ABC, abstractmethod


class IPayload(ABC):

    @abstractmethod
    def to_dict(self): ...
