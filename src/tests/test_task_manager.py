from tasks.task_manager import TaskManager

tm = TaskManager()

tm.create_task(
    "Generate Samurai",
    "image"
)

tm.create_task(
    "Generate Castle",
    "image"
)

tm.create_task(
    "Upscale Image",
    "upscale"
)

for task in tm.all_tasks():

    print(task)