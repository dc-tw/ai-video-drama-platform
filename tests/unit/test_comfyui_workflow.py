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


def test_video_workflow_has_prompt_placeholders_and_mp4_output() -> None:
    template = ComfyUIClient.load_workflow(
        Path("comfyui/workflows/video/kandinsky5_t2v_api.json")
    )
    workflow = ComfyUIClient.prepare_workflow(
        template,
        prompt="A cat astronaut walks slowly across a space station hull.",
        negative_prompt="text, watermark, malformed motion",
        checkpoint="unused-by-this-workflow.safetensors",
        seed=456,
    )

    assert workflow["5"]["inputs"]["text"].startswith("A cat astronaut")
    assert workflow["2"]["inputs"]["text"] == "text, watermark, malformed motion"
    assert workflow["8"]["inputs"]["seed"] == 456
    assert workflow["11"]["class_type"] == "SaveVideo"
    assert workflow["11"]["inputs"]["format"] == "mp4"
