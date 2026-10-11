import shutil
from pathlib import Path

import pytest

from app.integrations.ffmpeg.composer import FFmpegComposer

pytestmark = pytest.mark.integration


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_ffmpeg_combines_three_images_into_mp4(tmp_path: Path) -> None:
    images: list[Path] = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for index, color in enumerate(colors, start=1):
        image = tmp_path / f"frame_{index}.ppm"
        pixels = " ".join(f"{color[0]} {color[1]} {color[2]}" for _ in range(16))
        image.write_text(f"P3\n4 4\n255\n{pixels}\n", encoding="ascii")
        images.append(image)

    output = FFmpegComposer().compose_slideshow(
        images,
        tmp_path / "output.mp4",
        seconds_per_image=0.2,
        width=64,
        height=64,
        fps=10,
    )

    assert output.is_file()
    assert output.stat().st_size > 0
