from typing import Any

from openai import AsyncOpenAI

from app.core.config import Settings
from app.models.storyboard import Storyboard, StoryboardRequest

SYSTEM_PROMPT = """
You are a film director and storyboard planner for short vertical dramas.
Turn the supplied outline into a production-ready storyboard.

Rules:
- Keep character_id values stable in the character bible and all shots.
- Preserve each character's canonical visual traits across image prompts.
- Make every scene a single independently renderable image.
- Put lens, lighting, composition, character traits, environment and style in
  each prompt. Do not put dialogue or subtitles in prompts.
- Use dialogue sparingly and keep the total runtime close to the requested one.
- Use sequential scene_id values starting at scene_001.
- Put every visible character ID in character_ref.
- Return only data that conforms to the requested schema.
""".strip()


class StoryboardGenerationError(RuntimeError):
    """Raised when the model cannot return a usable storyboard."""


class StoryboardGenerator:
    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self._model = settings.openai_model
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, request: StoryboardRequest) -> Storyboard:
        response = await self._client.responses.parse(
            model=self._model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_prompt(request),
                },
            ],
            text_format=Storyboard,
        )

        if response.output_parsed is None:
            raise StoryboardGenerationError(
                "The LLM returned no parsed storyboard; inspect refusal or incomplete output."
            )
        return response.output_parsed

    @staticmethod
    def _build_user_prompt(request: StoryboardRequest) -> str:
        return (
            f"Story outline:\n{request.story_outline}\n\n"
            f"Genre: {request.genre}\n"
            f"Visual style: {request.visual_style}\n"
            f"Aspect ratio: {request.aspect_ratio}\n"
            f"Target runtime: {request.target_duration_seconds} seconds\n"
            f"Create exactly {request.max_scenes} scenes."
        )


async def example() -> None:
    """Minimal standalone example: `python -m app.services.storyboard_generator`."""
    from app.core.config import get_settings

    request = StoryboardRequest(
        story_outline=(
            "A courier discovers that the final package of her night shift contains "
            "a voice message recorded by her future self, warning her not to make the delivery."
        ),
        genre="science-fiction thriller",
        visual_style="neon noir, grounded cinematic realism",
        target_duration_seconds=60,
    )
    storyboard = await StoryboardGenerator(get_settings()).generate(request)
    print(storyboard.model_dump_json(indent=2))


if __name__ == "__main__":
    import asyncio

    asyncio.run(example())
