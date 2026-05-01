# Zoltan ComfyUI Machine Reference

Use this as a machine-specific runbook. Verify live state before acting; paths and jobs can change.

## Core Install

- Portable Comfy root: `C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable`
- ComfyUI package root: `C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\ComfyUI`
- Embedded Python: `C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\python_embeded\python.exe`
- Intended LAN URL: `http://10.10.101.122:8188`
- Local URL: `http://127.0.0.1:8188`
- Central models root: `D:\ComfyUI\models`
- Model mapping file: `C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\ComfyUI\extra_model_paths.yaml`

Typical launch command:

```powershell
Set-Location "C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable"
.\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --listen 0.0.0.0 --port 8188 --use-sage-attention --fast fp16_accumulation fp8_matrix_mult autotune
```

LAN launcher:

```text
C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\run_nvidia_gpu_lan_5090_fast.bat
```

If another LAN machine cannot connect while local access works, Windows Firewall may still need an admin rule:

```powershell
New-NetFirewallRule -DisplayName "ComfyUI 8188 LAN" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8188 -Profile Domain,Private
```

## MCP Setup

Comfy MCP repo:

```text
C:\Users\zoltan.ernyei\dev\Comfy-mcp
```

Codex config entry:

```toml
[mcp_servers.comfyui]
command = "node"
args = ["C:/Users/zoltan.ernyei/dev/Comfy-mcp/dist/index.js"]

[mcp_servers.comfyui.env]
COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = "8188"
COMFYUI_PATH = "C:/Users/zoltan.ernyei/Comfy_portable/ComfyUI_windows_portable/ComfyUI"
```

Current Codex sessions may not hot-load newly added MCP servers. If no `comfyui` MCP namespace is available, use the HTTP API directly.

## Custom LAN Apps

Installed custom nodes:

```text
C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\ComfyUI\custom_nodes\kosz_ltx23_30s_app
C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\ComfyUI\custom_nodes\z_image_t2i_app
```

Routes:

```text
http://10.10.101.122:8188/ltx23-30s-i2v
http://10.10.101.122:8188/z-image-t2i
```

LTX app status endpoint:

```text
http://127.0.0.1:8188/kosz-ltx23-30s/status
```

The Z-Image route only appears after Comfy restarts with the custom node loaded. If a long LTX render is active, do not force the restart; use or check the activator script:

```text
C:\Users\zoltan.ernyei\Documents\Codex\2026-04-30\is-there-a-comfyui-mcp-do\Activate-ZImageAppAfterQueueIdle.ps1
C:\Users\zoltan.ernyei\Documents\Codex\2026-04-30\is-there-a-comfyui-mcp-do\z_image_app_activation.log
```

## Known Models

LTX2.3:

```text
D:\ComfyUI\models\checkpoints\ltx-2.3-22b-dev-fp8.safetensors
D:\ComfyUI\models\checkpoints\ltx-2.3-22b-distilled-fp8.safetensors
D:\ComfyUI\models\text_encoders\gemma_3_12B_it_fp4_mixed.safetensors
D:\ComfyUI\models\loras\ltx-2.3-22b-distilled-lora-384.safetensors
D:\ComfyUI\models\loras\gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors
D:\ComfyUI\models\latent_upscale_models\ltx-2.3-spatial-upscaler-x2-1.0.safetensors
D:\ComfyUI\models\latent_upscale_models\ltx-2.3-spatial-upscaler-x2-1.1.safetensors
```

Wan2.2:

```text
D:\ComfyUI\models\diffusion_models\wan2.2_fun_control_high_noise_14B_fp8_scaled.safetensors
D:\ComfyUI\models\diffusion_models\wan2.2_fun_control_low_noise_14B_fp8_scaled.safetensors
D:\ComfyUI\models\diffusion_models\wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
D:\ComfyUI\models\diffusion_models\wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
D:\ComfyUI\models\diffusion_models\wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors
D:\ComfyUI\models\vae\wan_2.1_vae.safetensors
D:\ComfyUI\models\text_encoders\umt5_xxl_fp16.safetensors
D:\ComfyUI\models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors
D:\ComfyUI\models\clip_vision\clip_vision_h.safetensors
D:\ComfyUI\models\clip_vision\sigclip_vision_patch14_384.safetensors
```

Z-Image:

```text
D:\ComfyUI\models\diffusion_models\z_image_turbo_bf16.safetensors
D:\ComfyUI\models\text_encoders\qwen_3_4b.safetensors
D:\ComfyUI\models\vae\ae.safetensors
```

## Known Workflows

LTX2.3 30 second I2V uses chained segments because single-shot 30 second generation is impractical. Existing helper files in the Codex workspace include `queue_ltx23_long_segment.mjs` and several `ltx23_long_seg*_api_workflow.json` files. The LAN app wraps this pattern for end users.

Previously generated final 30 second LTX output:

```text
C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\ComfyUI\output\video\kosz_ltx23_moodboard_v2_30s.mp4
```

Z-Image workflow source:

```text
C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\ComfyUI\user\default\workflows\image_z_image_turbo_cont.json
```

Important Z-Image nodes and settings:

```text
UNETLoader: z_image_turbo_bf16.safetensors
CLIPLoader: qwen_3_4b.safetensors, type lumina2
VAELoader: ae.safetensors
KSampler: steps 3, cfg 1, sampler res_multistep, scheduler simple, denoise 1
```

## Useful PowerShell Checks

```powershell
$base = "http://127.0.0.1:8188"
Invoke-RestMethod "$base/system_stats" -TimeoutSec 5
Invoke-RestMethod "$base/queue" -TimeoutSec 5
Invoke-RestMethod "$base/kosz-ltx23-30s/status" -TimeoutSec 5
Invoke-WebRequest "http://127.0.0.1:8188/ltx23-30s-i2v" -TimeoutSec 5
Invoke-WebRequest "http://10.10.101.122:8188/ltx23-30s-i2v" -TimeoutSec 5
```

Find the running Comfy process:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match "ComfyUI\\main.py" } |
  Select-Object ProcessId,CommandLine
```

Inspect generated video:

```powershell
ffprobe -v error -show_entries stream=width,height,r_frame_rate,nb_frames -show_entries format=duration -of default=nw=1 "path\to\video.mp4"
```
