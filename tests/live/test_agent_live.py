import os

import pytest

from app.core.config import get_settings
from app.models.storyboard import StoryboardRequest
from app.services.storyboard_generator import StoryboardGenerator

pytestmark = [
    pytest.mark.live_llm,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_LLM_TESTS") != "1",
        reason="set RUN_LIVE_LLM_TESTS=1 to spend API credits",
    ),
]


@pytest.mark.asyncio
async def test_real_llm_returns_required_scene_contract() -> None:
    result = await StoryboardGenerator(get_settings()).generate(
        StoryboardRequest(
            story_outline="一隻橘貓穿著白色太空衣，在太空站外追逐漂浮的紅色毛線球。",
            max_scenes=3,
        )
    )

    assert len(result.scenes) == 3
    for scene in result.scenes:
        assert scene.scene_id
        assert scene.prompt
        assert isinstance(scene.character_ref, list)
