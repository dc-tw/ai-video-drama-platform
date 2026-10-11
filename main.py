from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.models.storyboard import Storyboard
from app.services.pipeline import render_storyboard, run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI short-drama generation pipeline")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--story", help="Story outline; requires OPENAI_API_KEY")
    source.add_argument(
        "--storyboard",
        type=Path,
        help="Validated storyboard JSON; bypasses the LLM and OpenAI",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output.mp4"),
        help="Final MP4 path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    settings = get_settings()
    if args.storyboard is not None:
        storyboard = Storyboard.model_validate_json(
            args.storyboard.read_text(encoding="utf-8")
        )
        asyncio.run(render_storyboard(storyboard, settings, output_path=args.output))
    else:
        asyncio.run(run_pipeline(args.story, settings, output_path=args.output))


if __name__ == "__main__":
    main()
