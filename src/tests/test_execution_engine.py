from engine.execution_engine import ExecutionEngine
from tasks.task_manager import TaskManager


engine = ExecutionEngine()

tm = TaskManager()

task = tm.create_task(
    "Generate Image",
    "image"
)


def run(task):

    print("Running:", task.name)

    task.progress = 50

    print(task.progress)

    task.progress = 100


engine.execute(task, run)

print(task.status)