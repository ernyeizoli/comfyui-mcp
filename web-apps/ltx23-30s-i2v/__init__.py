import json
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
import re
from pathlib import Path

from aiohttp import web

try:
    from server import PromptServer
except Exception:
    PromptServer = None


NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

COMFY_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = COMFY_DIR / "input"
OUTPUT_VIDEO_DIR = COMFY_DIR / "output" / "video"

DEFAULT_IMAGE = "kosz_moodboard_v2_03.png"
DEFAULT_PROMPT = (
    "Use the starting corridor image as the exact visual reference and first shot identity. "
    "Create a slow cinematic push-in forward down the abandoned concrete corridor toward the dark end, "
    "with gentle parallax and dimensional depth. Preserve the original composition, cracked concrete walls, "
    "right-side windows, damp floor, scattered debris, soft window light, gray-green gritty atmosphere, "
    "and dark vanishing point. Smooth continuous motion, high fidelity, realistic architectural texture, "
    "no cuts, no shake, no morphing."
)
CONTINUATION_PROMPT = (
    "Continue the same shot from this exact frame as the visual reference. Maintain a slow cinematic "
    "push-in forward through the abandoned concrete corridor toward the dark end, with gentle parallax "
    "and dimensional depth. Preserve the same cracked concrete walls, right-side windows, damp floor, "
    "scattered debris, soft window light, gray-green gritty atmosphere, and dark vanishing point. "
    "Smooth continuous motion, high fidelity, realistic architectural texture, no cuts, no shake, no morphing."
)
NEGATIVE_PROMPT = (
    "low quality, blurry, flicker, jitter, cuts, jump cut, fast zoom, camera shake, warping, melting, "
    "morphing, posters, moodboard, collage, portrait, person, face, typography, text, colorful squares, "
    "new unrelated scene, oversaturated colors, video game, cartoon, childish, ugly"
)

JOB_LOCK = threading.Lock()
JOB = {
    "running": False,
    "started": None,
    "completed": None,
    "error": None,
    "output": None,
    "output_url": None,
    "logs": [],
}


def _log(message):
    stamp = time.strftime("%H:%M:%S")
    with JOB_LOCK:
        JOB["logs"].append(f"[{stamp}] {message}")
        JOB["logs"] = JOB["logs"][-200:]


def _set_job(**updates):
    with JOB_LOCK:
        JOB.update(updates)


def _job_snapshot():
    with JOB_LOCK:
        return dict(JOB)


def _input_images():
    if not INPUT_DIR.exists():
        return []
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    return sorted(p.name for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() in allowed)


def _safe_upload_name(filename):
    suffix = Path(filename or "upload.png").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        suffix = ".png"
    stem = Path(filename or "upload").stem
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._-") or "upload"
    return f"ltx23_i2v_{time.strftime('%Y%m%d_%H%M%S')}_{stem[:40]}{suffix}"


