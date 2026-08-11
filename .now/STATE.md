# STATE — aions-mcp-lan

## 2026-08-07T18:45 — HTTP transport added and proven over LAN
Done: `src/__main__.py` gained an `http|streamable-http|sse` branch (env-driven host/port,
DNS-rebinding guard opt-out via AIONS_HTTP_ALLOWED_HOSTS). New `start_aions_http.bat`,
`scripts/smoke_http_mcp.py`. Scheduled task "AIONS MCP HTTP" registered at logon.
Proven: `python scripts/smoke_http_mcp.py http://172.20.10.5:8787/mcp` -> exit 0,
initialize OK (serverInfo.name=aions_context_server), tools/list -> 69 tools.
Next: firewall rule needs an elevated shell; then `claude mcp add` on the Ubuntu box.

## Gotcha worth remembering
mcp SDK >= 1.x enables DNS-rebinding protection by default. Binding 0.0.0.0 is not enough —
any Host header that is not localhost gets HTTP 421 Misdirected Request until
`settings.transport_security` is relaxed. That was the whole failure mode here.


## 2026-08-07T19:37 — provenance on memory writes (additive, no migration)
Done: `server.py` gained `provenance()` / `with_provenance()` / `_client_identity()`.
Every write via `memory_store` and `_auto_dump_logs` now carries
agent / host / server_host / surface / run_id / os / era. Session stays SINGLE
(`claude_marcin_main`) — machine is metadata, not a separate memory.
Remote clients declare themselves with `X-AIONS-Host` / `X-AIONS-Surface` headers;
without them a LAN write would be stamped with the server's hostname.
`server_host` always records where the record physically landed.
Launchers set `AIONS_AGENT` + `AIONS_SURFACE` (local-stdio / lan-http).

Proven:
- `scripts/proof_provenance.py http://172.20.10.5:8787/mcp` -> exit 0, all keys present
- filtered search on `claude_marcin_main`: no filter = 5 hits, host=desktop-udi6m9f = 1,
  surface=lan-http = 1, host=ubuntu-dev = 0
- header spoof test -> host=ubuntu-dev, server_host=desktop-udi6m9f, surface=code-cli

Not done on purpose: NO backfill of the ~30 existing sessions. Old records keep
agent="unknown" and no host/era keys. Absence of `host` IS the marker for
"written before the split" — cheaper and safer than rewriting history.
Backups taken first: `server.py.bak_20260807_193134`, `_backups\chroma_20260807_193134`.

## Gotcha
Killing the server by PID triggers the scheduled task's restart, which silently
brings up a process with the OLD env. `Stop-ScheduledTask` first, then kill.
Cost me one confusing `surface: unknown` result.
