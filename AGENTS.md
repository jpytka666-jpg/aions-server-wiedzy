# AGENTS.md — AIONS Cognitive Platform

## Architectural principle

> **Linux is the hardware layer. CBMS is the cognitive system. MCP is the execution layer. LLM is a replaceable communication interface.**

Roadmap: [`.claude/specs/AIONS_OS_ROADMAP.md`](.claude/specs/AIONS_OS_ROADMAP.md) (v16, Fazy 1–10 + Operator Senses)

## Canonical paths

| What | Path |
|------|------|
| Repo (canonical, edit here) | `E:\server wiedzy` |
| Prod Chroma | `E:\server wiedzy\data\chroma` |
| Prod MCP | `E:\server wiedzy\venv` + `start_aions_mcp.bat` |
| CBMS / AIONS_PATH | `E:\server wiedzy\aions_core` |
| Dev mirror (WSL) | `D:\AIONS_DEV\repo\server-wiedzy` |
| Dev venv | `D:\AIONS_DEV\venv` |
| Dev logs | `D:\AIONS_DEV\logs\` |

## Do not change without explicit approval

- `C:\Users\User\.cursor\mcp.json` entry **`aions-context`** (prod MCP)
- Prod Chroma on `E:\server wiedzy\data\chroma`
- `scripts/aions-ctl` core behavior (extend via subcommands, don't break WSL prod)

## Dev workflow

1. Edit on **E:** (canonical)
2. `scripts\sync_dev_mirror.ps1` → D:
3. WSL user **`aions`**: `D:\AIONS_DEV\start_aions_dev.bat status` or `aions-ctl up`
4. Dev MCP: `aions-dev` in `mcp.json` → Reload MCP after changes

## Active phase

**Operator Senses** (Fala 5) — read-only integracje Gmail/kalendarz/Outlook. Kod w `runtime/integrations/` (Google OAuth REAL); **nie live E2E** bez credentials w `runtime/secrets/`; Outlook = stub. Faza 2 Deploy Anywhere zamknięta 2/3 (VPS SKIPPED 2026-07). Platform matrix: [`runtime/docs/PLATFORM_MATRIX.md`](runtime/docs/PLATFORM_MATRIX.md). CBMS dla człowieka: [`docs/CBMS_HUMAN_GUIDE.md`](docs/CBMS_HUMAN_GUIDE.md)

## Cursor rules (repo)

| Rule | Scope |
|------|-------|
| `.cursor/rules/aions-architecture.mdc` | Always — 4 layers, MCP ≠ brain |
| `.cursor/rules/aions-runtime.mdc` | Always — Python, venv, prod vs dev, MCP health gate, automation limits |
| `.cursor/rules/aions-deploy.mdc` | VM install, TMPDIR, LF scripts |
| `.cursor/rules/aions-control-plane.mdc` | `control_plane/`, API extensions |
| `.cursor/rules/aions-platform-matrix.mdc` | New deploy targets |

## MCP health gate

Before **`desktop_*`**, **`browser_*`**, or any long desktop/VM automation:

1. Call **`system_health()`** on **`user-aions-context`** (prod); confirm **`aions-dev`** is connected if used.
2. `system_health()` must return fast (default deadline ≤15s). If it returns `{"status":"error","error":"timeout"}`, fails, returns `status != ok`, or Cursor reports an MCP transport error: **STOP** automation immediately.
   - Tell the user: **Reload MCP in Cursor Settings** (`aions-context` / `aions-dev` → Reload).
   - Note the incident (`conv_log` tag `MCP_RELOAD` or `memory_store` to `claude_marcin_main`) so repeat failures are visible.
3. **Do NOT** retry-loop `desktop_click` / `desktop_*` / `browser_*` when MCP returns transport or tool errors — that burns turns and leaves the desktop in a bad state.
4. After the user reports MCP was reloaded: call **`session_bootstrap()`** once, then re-run **`system_health()`** before resuming automation.

Optional local pre-check (venv/Chroma only, not MCP transport): `scripts\check_aions_mcp_health.ps1`

## Automation limits

SSOT table: [`scripts/aions_automation_limits.md`](scripts/aions_automation_limits.md). Aligns with [`.claude/steering/tech.md`](.claude/steering/tech.md) § Agent Timeout Discipline.

- **Max attempts per action type** — e.g. `desktop_click` / same-coords loop: **3**; desktop snapshot loop: **5**; per-action desktop/browser retries: **3–5**, never 15–20.
- **Time budgets** — desktop automation session: **2–3 min** total; shell status check: **30s**; builds: **120s**; subnet /24 scan: **forbidden** unless user explicitly asks.
- **Between retries** — report state (last error, snapshot, coords); do **not** blind-retry the same failing action.
- **User interrupt** — on **"timeout"**, **"zawiesiles sie"**, or **"wisisz"**: **STOP** current path, report state, propose **one** smallest next step only.
- **MCP tool calls** — expect response within **30s**; retry **once** (2 attempts max), then stop and report.

## Timeouts and anti-hang

- Shell status: 30s; builds: 120s; long scans: background only (`block_until_ms: 0`)
- VM IP wait: max 15 min; pip install: max 45 min; kill stale processes without log output >20 min
- Full limits table: [`scripts/aions_automation_limits.md`](scripts/aions_automation_limits.md)
- See [`.claude/steering/tech.md`](.claude/steering/tech.md) § Agent Timeout Discipline

## Tech standards

Full standards: [`.claude/steering/tech.md`](.claude/steering/tech.md)  
Legacy map: [`.claude/specs/LEGACY_ETAP_MAP.md`](.claude/specs/LEGACY_ETAP_MAP.md)

## Tool routing

MCP tool cheat sheet (Everything, `wsl_run`, `network_ping`, when **not** to use vmconnect/browser): [`.cursor/rules/aions-mcp-tools.mdc`](.cursor/rules/aions-mcp-tools.mdc)
