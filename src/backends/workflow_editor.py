class WorkflowEditor:

    @staticmethod
    def prepare(

        workflow,

        prompt,

        width,

        height,

        steps,

        seed

    ):

        workflow["6"]["inputs"]["text"] = prompt

        workflow["5"]["inputs"]["width"] = width

        workflow["5"]["inputs"]["height"] = height

        workflow["22"]["inputs"]["steps"] = steps

        workflow["13"]["inputs"]["noise_seed"] = seed

        return workflow