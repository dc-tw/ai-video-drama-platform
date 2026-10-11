from __future__ import annotations

import asyncio
import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import httpx
import websockets


class ComfyUIError(RuntimeError):
    """Raised when ComfyUI rejects or fails a workflow."""


class ComfyUIClient:
    def __init__(self, base_url: str, timeout_seconds: float = 300) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def load_workflow(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def prepare_workflow(
        template: dict[str, Any],
        *,
        prompt: str,
        negative_prompt: str,
        checkpoint: str,
        seed: int,
    ) -> dict[str, Any]:
        replacements: dict[str, Any] = {
            "__PROMPT__": prompt,
            "__NEGATIVE_PROMPT__": negative_prompt,
            "__CHECKPOINT__": checkpoint,
            "__SEED__": seed,
        }

        def replace(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: replace(item) for key, item in value.items()}
            if isinstance(value, list):
                return [replace(item) for item in value]
            return replacements.get(value, value)

        return replace(deepcopy(template))

    async def generate_and_download(
        self,
        workflow: dict[str, Any],
        output_dir: Path,
    ) -> list[Path]:
        client_id = uuid.uuid4().hex
        websocket_url = self._websocket_url(client_id)

        async with websockets.connect(websocket_url, open_timeout=10) as websocket:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            ) as client:
                prompt_id = await self._queue_prompt(client, workflow, client_id)
                await self._wait_for_success(websocket, prompt_id)
                images = await self._get_output_images(client, prompt_id)
                return await self._download_images(client, images, output_dir)

    def _websocket_url(self, client_id: str) -> str:
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        query = urlencode({"clientId": client_id})
        return urlunparse((scheme, parsed.netloc, "/ws", "", query, ""))

    async def _queue_prompt(
        self,
        client: httpx.AsyncClient,
        workflow: dict[str, Any],
        client_id: str,
    ) -> str:
        response = await client.post(
            "/prompt",
            json={"prompt": workflow, "client_id": client_id},
        )
        response.raise_for_status()
        payload = response.json()
        prompt_id = payload.get("prompt_id")
        if not isinstance(prompt_id, str):
            raise ComfyUIError(f"Missing prompt_id in ComfyUI response: {payload}")
        return prompt_id

    async def _wait_for_success(self, websocket: Any, prompt_id: str) -> None:
        async def receive_events() -> None:
            while True:
                message = await websocket.recv()
                if isinstance(message, bytes):
                    continue
                event = json.loads(message)
                event_type = event.get("type")
                data = event.get("data", {})
                if data.get("prompt_id") != prompt_id:
                    continue
                if event_type in {"execution_error", "execution_interrupted"}:
                    raise ComfyUIError(f"ComfyUI execution failed: {event}")
                if event_type == "execution_success":
                    return
                if event_type == "executing" and data.get("node") is None:
                    return

        try:
            await asyncio.wait_for(receive_events(), timeout=self.timeout_seconds)
        except TimeoutError as exc:
            raise ComfyUIError(
                f"Timed out waiting for ComfyUI prompt {prompt_id}"
            ) from exc

    async def _get_output_images(
        self,
        client: httpx.AsyncClient,
        prompt_id: str,
    ) -> list[dict[str, str]]:
        response = await client.get(f"/history/{prompt_id}")
        response.raise_for_status()
        history = response.json().get(prompt_id, {})
        images: list[dict[str, str]] = []
        for output in history.get("outputs", {}).values():
            for image in output.get("images", []):
                if isinstance(image.get("filename"), str):
                    images.append(image)
        if not images:
            raise ComfyUIError(f"Prompt {prompt_id} completed without output images")
        return images

    async def _download_images(
        self,
        client: httpx.AsyncClient,
        images: list[dict[str, str]],
        output_dir: Path,
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for index, image in enumerate(images, start=1):
            response = await client.get(
                "/view",
                params={
                    "filename": image["filename"],
                    "subfolder": image.get("subfolder", ""),
                    "type": image.get("type", "output"),
                },
            )
            response.raise_for_status()
            suffix = Path(image["filename"]).suffix or ".png"
            path = output_dir / f"image_{index:03d}{suffix}"
            path.write_bytes(response.content)
            paths.append(path)
        return paths
