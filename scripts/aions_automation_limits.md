# AIONS automation limits (SSOT)

Canonical time and attempt budgets for agents. See also [`.claude/steering/tech.md`](../.claude/steering/tech.md) § Agent Timeout Discipline.

| Operation | Max time | Max attempts |
|-----------|----------|--------------|
| Desktop automation session (total) | 180s (2–3 min) | — |
| Desktop snapshot loop | 120s | 5 iterations |
| `desktop_click` same coords | 30s | 3 |
| `desktop_*` / `browser_*` per failing action | — | 3–5 (not 15–20) |
| Shell status check | 30s | — |
| Shell build | 120s | — |
| Shell subnet scan (/24 or wider) | forbidden unless user asked | — |
| MCP tool call | 30s expect response | 2 (retry once) |
| `system_health` MCP health gate | ≤15s hard deadline, then structured timeout error | 2 (retry once) |
| VMConnect open | 1 per session unless user asks | 1 |
| Long scan (`full_system_scan`, etc.) | background only (`block_until_ms: 0`) | do not restart unless user asks |

## Retry discipline

- Between retries: **report state** (what failed, last snapshot/output) — no blind retry of the same failing action.
- On MCP transport errors: see MCP health gate in `AGENTS.md` — **stop**, do not loop.
- User says **"timeout"** or **"zawiesiles sie"** / **"wisisz"**: **STOP**, report current state, propose **one** smallest next step.
