# Development Notes

## Local Testing with npm link

The developer uses `npm link` so that `npx comfyui-mcp` resolves to the local build at `C:\Users\klutt\code\comfyui-mcp\dist\`.

**DO NOT modify `plugin/.mcp.json`** to point to a local path. It must stay as:
```json
{
  "comfyui": {
    "command": "npx",
    "args": ["-y", "comfyui-mcp"]
  }
}
```
This works for both:
- **Public users**: `npx` downloads from npm
- **Developer**: `npm link` makes `npx` resolve to the local build

After code changes: `npm run build` then `/mcp` reconnect in Claude Code.

## Restarting Local ComfyUI and MCP

For this Windows portable setup, restart ComfyUI with:

```powershell
C:\Users\zoltan.ernyei\dev\Comfy-mcp\comfy-apps-repo\start.ps1 -Restart -Force
```

Confirm readiness with `http://127.0.0.1:8188/system_stats`; HTTP `200` means ComfyUI is back. If MCP calls fail with `Transport closed`, stop stale `node.exe .../Comfy-mcp/dist/index.js` processes, then run `/mcp` in Claude Code and reconnect/restart the `comfyui` server. If reconnect does not respawn it, restart the Codex/Claude app session.

Helper-script logs live under `C:\Users\zoltan.ernyei\Comfy_portable\ComfyUI_windows_portable\logs\`. Manual recovery launches may redirect logs to `C:\tmp\comfyui-stdout.log` and `C:\tmp\comfyui-stderr.log`.

## Plugin File Sync

The plugin runs from cached copies, not the source tree. After changing files in `plugin/`:
- Cache: `~/.claude/plugins/cache/comfyui-mcp/comfy/0.1.0/`
- Marketplace: `~/.claude/plugins/marketplaces/comfyui-mcp/plugin/`

Copy changed files to both locations, then restart Claude Code for hooks or `/mcp` for MCP tools.
