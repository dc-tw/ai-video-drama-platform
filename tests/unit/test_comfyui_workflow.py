from pathlib import Path

from app.integrations.comfyui.client import ComfyUIClient


def test_workflow_placeholders_are_replaced_without_mutating_template() -> None:
    template = ComfyUIClient.load_workflow(
        Path("comfyui/workflows/text_to_image_api.json")
    )
    workflow = ComfyUIClient.prepare_workflow(
        template,
        prompt="a cat in space",
        negative_prompt="watermark",
        checkpoint="sd15.safetensors",
        seed=123,
    )

    assert workflow["6"]["inputs"]["text"] == "a cat in space"
    assert workflow["7"]["inputs"]["text"] == "watermark"
    assert workflow["4"]["inputs"]["ckpt_name"] == "sd15.safetensors"
    assert workflow["3"]["inputs"]["seed"] == 123
    assert template["6"]["inputs"]["text"] == "__PROMPT__"
