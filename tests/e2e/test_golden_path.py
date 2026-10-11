import os
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.services.pipeline import run_pipeline

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.getenv("RUN_E2E_TESTS") != "1",
        reason="set RUN_E2E_TESTS=1 with OpenAI, ComfyUI and FFmpeg configured",
    ),
]


@pytest.mark.asyncio
async def test_cat_in_space_golden_path(tmp_path: Path) -> None:
    output = await run_pipeline(
        "一隻橘貓穿著白色太空衣，在太空站外緩慢漫步，最後追上漂浮的紅色毛線球。",
        get_settings(),
        output_path=tmp_path / "output.mp4",
        scene_count=3,
    )

    assert output.is_file()
    assert output.stat().st_size > 0
