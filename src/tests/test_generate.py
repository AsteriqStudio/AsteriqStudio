from backends.comfy_client import ComfyClient
from backends.workflow_loader import WorkflowLoader
from backends.workflow_editor import WorkflowEditor
from backends.history_parser import HistoryParser
from backends.output_manager import OutputManager
from backends.image_importer import ImageImporter


client = ComfyClient()

loader = WorkflowLoader()

workflow = loader.load("image/sdxl_turbo_api.json")

workflow = WorkflowEditor.prepare(

    workflow,

    prompt="A futuristic city at sunset, ultra realistic",

    width=512,

    height=512,

    steps=1,

    seed=42

)

prompt_id = client.generate(workflow)

print(prompt_id)

history = client.wait_for_image(prompt_id)

image = HistoryParser.get_image(history)

print(image)

manager = OutputManager()

path = manager.image_path(image)

print(path)

importer = ImageImporter()

project_folder = "Projects/Default/Images"

new_image = importer.copy(
    path,
    project_folder
)

print(new_image)