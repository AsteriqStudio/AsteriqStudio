from backends.workflow_loader import WorkflowLoader

loader = WorkflowLoader()

workflow = loader.load("image/sdxl_turbo_api.json")

print(type(workflow))

print(len(workflow))