import os
import subprocess
from pathlib import Path

from aiohttp import web

try:
    from server import PromptServer
except Exception:
    PromptServer = None

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

COMFY_DIR = Path(__file__).resolve().parents[2]
PORTABLE_DIR = COMFY_DIR.parent
LOG_PATH = PORTABLE_DIR / "logs" / "comfy-terminal.log"
ERR_LOG_PATH = PORTABLE_DIR / "logs" / "comfy-terminal.err.log"


def _tail_text(path, max_bytes=65536):
    try:
        if not path.exists():
            return ""
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > max_bytes:
                handle.seek(-max_bytes, os.SEEK_END)
            data = handle.read()
        return data.decode("utf-8", errors="replace")
    except Exception as exc:
        return f"Unable to read log: {exc}"


def _running_command():
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'ComfyUI\\\\main.py' -and $_.Name -match 'python' } | Select-Object -First 1 -ExpandProperty CommandLine",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        command = result.stdout.strip()
        if command:
            return command
    except Exception:
        pass
    return "ComfyUI process command is not available."


def _combined_log():
    stdout = _tail_text(LOG_PATH)
    stderr = _tail_text(ERR_LOG_PATH)
    sections = []
    if stdout:
        sections.append("[stdout]\n" + stdout.rstrip())
    if stderr:
        sections.append("[stderr]\n" + stderr.rstrip())
    return "\n\n".join(sections)


if PromptServer is not None:
    @PromptServer.instance.routes.get("/comfy-app-switcher/terminal")
    async def comfy_app_switcher_terminal(request):
        return web.json_response(
            {
                "command": _running_command(),
                "log_path": str(LOG_PATH),
                "stderr_path": str(ERR_LOG_PATH),
                "log": _combined_log(),
            }
        )


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
