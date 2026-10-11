import os
from pathlib import Path

import pytest

from app.integrations.comfyui.client import ComfyUIClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_COMFYUI_TESTS") != "1",
        reason="set RUN_COMFYUI_TESTS=1 with local ComfyUI running",
    ),
]


@pytest.mark.asyncio
async def test_comfyui_prompt_websocket_and_image_download(tmp_path: Path) -> None:
    client = ComfyUIClient(os.getenv("COMFYUI_BASE_URL", "http://localhost:8188"))
    template = client.load_workflow(
        Path(os.getenv("COMFYUI_WORKFLOW_PATH", "comfyui/workflows/text_to_image_api.json"))
    )
    workflow = client.prepare_workflow(
        template,
        prompt="a tiny orange cat walking in space, cinematic",
        negative_prompt="text, watermark, blurry",
        checkpoint=os.environ["COMFYUI_CHECKPOINT"],
        seed=42,
    )

    images = await client.generate_and_download(workflow, tmp_path)

    assert images
    assert all(path.is_file() and path.stat().st_size > 0 for path in images)
