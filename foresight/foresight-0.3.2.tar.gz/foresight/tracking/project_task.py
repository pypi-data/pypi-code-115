import pendulum
from pendulum import datetime


class ProjectTask:
    def __init__(
        self, client: str, project: str, task: str, date: datetime, duration: float
    ) -> None:
        self.client = client
        self.project = project
        self.task = task
        self.date = date
        self.duration = duration

    @property
    def day(self) -> int:
        return self.date.day_of_year

    def _can_merge(self, other: "ProjectTask") -> bool:
        props = ["client", "project", "task"]
        for prop in props:
            if getattr(self, prop) != getattr(other, prop):
                return False

        if self.day != other.day or self.date.year != other.date.year:
            return False

        return True

    def __add__(self, other: "ProjectTask") -> "ProjectTask":
        if not self._can_merge(other):
            raise ValueError(
                "Project tasks must be of same client, project, task, and day of the year to combine."
            )

        return ProjectTask(
            client=self.client,
            project=self.project,
            task=self.task,
            date=self.date,
            duration=self.duration + other.duration,
        )

    def __lt__(self, other: "ProjectTask") -> "ProjectTask":
        if self.date < other.date:
            return True

    def __str__(self) -> str:
        return f"{self.client} [{self.project} - {self.task}] ({self.date}): {self.duration}"
