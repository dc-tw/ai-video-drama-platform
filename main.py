from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.services.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI short-drama generation pipeline")
    parser.add_argument("--story", required=True, help="Story outline")
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
    asyncio.run(run_pipeline(args.story, get_settings(), output_path=args.output))


if __name__ == "__main__":
    main()
