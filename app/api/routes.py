from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.models.storyboard import Storyboard, StoryboardRequest
from app.services.storyboard_generator import StoryboardGenerator

router = APIRouter()


@router.post("/storyboards/generate", response_model=Storyboard)
async def generate_storyboard(
    request: StoryboardRequest,
    settings: Settings = Depends(get_settings),
) -> Storyboard:
    generator = StoryboardGenerator(settings=settings)
    return await generator.generate(request)
