from __future__ import annotations

import logging
import secrets
from pathlib import Path

from app.core.config import Settings
from app.integrations.comfyui.client import ComfyUIClient
from app.integrations.ffmpeg.composer import FFmpegComposer
from app.models.storyboard import StoryboardRequest
from app.services.storyboard_generator import StoryboardGenerator

logger = logging.getLogger(__name__)


async def run_pipeline(
    story: str,
    settings: Settings,
    *,
    output_path: Path = Path("output.mp4"),
    scene_count: int = 3,
) -> Path:
    logger.info("LLM：拆解故事並產生 %s 個結構化場景", scene_count)
    storyboard = await StoryboardGenerator(settings).generate(
        StoryboardRequest(
            story_outline=story,
            max_scenes=scene_count,
            target_duration_seconds=max(15, scene_count * 3),
        )
    )
    if len(storyboard.scenes) != scene_count:
        raise RuntimeError(
            f"Expected {scene_count} scenes but LLM returned {len(storyboard.scenes)}"
        )

    workflow_path = Path(settings.comfyui_workflow_path)
    template = ComfyUIClient.load_workflow(workflow_path)
    client = ComfyUIClient(settings.comfyui_base_url)
    job_dir = Path("data/jobs") / secrets.token_hex(8)
    images: list[Path] = []

    for index, scene in enumerate(storyboard.scenes, start=1):
        logger.info(
            "ComfyUI：生成圖片 %s/%s（%s，character_ref=%s）",
            index,
            scene_count,
            scene.scene_id,
            scene.character_ref,
        )
        workflow = client.prepare_workflow(
            template,
            prompt=scene.prompt,
            negative_prompt=scene.negative_prompt,
            checkpoint=settings.comfyui_checkpoint,
            seed=secrets.randbits(63),
        )
        generated = await client.generate_and_download(
            workflow,
            job_dir / scene.scene_id,
        )
        images.append(generated[0])

    logger.info("FFmpeg：串接 %s 張圖片", len(images))
    composer = FFmpegComposer()
    result = composer.compose_slideshow(
        images,
        output_path,
        seconds_per_image=3,
    )
    logger.info("完成：%s", result.resolve())
    return result
