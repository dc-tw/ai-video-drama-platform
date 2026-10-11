from pathlib import Path

from app.core.config import Settings
from app.models.storyboard import Storyboard


def test_manual_storyboard_is_valid_without_openai_key() -> None:
    storyboard = Storyboard.model_validate_json(
        Path("examples/manual_storyboard.json").read_text(encoding="utf-8")
    )
    settings = Settings(openai_api_key=None)

    assert settings.openai_api_key is None
    assert [scene.scene_id for scene in storyboard.scenes] == [
        "scene_001",
        "scene_002",
        "scene_003",
    ]
    assert [scene.duration_seconds for scene in storyboard.scenes] == [3, 4, 3]
