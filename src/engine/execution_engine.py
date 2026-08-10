from tasks.task import TaskStatus


class ExecutionEngine:

    def __init__(self):

        self.running = False

        self.current_task = None

    def execute(self, task, callback):

        self.running = True

        self.current_task = task

        task.status = TaskStatus.RUNNING

        try:

            result = callback(task)

            task.status = TaskStatus.FINISHED

            task.progress = 100

            return result

        except Exception:

            task.status = TaskStatus.FAILED

            raise

        finally:

            self.current_task = None

            self.running = False