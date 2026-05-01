---
name: pbv-comfy-batch-generation
description: Create pasteable PBV Local AI Center Batch Generation JSON for ComfyUI. Use when the user asks to generate many images/videos/jobs at once, queue mixed models in one batch, make Flux/God WAN22/WAN/ATI/SeedVR2/TRELLIS/LTX requests, or produce API-style JSON that can be pasted into the PBV BATCH GENERATION text area.
---

# PBV Comfy Batch Generation

## Output Contract

Produce one valid JSON object that can be pasted directly into PBV Local AI Center's `BATCH GENERATION` tab. Do not include comments, trailing commas, Markdown inside the JSON, JavaScript, or prose inside the code block.

Use this top-level shape:

```json
{
  "version": 1,
  "defaults": {},
  "jobs": []
}
```

Put shared settings in `defaults`; put prompt-specific overrides in `jobs`. Each job can choose its own `app`, so one batch may mix image, video, upscale, 3D, LTX, and raw Comfy prompt requests.

## Workflow

1. Turn each requested subject, shot, variation, or prompt into one job unless the user explicitly asks for repeated runs of the same prompt.
2. Use concise `label` values for filenames and queue labels, such as `car`, `banana`, `city-wide`.
3. Use a stable `prefix`, normally `batch/<project-or-model>`, so outputs land in grouped folders.
4. For random seeds, omit `seed` or set `seed: -1`. For reproducible batches, set a numeric seed per job.
5. For image/video-input jobs, reference filenames already in Comfy input. Do not invent `startImage`, `endImage`, `sourceImage`, `video`, or `refImage` filenames.
6. If the user has not provided required file names for file-dependent jobs, either use a text-only app such as `flux` or `god` `t2v`, or ask for the Comfy input filenames.

## App Choices

Use `flux` for still images. Modes: `dev`, `schnell`, `kontext`. `kontext` requires `refImage`.

Use `god` for God WAN22 video. Modes: `t2v`, `i2v`, `flf`, `auto`. `t2v` needs no images; `i2v` needs `startImage`; `flf` needs `startImage` and `endImage`.

Use `wan` for WAN-FMLF image-to-video, first-last-frame, or keyframe jobs. It requires `startImage` or a `keyframes` array.

Use `ati` for motion-track image-to-video. It requires `startImage`.

Use `seedvr2` or `upscale` for video upscale. It requires `video`.

Use `trellis` for image-to-3D. It requires `sourceImage`. Prefer `preset: "fast"` for batches unless the user explicitly asks for high quality; dense GLB export can time out during UV parameterization.

Use `ltx` for LTX 2.3 image-to-video. It requires `startImage` and queues through the PBV LTX backend.

Use `raw` only when the user provides or requests a full Comfy API prompt object.

For exact field names and examples, read `references/pbv-batch-schema.md`.
