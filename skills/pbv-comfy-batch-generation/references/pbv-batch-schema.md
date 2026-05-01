# PBV Batch JSON Schema

PBV accepts a JSON object:

```json
{
  "version": 1,
  "defaults": {
    "app": "flux",
    "prefix": "batch/project-name"
  },
  "jobs": [
    {
      "label": "subject",
      "prompt": "Prompt text"
    }
  ]
}
```

It also accepts an array of jobs or one raw Comfy API prompt object, but prefer the object shape above.

## Shared Fields

- `app`: `flux`, `god`, `wan`, `ati`, `seedvr2`, `upscale`, `trellis`, `ltx`, or `raw`.
- `mode`: model variant or workflow mode.
- `label`: short filename-safe label.
- `prompt`: positive prompt.
- `negative`: negative prompt.
- `prefix`: output prefix. PBV appends `/<job-number>-<label>`.
- `runs`: repeated runs of one job. Prefer separate jobs for different subjects.
- `seed`: numeric seed, or omit/use `-1` for random.
- `width`, `height`, `steps`, `cfg`, `fps`, `frames`: common generation settings.
- `outputFormat`: video output format, usually `mp4`, `mp4_10`, `mov`, or `png16`.
- `id`: stores a generated output under a stable name for later jobs.
- `saveAsInput`: optional; when true, PBV captures this job's output even if no later job references it.
- `waitForCompletion`: optional; defaults to `true` so PBV waits for each Comfy prompt and reports node errors. Set to `false` only for queue-only jobs.
- `sourceFrom`: shortcut for using a previous `id` as the main input of an app.

Use `id`, `sourceFrom`, or `$outputs.<id>` for app-only chains such as FLUX image first, TRELLIS model second. PBV queues apps in order, waits for app completion, uploads referenced non-3D media back into Comfy input, and does not merge apps into a custom workflow.

Output variables:

- `$outputs.<id>`: default input file for image/video-input app fields.
- `$outputs.<id>.inputFile`: uploaded Comfy input filename.
- `$outputs.<id>.path`: relative output path.
- `$outputs.<id>.url`: browser URL for the output.
- `$outputs.<id>.filename`: output filename.
- `$outputs.<id>.promptId`: Comfy prompt id.

Template style also works: `${outputs.<id>.path}`.

## FLUX

```json
{
  "app": "flux",
  "mode": "dev",
  "label": "car",
  "width": 2048,
  "height": 2048,
  "steps": 20,
  "cfg": 1,
  "guidance": 3.5,
  "sampler": "euler",
  "scheduler": "simple",
  "prompt": "A cinematic red sports car..."
}
```

Modes:

- `dev`: FLUX.1 Dev FP8, default `steps: 20`, `guidance: 3.5`.
- `schnell`: FLUX.1 Schnell FP8, default `steps: 4`, `guidance: 0`.
- `kontext`: FLUX Kontext edit FP8, requires `refImage`.

Optional FLUX fields: `lora`, `loraStrength`, `denoise`, `refImage`.

## God WAN22

```json
{
  "app": "god",
  "mode": "t2v",
  "label": "neon-city",
  "width": 1280,
  "height": 720,
  "frames": 81,
  "fps": 25,
  "steps": 30,
  "cfg": 1,
  "shift": 7,
  "blockSwap": 20,
  "prompt": "A slow rainy neon city dolly shot..."
}
```

Modes:

- `t2v`: text-only video.
- `i2v`: requires `startImage`.
- `flf`: requires `startImage` and `endImage`.
- `auto`: PBV selects `flf`, `i2v`, or `t2v` from provided images.

## WAN-FMLF

```json
{
  "app": "wan",
  "mode": "flf",
  "label": "product-turn",
  "startImage": "product_start.png",
  "endImage": "product_end.png",
  "width": 1280,
  "height": 720,
  "frames": 125,
  "prompt": "A controlled first-last-frame product camera move..."
}
```

For keyframes:

```json
{
  "app": "wan",
  "mode": "keyframes",
  "label": "three-beat-shot",
  "keyframes": [
    { "image": "shot_start.png", "frame": 1 },
    { "image": "shot_middle.png", "frame": 41 },
    { "image": "shot_end.png", "frame": 81 }
  ],
  "frames": 81,
  "prompt": "A smooth cinematic move through the three references..."
}
```

WAN frame counts must be aligned to `4n+1`; PBV rounds through its normal `wanFrameCount` helper.

## Other Apps

ATI:

```json
{
  "app": "ati",
  "label": "tracked-pan",
  "startImage": "frame.png",
  "startX": 416,
  "startY": 240,
  "endX": 560,
  "endY": 240,
  "prompt": "A subtle tracked camera move..."
}
```

SeedVR2:

```json
{
  "app": "seedvr2",
  "label": "upscale-shot",
  "video": "source.mp4",
  "resolution": 1080,
  "outputFormat": "mp4"
}
```

TRELLIS:

```json
{
  "app": "trellis",
  "label": "object-glb",
  "sourceImage": "object.png",
  "preset": "fast",
  "faces": 80000,
  "textureSize": 1024
}
```

TRELLIS batch defaults to `preset: "fast"` because GLB export can time out during UV parameterization on dense meshes. Use `preset: "balanced"` for about 160k faces, or `preset: "quality"` for the older 500k face / 2048 texture export. Override `faces`, `textureSize`, `resolution`, and step counts only when you need to.

LTX:

```json
{
  "app": "ltx",
  "label": "image-to-video",
  "startImage": "start.png",
  "endImage": "end.png",
  "duration": "10",
  "fps": 25,
  "prompt": "A smooth cinematic motion from the input image..."
}
```

Raw Comfy API prompt:

```json
{
  "app": "raw",
  "label": "custom-workflow",
  "workflow": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "model.safetensors"
      }
    }
  }
}
```

## Mixed Example

```json
{
  "version": 1,
  "defaults": {
    "prefix": "batch/mixed",
    "negative": "low quality, blurry, distorted, watermark, text, logo"
  },
  "jobs": [
    {
      "app": "flux",
      "mode": "dev",
      "label": "car",
      "width": 2048,
      "height": 2048,
      "prompt": "A cinematic high-detail image of a red electric sports car on a wet mountain road at sunrise."
    },
    {
      "app": "flux",
      "mode": "schnell",
      "label": "banana",
      "width": 1024,
      "height": 1024,
      "prompt": "A bright studio product photo of a ripe banana on a matte blue surface."
    },
    {
      "app": "god",
      "mode": "t2v",
      "label": "neon-city",
      "width": 1280,
      "height": 720,
      "frames": 81,
      "prompt": "A slow cinematic dolly shot through a rainy neon city street at night."
    }
  ]
}
```

## App-Only FLUX To TRELLIS Chain

```json
{
  "version": 1,
  "jobs": [
    {
      "app": "flux",
      "id": "banana-image",
      "label": "banana-image",
      "mode": "dev",
      "prompt": "Isolated ripe banana, full object visible, clean studio background."
    },
    {
      "app": "trellis",
      "label": "banana-3d",
      "sourceFrom": "banana-image",
      "preset": "fast"
    }
  ]
}
```

Equivalent explicit variable form:

```json
{
  "app": "trellis",
  "label": "banana-3d",
  "sourceImage": "$outputs.banana-image.inputFile",
  "preset": "fast"
}
```
