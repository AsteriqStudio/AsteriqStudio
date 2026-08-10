from backends.workflow_loader import WorkflowLoader

loader = WorkflowLoader("workflows/video")

workflow = loader.load("ltx.json")

print(type(workflow))