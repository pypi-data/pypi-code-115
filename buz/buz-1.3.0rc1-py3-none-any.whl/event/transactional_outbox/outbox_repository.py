from abc import ABC, abstractmethod

from buz.event.transactional_outbox import OutboxRecord


class OutboxRepository(ABC):
    @abstractmethod
    def save(self, outbox_record: OutboxRecord) -> None:
        pass
