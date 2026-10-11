# AI Video Drama Platform

An initial backend skeleton for turning a story outline into a validated
storyboard, then orchestrating ComfyUI and FFmpeg in later stages.

## Architecture

```text
Story outline
    │
    ▼
FastAPI / CLI
    │
    ▼
OpenAI Structured Outputs + Pydantic
    │  validated scenes: scene_id, prompt, character_ref
    ▼
ComfyUI REST + WebSocket
    │  generated PNG frames
    ▼
FFmpeg
    │
    ▼
output.mp4
```

FastAPI exposes the application boundary, Pydantic is the contract between the
LLM and generation layer, ComfyUI owns local image inference, and FFmpeg owns
deterministic media assembly. Provider-specific generation is isolated under
`app/integrations`, so a hosted image/video API can be added without changing
the storyboard schema or editing pipeline.

## Directory structure

```text
ai-video-drama-platform/
├── app/
│   ├── api/routes.py                  # FastAPI endpoints
│   ├── core/config.py                 # Environment configuration
│   ├── models/storyboard.py           # Pydantic storyboard contract
│   ├── services/storyboard_generator.py # Structured LLM generation
│   ├── integrations/
│   │   ├── comfyui/client.py          # REST/WebSocket client
│   │   └── ffmpeg/composer.py         # Image-to-MP4 composition
│   ├── workers/                       # Background task orchestration
│   └── main.py
├── comfyui/workflows/                 # ComfyUI API workflow templates
├── data/                              # Runtime inputs, outputs and job data
├── tests/
│   ├── unit/                          # Offline schema/workflow tests
│   ├── integration/                   # ComfyUI and FFmpeg tests
│   ├── live/                          # Opt-in real LLM test
│   └── e2e/                           # Opt-in golden path
├── main.py                            # End-to-end CLI
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Run locally

```bash
cp .env.example .env
# Set OPENAI_API_KEY in .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

To run the offline unit tests:

```bash
pip install -r requirements-dev.txt
pytest tests/unit -q
```

Open `http://localhost:8000/docs`, or run the standalone example:

```bash
python -m app.services.storyboard_generator
```

### How users enter a story

There is no browser frontend in v0.1 yet. Users can enter a story through the
CLI for the complete video pipeline, or through FastAPI for storyboard-only
generation.

**Option A — CLI: generate the complete MP4**

Pass the story directly to `--story`:

```bash
python main.py \
  --story "一隻貓在太空漫步，追逐漂浮在太空站外的紅色毛線球。" \
  --output my-cat-video.mp4
```

The `--story` value is sent to the LLM, converted into three typed scenes,
rendered through ComfyUI, and assembled into the selected output file.

**Option B — Swagger UI: inspect structured storyboard generation**

Start the API with `uvicorn app.main:app --reload`, open
`http://localhost:8000/docs`, expand `POST /api/v1/storyboards/generate`, click
**Try it out**, and enter:

```json
{
  "story_outline": "一隻貓在太空漫步，追逐漂浮在太空站外的紅色毛線球。",
  "genre": "science fiction",
  "visual_style": "cinematic realism",
  "aspect_ratio": "9:16",
  "target_duration_seconds": 30,
  "max_scenes": 3
}
```

The same storyboard endpoint can be called directly:

```bash
curl -X POST http://localhost:8000/api/v1/storyboards/generate \
  -H "Content-Type: application/json" \
  -d '{
    "story_outline": "一隻貓在太空漫步，追逐漂浮在太空站外的紅色毛線球。",
    "max_scenes": 3
  }'
```

This API endpoint currently returns validated storyboard JSON only. Use the
CLI when you want ComfyUI generation and the final MP4 in one command.

### Generate your own MP4

1. Install and start ComfyUI. On Apple Silicon, use a native macOS ComfyUI
   installation so it can use MPS.
