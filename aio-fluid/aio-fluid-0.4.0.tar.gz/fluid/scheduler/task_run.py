import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional

from .constants import FINISHED_STATES, TaskState

if TYPE_CHECKING:
    from .task import Task


@dataclass
class TaskRun:
    """A TaskRun contains all the data generated by a Task run"""

    id: str
    queued: int
    task: "Task"
    params: Dict[str, Any]
    start: int = 0
    end: int = 0
    priority: str = ""
    state: str = TaskState.init.name
    waiter: asyncio.Future = field(default_factory=asyncio.Future)

    @property
    def in_queue(self) -> int:
        return self.start - self.queued

    @property
    def duration(self) -> int:
        return self.end - self.start

    @property
    def total(self) -> int:
        return self.end - self.queued

    @property
    def name(self) -> str:
        return self.task.name

    @property
    def name_id(self) -> str:
        return f"{self.task.name}.{self.id}"

    @property
    def exception(self) -> Optional[BaseException]:
        return self.waiter.exception() if self.waiter.done() else None

    @property
    def result(self) -> Any:
        return (
            self.waiter.result() if self.waiter.done() and not self.exception else None
        )

    @property
    def in_finish_state(self) -> bool:
        return TaskState[self.state] in FINISHED_STATES

    @property
    def is_failure(self) -> bool:
        return TaskState[self.state] is TaskState.failure

    def set_state(self, state: TaskState) -> None:
        self.state = state.name
