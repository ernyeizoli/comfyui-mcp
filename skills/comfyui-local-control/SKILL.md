---
name: comfyui-local-control
description: Control, inspect, and extend Zoltan's local ComfyUI RTX 5090 setup. Use when Codex needs to operate ComfyUI on this Windows machine, use or repair the Comfy MCP in C:\Users\zoltan.ernyei\dev\Comfy-mcp, expose or verify LAN access, queue workflows through the Comfy HTTP API, create LAN-facing Comfy app routes, manage D:\ComfyUI\models, or run the existing LTX2.3 30s I2V and Z-Image text-to-image workflows.
---

# ComfyUI Local Control

## First Checks

Start by reading `references/zoltan-comfy-machine.md` for the current paths, URLs, model folders, and known custom apps. Treat the reference as a map, not a source of truth: verify the running process and API before changing anything.

Check Comfy without restarting it:

```powershell
$base = "http://127.0.0.1:8188"
Invoke-RestMethod "$base/system_stats" -TimeoutSec 5
Invoke-RestMethod "$base/queue" -TimeoutSec 5
```

If `/queue` shows a running item, or `/kosz-ltx23-30s/status` reports `running: true`, do not restart or kill Comfy unless the user explicitly asks. Long video jobs can run for a long time and still be healthy.

## Control Path

Prefer the Comfy MCP when this Codex session exposes a `comfyui` MCP namespace. The MCP server is configured from `C:\Users\zoltan.ernyei\dev\Comfy-mcp\dist\index.js` and targets `127.0.0.1:8188`.

If the MCP namespace is unavailable, use Comfy's HTTP API directly. This is the normal fallback and is enough to upload images, queue workflow JSON, poll progress, inspect history, and retrieve outputs.

Use these endpoints first:

```text
GET  /system_stats
GET  /queue
POST /prompt
GET  /history/{prompt_id}
GET  /view?filename=...&type=output|input&subfolder=...
POST /upload/image
```

For workflow edits, export or build API-format workflow JSON and queue it through `/prompt`. Keep generated workflow files in the current Codex workspace unless the user asks to install them into Comfy.

## LAN And Apps

The intended launch mode binds Comfy to the LAN:

```text
--listen 0.0.0.0 --port 8188 --use-sage-attention --fast fp16_accumulation fp8_matrix_mult autotune
```

Verify local and LAN access separately. A local success does not prove the Windows firewall allows another machine in.

Build end-user LAN tools as Comfy custom nodes with standalone `aiohttp` routes. Prefer standalone pages such as `/ltx23-30s-i2v` over auto-loaded frontend extensions when a tool should be stable for nontechnical users. Auto-loaded JavaScript extensions can break the Comfy interface with repeated "Loading Error" toasts.

After installing or changing a custom node, restart Comfy only when the queue is idle. If a render is running, write an activator script that waits for `/queue` and any app-specific status endpoint to become idle before restarting.

## Model Handling

Use the shared model library at `D:\ComfyUI\models`. Do not duplicate large models into the portable Comfy install unless the user specifically asks. Confirm model visibility with `ComfyUI\extra_model_paths.yaml` and by checking the appropriate subfolder under `D:\ComfyUI\models`.

When a workflow fails because a model is missing, identify the exact loader node and expected subfolder before downloading. Put checkpoints, diffusion models, text encoders, VAEs, LoRAs, latent upscalers, and clip vision models in their matching folders so Comfy dropdowns resolve them.

## Safety Rules

Work with the portable install at `C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable`; do not switch to another Comfy install unless the user asks.

Before editing files outside the Codex workspace, request escalation. Stage manual edits in the current workspace with `apply_patch`, then copy them into the Comfy or MCP directory with an escalated `Copy-Item`.

Do not overwrite unrelated user workflows, output videos, model files, or custom node edits. If the Comfy process is busy, report the status and continue with noninterrupting work.

## Validation

After any setup change, verify:

```powershell
Invoke-RestMethod "http://127.0.0.1:8188/system_stats" -TimeoutSec 5
Invoke-RestMethod "http://127.0.0.1:8188/queue" -TimeoutSec 5
Invoke-WebRequest "http://10.10.101.122:8188/" -TimeoutSec 5
```

For custom app routes, check both local and LAN URLs. For generated media, inspect the output path and use `ffprobe` or a contact sheet when duration, frame count, or resolution matters.