APP_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LTX2.3 I2V</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, Segoe UI, system-ui, sans-serif; background: #111214; color: #f4f4f5; }
    body { margin: 0; min-height: 100vh; background: #111214; }
    .shell { max-width: 1180px; margin: 0 auto; padding: 24px; display: grid; gap: 18px; }
    header { display: flex; align-items: end; justify-content: space-between; gap: 16px; border-bottom: 1px solid #2d3035; padding-bottom: 14px; }
    h1 { margin: 0; font-size: 24px; line-height: 1.1; letter-spacing: 0; }
    .sub { margin: 6px 0 0; color: #a1a1aa; font-size: 13px; }
    main { display: grid; grid-template-columns: minmax(360px, 440px) 1fr; gap: 18px; align-items: start; }
    section { border: 1px solid #2d3035; border-radius: 8px; background: #18191c; }
    .panel { padding: 16px; display: grid; gap: 13px; }
    label { display: grid; gap: 6px; color: #d4d4d8; font-size: 13px; }
    input, select, textarea, button { font: inherit; }
    select, textarea, input[type=file] { width: 100%; box-sizing: border-box; border: 1px solid #3f3f46; border-radius: 6px; background: #24262b; color: #fff; padding: 9px; }
    textarea { min-height: 190px; resize: vertical; line-height: 1.45; }
    button { border: 1px solid #356fa8; border-radius: 6px; background: #2f7dd1; color: white; padding: 10px 12px; cursor: pointer; font-weight: 650; }
    button.secondary { background: #24262b; border-color: #3f3f46; }
    button:disabled { cursor: not-allowed; opacity: .55; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .drop { border: 1px dashed #565c68; border-radius: 8px; padding: 14px; color: #c4c7ce; background: #141519; }
    .status { min-height: 460px; padding: 16px; display: grid; gap: 12px; }
    .badge { display: inline-flex; width: fit-content; align-items: center; border: 1px solid #3f3f46; border-radius: 999px; padding: 5px 9px; color: #d4d4d8; background: #202226; font-size: 12px; }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; border-radius: 8px; background: #0b0c0e; color: #d4d4d8; padding: 12px; min-height: 220px; max-height: 360px; overflow: auto; }
    video { width: 100%; max-height: 520px; background: #050506; border-radius: 8px; }
    a { color: #8ec5ff; }
    @media (max-width: 840px) { main { grid-template-columns: 1fr; } .shell { padding: 14px; } }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1>LTX2.3 I2V</h1>
        <p class="sub">LAN app for LTX2.3 image-to-video generation on this RTX 5090 Comfy server.</p>
      </div>
      <a href="/" target="_blank">Open Comfy UI</a>
    </header>
    <main>
      <section class="panel">
        <label>Upload start image
          <div class="drop">
            <input id="file" type="file" accept="image/png,image/jpeg,image/webp">
          </div>
        </label>
        <div class="row">
          <button id="upload">Upload Image</button>
          <button class="secondary" id="refresh">Refresh</button>
        </div>
        <label>Start image in Comfy input
          <select id="image"></select>
        </label>
        <label>Prompt
          <textarea id="prompt"></textarea>
        </label>
        <label>Duration mode
          <select id="duration">
            <option value="5">5s at 25 fps</option>
            <option value="10">10s at 25 fps</option>
            <option value="20">20s at 25 fps</option>
            <option value="30" selected>30s at 25 fps</option>
          </select>
        </label>
        <button id="run">Generate Video</button>
      </section>
      <section class="status">
        <div class="row">
          <span class="badge" id="state">Loading</span>
          <a id="outputLink" target="_blank" hidden>Open output video</a>
        </div>
        <video id="video" controls hidden></video>
        <pre id="log">Loading...</pre>
      </section>
    </main>
  </div>
  <script>
    const defaultPrompt = [
      "Use the starting corridor image as the exact visual reference and first shot identity.",
      "Create a slow cinematic push-in forward down the abandoned concrete corridor toward the dark end, with gentle parallax and dimensional depth.",
      "Preserve the original composition, cracked concrete walls, right-side windows, damp floor, scattered debris, soft window light, gray-green gritty atmosphere, and dark vanishing point.",
      "Smooth continuous motion, high fidelity, realistic architectural texture, no cuts, no shake, no morphing."
    ].join(" ");
    const $ = (id) => document.getElementById(id);
    $("prompt").value = defaultPrompt;

    async function jsonFetch(url, options) {
      const response = await fetch(url, options);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || response.statusText);
      return data;
    }

    function renderStatus(data) {
      const job = data.job || {};
      const selected = $("image").value || data.default_image;
      $("image").innerHTML = "";
      for (const name of data.images || []) {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        if (name === selected || (!selected && name === data.default_image)) option.selected = true;
        $("image").appendChild(option);
      }
      $("state").textContent = job.running ? "Rendering" : (job.error ? "Error" : "Ready");
      $("run").disabled = !!job.running;
      const lines = [];
      if (job.started) lines.push(`Started: ${job.started}`);
      if (job.completed) lines.push(`Completed: ${job.completed}`);
      if (job.output) lines.push(`Output: ${job.output}`);
      if (job.error) lines.push(`Error: ${job.error}`);
      lines.push("");
      lines.push(...(job.logs || []));
      $("log").textContent = lines.join("\\n") || "Ready.";
      if (job.output_url) {
        $("outputLink").hidden = false;
        $("outputLink").href = job.output_url;
        $("video").hidden = false;
        if (!$("video").src.endsWith(job.output_url)) $("video").src = job.output_url;
      }
    }

    async function refresh() {
      renderStatus(await jsonFetch("/kosz-ltx23-30s/status"));
    }

    $("refresh").onclick = refresh;
    $("upload").onclick = async () => {
      const file = $("file").files[0];
      if (!file) return alert("Choose an image first.");
      const body = new FormData();
      body.append("image", file);
      const result = await jsonFetch("/ltx23-30s-i2v/upload", { method: "POST", body });
      await refresh();
      $("image").value = result.filename;
    };
    $("run").onclick = async () => {
      $("run").disabled = true;
      $("log").textContent = "Starting render...";
      await jsonFetch("/kosz-ltx23-30s/run", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ image: $("image").value, prompt: $("prompt").value, duration: $("duration").value, fps: 25 })
      });
      await refresh();
    };
    refresh();
    setInterval(refresh, 5000);
  </script>
</body>
</html>"""


def _ffmpeg_command():
    found = shutil.which("ffmpeg")
    if found:
        return [found]
    fallback = Path(r"C:\Users\zoltan.ernyei\.local\bin\ffmpeg.cmd")
    if fallback.exists():
        return ["cmd.exe", "/c", str(fallback)]
    return ["ffmpeg"]


def _run_ffmpeg(args):
    command = _ffmpeg_command() + args
    result = subprocess.run(
        command,
        cwd=str(COMFY_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout[-4000:])


def _http_json(method, url, payload=None, timeout=30):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def _duration_mode(value):
    try:
        parsed = int(value)
    except Exception:
        parsed = 30
    if parsed <= 5:
        return 5
    if parsed <= 10:
        return 10
    if parsed <= 20:
        return 20
    return 30


def _segment_plan(duration):
    if duration <= 5:
        return [(129, False)]
    if duration <= 10:
        return [(257, False)]
    if duration <= 20:
        return [(257, False), (257, False)]
    return [(257, False), (257, False), (129, True), (129, True)]


def _build_prompt(segment, source_image, prefix, frames, seed, refine_seed, skip_refine, prompt_text, fps):
    final_width = 1280
    final_height = 704
    low_width = final_width // 2
    low_height = final_height // 2
    positive = prompt_text if segment == 1 else CONTINUATION_PROMPT

    prompt = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}},
        "2": {
            "class_type": "LTXAVTextEncoderLoader",
            "inputs": {
                "text_encoder": "gemma_3_12B_it_fp4_mixed.safetensors",
                "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors",
                "device": "default",
            },
        },
        "3": {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": ["1", 0], "lora_name": "ltx-2.3-22b-distilled-lora-384.safetensors", "strength_model": 0.5},
        },
        "4": {"class_type": "LoadImage", "inputs": {"image": source_image}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["2", 0]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE_PROMPT, "clip": ["2", 0]}},
        "7": {"class_type": "LTXVConditioning", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "frame_rate": fps}},
        "8": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": low_width, "height": low_height, "length": frames, "batch_size": 1}},
        "9": {
            "class_type": "LTXVAddGuide",
            "inputs": {"positive": ["7", 0], "negative": ["7", 1], "vae": ["1", 2], "latent": ["8", 0], "image": ["4", 0], "frame_idx": 0, "strength": 1.0},
        },
        "10": {"class_type": "LTXVAudioVAELoader", "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"}},
        "11": {"class_type": "LTXVEmptyLatentAudio", "inputs": {"frames_number": frames, "frame_rate": fps, "batch_size": 1, "audio_vae": ["10", 0]}},
        "12": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["9", 2], "audio_latent": ["11", 0]}},
        "13": {"class_type": "ModelSamplingLTXV", "inputs": {"model": ["3", 0], "max_shift": 2.05, "base_shift": 0.95, "latent": ["12", 0]}},
        "14": {"class_type": "CFGGuider", "inputs": {"model": ["13", 0], "positive": ["9", 0], "negative": ["9", 1], "cfg": 1.0}},
        "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral_cfg_pp"}},
        "17": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"}},
        "18": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["15", 0], "guider": ["14", 0], "sampler": ["16", 0], "sigmas": ["17", 0], "latent_image": ["12", 0]}},
        "19": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["18", 0]}},
        "20": {"class_type": "LTXVCropGuides", "inputs": {"positive": ["9", 0], "negative": ["9", 1], "latent": ["19", 0]}},
        "21": {"class_type": "LatentUpscaleModelLoader", "inputs": {"model_name": "ltx-2.3-spatial-upscaler-x2-1.1.safetensors"}},
        "22": {"class_type": "LTXVLatentUpsampler", "inputs": {"samples": ["20", 2], "upscale_model": ["21", 0], "vae": ["1", 2]}},
        "23": {
            "class_type": "LTXVAddGuide",
            "inputs": {"positive": ["20", 0], "negative": ["20", 1], "vae": ["1", 2], "latent": ["22", 0], "image": ["4", 0], "frame_idx": 0, "strength": 1.0},
        },
        "24": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["23", 2], "audio_latent": ["19", 1]}},
        "25": {"class_type": "ModelSamplingLTXV", "inputs": {"model": ["3", 0], "max_shift": 2.05, "base_shift": 0.95, "latent": ["24", 0]}},
        "26": {"class_type": "CFGGuider", "inputs": {"model": ["25", 0], "positive": ["23", 0], "negative": ["23", 1], "cfg": 1.0}},
        "27": {"class_type": "RandomNoise", "inputs": {"noise_seed": refine_seed}},
        "28": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_cfg_pp"}},
        "29": {"class_type": "ManualSigmas", "inputs": {"sigmas": "0.85, 0.7250, 0.4219, 0.0"}},
        "30": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["27", 0], "guider": ["26", 0], "sampler": ["28", 0], "sigmas": ["29", 0], "latent_image": ["24", 0]}},
        "31": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["30", 0]}},
        "32": {"class_type": "LTXVCropGuides", "inputs": {"positive": ["23", 0], "negative": ["23", 1], "latent": ["31", 0]}},
        "33": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["22", 0] if skip_refine else ["32", 2], "vae": ["1", 2], "tile_size": 512, "overlap": 64, "temporal_size": 16, "temporal_overlap": 4}},
        "34": {"class_type": "CreateVideo", "inputs": {"images": ["33", 0], "fps": fps}},
        "35": {"class_type": "SaveVideo", "inputs": {"video": ["34", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}},
    }
    return prompt


def _queue_segment(base_url, segment, source_image, prefix, frames, seed, refine_seed, skip_refine, prompt_text, fps):
    client_id = str(uuid.uuid4())
    prompt = _build_prompt(segment, source_image, prefix, frames, seed, refine_seed, skip_refine, prompt_text, fps)
    queued = _http_json("POST", f"{base_url}/prompt", {"prompt": prompt, "client_id": client_id})
    prompt_id = queued["prompt_id"]
    _log(f"Queued segment {segment}: {frames} frames from {source_image}")

    last_progress = time.monotonic()
    while True:
        time.sleep(5)
        history = _http_json("GET", f"{base_url}/history/{prompt_id}", timeout=15)
        if prompt_id in history:
            item = history[prompt_id]
            status = item.get("status", {})
            if status.get("status_str") == "success":
                outputs = item.get("outputs", {}).get("35", {}).get("images", [])
                if not outputs:
                    raise RuntimeError(f"Segment {segment} completed without SaveVideo output")
                output = outputs[0]
                path = OUTPUT_VIDEO_DIR / output["filename"]
                _log(f"Finished segment {segment}: {output['filename']}")
                return path
            raise RuntimeError(f"Segment {segment} failed: {json.dumps(status)[-2000:]}")
        if time.monotonic() - last_progress > 30:
            _log(f"Segment {segment} still rendering...")
            last_progress = time.monotonic()


def _extract_last_frame(video_path, image_name):
    output_path = INPUT_DIR / image_name
    _run_ffmpeg(["-y", "-sseof", "-0.04", "-i", str(video_path), "-frames:v", "1", str(output_path)])
    _log(f"Extracted handoff frame: {image_name}")
    return image_name


def _concat_trim(paths, duration, fps):
    OUTPUT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    final_path = OUTPUT_VIDEO_DIR / f"kosz_ltx23_app_{duration}s_{timestamp}.mp4"
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
        concat_path = Path(handle.name)
        for path in paths:
            handle.write(f"file '{path.as_posix()}'\n")
    try:
        _run_ffmpeg([
            "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-t", str(duration), "-r", str(fps),
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(final_path),
        ])
    finally:
        try:
            concat_path.unlink()
        except OSError:
            pass
    _log(f"Final {duration}s file: {final_path.name}")
    return final_path


def _run_job(base_url, image_name, prompt_text, duration, fps):
    try:
        _set_job(running=True, started=time.strftime("%Y-%m-%d %H:%M:%S"), completed=None, error=None, output=None, output_url=None, logs=[])
        _log(f"Starting LTX2.3 {duration}s I2V chain at {fps} fps")
        segments = []
        source_image = image_name
        plan = _segment_plan(duration)
        for index, (frames, skip_refine) in enumerate(plan, start=1):
            prefix = f"video/kosz_ltx23_app_{duration}s_seg{index:02d}"
            segment_path = _queue_segment(
                base_url,
                index,
                source_image,
                prefix,
                frames,
                6043100 + index,
                430100 + index,
                skip_refine,
                prompt_text,
                fps,
            )
            segments.append(segment_path)
            if index < len(plan):
                source_image = _extract_last_frame(
                    segment_path,
                    f"kosz_ltx23_app_{duration}s_seg{index:02d}_last.png",
                )
        final_path = _concat_trim(segments, duration, fps)
        final_url = f"/view?filename={final_path.name}&subfolder=video&type=output"
        _set_job(running=False, completed=time.strftime("%Y-%m-%d %H:%M:%S"), output=str(final_path), output_url=final_url)
    except Exception as exc:
        _log(f"ERROR: {exc}")
        _set_job(running=False, completed=time.strftime("%Y-%m-%d %H:%M:%S"), error=str(exc))


if PromptServer is not None:
    @PromptServer.instance.routes.get("/ltx23-30s-i2v")
    async def ltx23_app(request):
        return web.Response(text=APP_HTML, content_type="text/html")

    @PromptServer.instance.routes.post("/ltx23-30s-i2v/upload")
    async def ltx23_upload(request):
        reader = await request.multipart()
        field = await reader.next()
        if field is None or field.name != "image":
            return web.json_response({"error": "No image file was uploaded"}, status=400)
        filename = _safe_upload_name(field.filename)
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = INPUT_DIR / filename
        with output_path.open("wb") as handle:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                handle.write(chunk)
        return web.json_response({"filename": filename})

    @PromptServer.instance.routes.get("/kosz-ltx23-30s/status")
    async def kosz_status(request):
        return web.json_response({"job": _job_snapshot(), "images": _input_images(), "default_image": DEFAULT_IMAGE})

    @PromptServer.instance.routes.post("/kosz-ltx23-30s/run")
    async def kosz_run(request):
        with JOB_LOCK:
            if JOB["running"]:
                return web.json_response({"error": "An LTX2.3 job is already running"}, status=409)
        try:
            data = await request.json()
        except Exception:
            data = {}
        image_name = data.get("image") or DEFAULT_IMAGE
        prompt_text = data.get("prompt") or DEFAULT_PROMPT
        duration = _duration_mode(data.get("duration"))
        try:
            fps = int(data.get("fps", 25))
        except Exception:
            fps = 25
        fps = max(8, min(30, fps))
        if image_name not in _input_images():
            return web.json_response({"error": f"Input image not found in Comfy input folder: {image_name}"}, status=400)
        sockname = request.transport.get_extra_info("sockname")
        port = sockname[1] if sockname else 8188
        base_url = f"http://127.0.0.1:{port}"
        thread = threading.Thread(target=_run_job, args=(base_url, image_name, prompt_text, duration, fps), daemon=True)
        thread.start()
        return web.json_response({"started": True})


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
