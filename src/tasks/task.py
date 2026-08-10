from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class TaskStatus(Enum):

    WAITING = "Waiting"

    RUNNING = "Running"

    FINISHED = "Finished"

    FAILED = "Failed"


@dataclass
class Task:

    id: int

    name: str

    task_type: str

    created: datetime

    status: TaskStatus

    progress: int = 0