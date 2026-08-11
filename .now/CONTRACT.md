# CONTRACT — aions-mcp-lan
Mode: FULL

## Goal
Claude Code CLI on the Ubuntu laptop reaches the AIONS-Context MCP server running on
DESKTOP-UDI6M9F over the local network, with the same 69 tools it has locally.

## Done means
- [x] `python scripts/smoke_http_mcp.py http://<lan-ip>:8787/mcp` exits 0 with 69 tools
- [ ] `claude mcp list` on Ubuntu shows aions as connected  (needs the Ubuntu box)
- [x] inbound firewall rule for TCP 8787 exists — "AIONS MCP HTTP 8787", Private, Enabled

## Constraints
Root: E:\server wiedzy (existing repo, extended not forked)
Ports: 8787 (was free) · Host: 0.0.0.0 · Path: /mcp
Touches: mcpServers/VS_CODE_MCP_CODEX/src/__main__.py (additive branch only — stdio path untouched)

## Out of scope
- Auth / TLS — single owner, private LAN, explicitly waived by Marcin
- Internet exposure (cloudflared, tailscale) — LAN-only by decision
- Porting the Windows-only tools (desktop_*, Everything fast_search) to run Linux-side;
  they execute on the Windows host, which is the intent

## Open questions
- Is 172.20.10.5 a DHCP lease that will move? A reservation or a static IP makes this durable.
