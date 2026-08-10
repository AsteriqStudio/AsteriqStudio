from datetime import datetime

from tasks.task import Task, TaskStatus


class TaskManager:

    def __init__(self):

        self.tasks = []
        self.next_id = 1

    def create_task(self, name, task_type, data=None):

        task = Task(
            id=self.next_id,
            name=name,
            task_type=task_type,
            created=datetime.now(),
            status=TaskStatus.WAITING
        )

        task.data = data

        self.tasks.append(task)

        self.next_id += 1

        return task

    def next_waiting_task(self):

        for task in self.tasks:

            if task.status == TaskStatus.WAITING:

                return task

        return None

    def all_tasks(self):

        return self.tasks