from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    """Raised when FFmpeg cannot produce the requested video."""


class FFmpegComposer:
    def __init__(self, binary: str = "ffmpeg") -> None:
        resolved = shutil.which(binary)
        if resolved is None:
            raise FFmpegError(f"FFmpeg binary not found: {binary}")
        self.binary = resolved

    def compose_slideshow(
        self,
        images: list[Path],
        output_path: Path,
        *,
        seconds_per_image: float = 2.0,
        durations: list[float] | None = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> Path:
        if not images:
            raise ValueError("At least one image is required")
        for image in images:
            if not image.is_file():
                raise FileNotFoundError(image)
        if durations is not None and len(durations) != len(images):
            raise ValueError("durations must contain one value per image")
        frame_durations = durations or [seconds_per_image] * len(images)
        if any(duration <= 0 for duration in frame_durations):
            raise ValueError("all image durations must be greater than zero")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        concat_path = output_path.with_suffix(".concat.txt")
        lines: list[str] = []
        for image, duration in zip(images, frame_durations, strict=True):
            escaped = str(image.resolve()).replace("'", "'\\''")
            lines.extend([f"file '{escaped}'", f"duration {duration}"])
        last = str(images[-1].resolve()).replace("'", "'\\''")
        lines.append(f"file '{last}'")
        concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        video_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"fps={fps},format=yuv420p"
        )
        command = [
            self.binary,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFmpegError(result.stderr.strip())
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise FFmpegError("FFmpeg exited successfully but produced no video")
        return output_path