2. Put a compatible checkpoint in ComfyUI's `models/checkpoints` directory.
3. Copy `.env.example` to `.env`, set `OPENAI_API_KEY`, set
   `COMFYUI_CHECKPOINT` to the exact checkpoint filename, and keep
   `COMFYUI_BASE_URL=http://localhost:8188` for a native local server.
4. Run:

```bash
python main.py --story "一隻貓在太空漫步，追逐漂浮在太空站外的紅色毛線球。"
```

The pipeline requests three typed scenes, generates one image per scene, and
writes `output.mp4`. Replace `comfyui/workflows/text_to_image_api.json` with an
API-format workflow containing the same placeholders to use another checkpoint
or node graph.

## Run with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

The API is exposed on port 8000 and the placeholder ComfyUI service on 8188.
The default ComfyUI image is only a portable placeholder: set
`COMFYUI_IMAGE` and GPU device settings to match the deployment host.

## Test layers

The default unit suite does not make API calls. It verifies that the typed LLM
boundary returns `scene_id`, `prompt`, and `character_ref`, rejects prefixed or
unknown JSON data, and injects values into a ComfyUI workflow without mutating
the template.

Run the real LLM contract test explicitly (this uses API credits):

```bash
RUN_LIVE_LLM_TESTS=1 pytest tests/live/test_agent_live.py -q
```

The included `text_to_image_api.json` is a minimal checkpoint-based workflow.
Set `COMFYUI_CHECKPOINT` to the exact filename shown in ComfyUI, start ComfyUI
on port 8188, then test the `/prompt` plus WebSocket plus `/view` round trip:

```bash
COMFYUI_CHECKPOINT=your-model.safetensors \
RUN_COMFYUI_TESTS=1 \
pytest tests/integration/test_comfyui.py -q -s
```

The FFmpeg integration test creates three synthetic images and validates a
non-empty MP4:

```bash
pytest tests/integration/test_ffmpeg.py -q
```

## Golden path

After configuring `.env`, starting local ComfyUI, and confirming the selected
checkpoint loads correctly (including MPS on macOS), run:

```bash
python main.py --story "一隻貓在太空漫步，追逐漂浮在太空站外的紅色毛線球。"
```

The terminal logs each boundary: LLM structured scenes, three ComfyUI jobs,
and FFmpeg composition. Acceptance is a non-empty `output.mp4`. The same path
is available as an opt-in automated test:

```bash
RUN_E2E_TESTS=1 pytest tests/e2e/test_golden_path.py -q -s
```

For Apple Silicon/MPS validation, run ComfyUI natively on macOS and execute the
CLI/tests from the host with `COMFYUI_BASE_URL=http://localhost:8188`. Docker
Desktop containers do not expose Apple's MPS backend; the Compose ComfyUI
service is therefore a deployment placeholder, not the MPS acceptance path.

## Cost model

Estimates below were checked on 2026-10-11 and exclude electricity, storage,
tax and retries. Always verify the linked provider catalog before production.

- Story planning uses one `gpt-4o-mini` request. At $0.15 per million input
  tokens and $0.60 per million output tokens, a typical three-scene storyboard
  using roughly 800–1,500 input and 1,500–3,000 output tokens costs about
  **$0.001–$0.002**. See the [official model pricing](https://developers.openai.com/api/docs/models/gpt-4o-mini).
- Local ComfyUI generation has **no per-image API charge**. The cost is the
  user's hardware time and electricity. FFmpeg is also local and token-free.
- A future hosted provider changes the economics. The current Higgsfield
  catalog includes example image models around **$0.0032–$0.06 per image** and
  video models priced per generated second. Three five-second clips can range
  from well under $1 to several dollars depending on model, resolution, audio,
  and discounts. See the [live Higgsfield catalog](https://higgsfield.ai/higgsfield-api).

In the repository's current default path, almost all metered cost is the small
storyboard LLM call; pixels and MP4 assembly run locally.
