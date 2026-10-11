from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model that rejects fields outside the agreed data contract."""

    model_config = ConfigDict(extra="forbid")


class ShotSize(str, Enum):
    extreme_wide = "extreme_wide"
    wide = "wide"
    medium = "medium"
    close_up = "close_up"
    extreme_close_up = "extreme_close_up"


class CameraMovement(str, Enum):
    static = "static"
    pan = "pan"
    tilt = "tilt"
    dolly = "dolly"
    tracking = "tracking"
    handheld = "handheld"


class Dialogue(StrictModel):
    speaker: str = Field(description="Character name or 'narrator'.")
    line: str = Field(description="The spoken line, ready for TTS.")
    emotion: str = Field(description="Short delivery direction for the voice model.")


class CharacterAppearance(StrictModel):
    character_id: str = Field(description="Stable ID reused across every shot.")
    name: str
    visual_description: str = Field(
        description="Canonical appearance, wardrobe, age, hair and distinguishing details."
    )
    reference_image_id: str | None = Field(
        default=None,
        description="Future IP-Adapter reference asset ID.",
    )


class Scene(StrictModel):
    scene_id: str = Field(description="Stable ID, for example scene_001.")
    duration_seconds: float = Field(ge=1, le=15)
    location: str
    time_of_day: str
    character_ref: list[str] = Field(
        description="Character IDs visible in this scene and used for IP-Adapter lookup."
    )
    action: str = Field(description="Only actions visible on screen.")
    shot_size: ShotSize
    camera_movement: CameraMovement
    dialogue: list[Dialogue]
    prompt: str = Field(
        description="Positive prompt passed directly to the ComfyUI workflow."
    )
    negative_prompt: str = Field(
        description="Artifacts and visual properties to avoid."
    )


class Storyboard(StrictModel):
    title: str
    logline: str
    visual_style: str
    aspect_ratio: str = Field(description="For example, 9:16.")
    characters: list[CharacterAppearance] = Field(min_length=1)
    scenes: list[Scene] = Field(min_length=1)


class StoryboardRequest(StrictModel):
    story_outline: str = Field(min_length=20)
    genre: str = "drama"
    visual_style: str = "cinematic realism"
    aspect_ratio: str = "9:16"
    target_duration_seconds: int = Field(default=60, ge=15, le=180)
    max_scenes: int = Field(default=4, ge=1, le=8)
