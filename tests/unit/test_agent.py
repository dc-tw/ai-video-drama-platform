from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.models.storyboard import Storyboard, StoryboardRequest
from app.services.storyboard_generator import StoryboardGenerator


def sample_storyboard() -> Storyboard:
    return Storyboard.model_validate(
        {
            "title": "太空貓",
            "logline": "一隻貓踏出太空站，追逐漂浮的紅色毛線球。",
            "visual_style": "cinematic science fiction",
            "aspect_ratio": "9:16",
            "characters": [
                {
                    "character_id": "cat_01",
                    "name": "小橘",
                    "visual_description": "orange tabby cat in a small white spacesuit",
                    "reference_image_id": "cat_ref.png",
                }
            ],
            "scenes": [
                {
                    "scene_id": "scene_001",
                    "duration_seconds": 3,
                    "location": "outside a space station",
                    "time_of_day": "orbital sunrise",
                    "character_ref": ["cat_01"],
                    "action": "The cat walks slowly along the hull.",
                    "shot_size": "wide",
                    "camera_movement": "tracking",
                    "dialogue": [],
                    "prompt": "Orange tabby astronaut walking on a space station hull",
                    "negative_prompt": "text, watermark, extra limbs",
                }
            ],
        }
    )


class FakeResponses:
    def __init__(self, output: Storyboard) -> None:
        self.output = output
        self.kwargs: dict[str, object] = {}

    async def parse(self, **kwargs: object) -> SimpleNamespace:
        self.kwargs = kwargs
        return SimpleNamespace(output_parsed=self.output)


class FakeClient:
    def __init__(self, output: Storyboard) -> None:
        self.responses = FakeResponses(output)


@pytest.mark.asyncio
async def test_agent_returns_typed_comfyui_fields_without_text_parsing() -> None:
    expected = sample_storyboard()
    client = FakeClient(expected)
    generator = StoryboardGenerator(
        Settings(openai_api_key="test-key"),
        client=client,
    )

    result = await generator.generate(
        StoryboardRequest(story_outline="一隻橘貓穿著太空衣，在太空站外追逐漂浮的紅色毛線球。")
    )

    scene = result.model_dump()["scenes"][0]
    assert isinstance(scene["scene_id"], str)
    assert isinstance(scene["prompt"], str)
    assert isinstance(scene["character_ref"], list)
    assert all(isinstance(item, str) for item in scene["character_ref"])
    assert client.responses.kwargs["text_format"] is Storyboard


def test_storyboard_rejects_non_json_prefix_and_unknown_fields() -> None:
    valid_json = sample_storyboard().model_dump_json()
    with pytest.raises(ValidationError):
        Storyboard.model_validate_json(f"Here is your JSON: {valid_json}")

    invalid = sample_storyboard().model_dump()
    invalid["scenes"][0]["unexpected"] = "noise"
    with pytest.raises(ValidationError):
        Storyboard.model_validate(invalid)
