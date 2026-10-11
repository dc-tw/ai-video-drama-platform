# Kandinsky 5.0 T2V workflow

This directory contains two representations of the same 5-second text-to-video
pipeline:

- `kandinsky5_t2v_ui.json`: the official ComfyUI template with node positions,
  notes, groups and model download metadata. Drag this file into ComfyUI to see
  and edit the graph.
- `kandinsky5_t2v_api.json`: the flattened API graph intended for `POST /prompt`.
  It contains `__PROMPT__`, `__NEGATIVE_PROMPT__`, and `__SEED__` placeholders
  understood by this project's `ComfyUIClient.prepare_workflow()` method.

The UI template is copied from the official
[`Comfy-Org/workflow_templates`](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_kandinsky5_t2v.json)
repository. The current API graph was flattened from that template; validate it
against the exact ComfyUI version you install before treating it as production.

## Required models

Download and place the files at these exact paths:

```text
ComfyUI/
└── models/
    ├── text_encoders/
    │   ├── qwen_2.5_vl_7b_fp8_scaled.safetensors
    │   └── clip_l.safetensors
    ├── diffusion_models/
    │   └── kandinsky5lite_t2v_sft_5s.safetensors
    └── vae/
        └── hunyuan_video_vae_bf16.safetensors
```

Model download URLs are embedded in the UI template's **For Local User** note.
The files total roughly 13.7 GB. Generation memory usage is additional.

## Inspect the UI

Use either route:

1. Drag `kandinsky5_t2v_ui.json` onto the ComfyUI canvas.
2. In an up-to-date ComfyUI, open **Workflows → Browse Templates → Video** and
   search for **Kandinsky 5.0 Video Lite Text to Video**.

The visible graph groups model loading, positive/negative prompts, latent video
creation, sampling, VAE decoding, frame-to-video conversion and MP4 saving.

The official model is documented for English and Russian prompts. Prefer an
English generation prompt even if the storyboard metadata is written in
Chinese.

## Important integration status

This workflow has been added locally, but it has not been rendered on this
machine because no local ComfyUI installation or required model files were
found. The repository's current `ComfyUIClient` also downloads image outputs
only. Before the application can run this graph end to end, add video result
parsing/downloading and a video-mode pipeline; do not simply point the existing
image pipeline at this file.
