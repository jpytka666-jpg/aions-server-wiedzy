# AIONS-Context MCP over LAN

The same server, two wires. `stdio` for clients on this machine, `streamable-http` for
clients on another machine in the network. One FastMCP instance, one tool set (69 tools).

| | stdio | http |
|---|---|---|
| launcher | `start_aions_mcp.bat` | `start_aions_http.bat` |
| used by | Cursor / Claude Desktop on this host | Claude Code CLI on other machines |
| endpoint | pipes | `http://<host-ip>:8787/mcp` |

## Windows side (server)

```bat
start_aions_http.bat
```

Env overrides, all optional:

| var | default | meaning |
|---|---|---|
| `AIONS_HTTP_HOST` | `0.0.0.0` | bind address |
| `AIONS_HTTP_PORT` | `8787` | port |
| `AIONS_HTTP_ALLOWED_HOSTS` | `*` | `*` disables the SDK DNS-rebinding guard; otherwise a comma-separated allow-list of Host header values |

Autostart: scheduled task **AIONS MCP HTTP** runs the batch at logon.
Remove with `Unregister-ScheduledTask -TaskName "AIONS MCP HTTP" -Confirm:$false`.

Firewall (elevated PowerShell, once):

```powershell
New-NetFirewallRule -DisplayName "AIONS MCP HTTP 8787" -Direction Inbound `
  -Action Allow -Protocol TCP -LocalPort 8787 -Profile Private
```

## Ubuntu side (client)

```bash
claude mcp add --transport http aions http://172.20.10.5:8787/mcp \
  --header "X-AIONS-Host: ubuntu-dev" \
  --header "X-AIONS-Surface: code-cli"
claude mcp list          # expect: aions ✓ connected
```

The two headers are not decoration. Provenance is stamped server-side, so without
them every write from this laptop is recorded as coming from the Windows box.
Pick a stable `X-AIONS-Host` per machine and never change it.

Scope flags: add `-s user` to make it available in every project on that machine.

## Verifying

```bash
python scripts/smoke_http_mcp.py http://172.20.10.5:8787/mcp
```

Exit 0 means initialize + tools/list both answered.

## Known traps

- **HTTP 421 Misdirected Request** — the MCP SDK enables DNS-rebinding protection by default
  and rejects any non-localhost `Host` header. Binding `0.0.0.0` alone does not fix it;
  `AIONS_HTTP_ALLOWED_HOSTS` does.
- **IP drift** — `172.20.10.5` is a DHCP lease. If the laptop reconnects and the address moves,
  the client config breaks. Pin it with a DHCP reservation on the router, or re-run `claude mcp add`.
- **Windows-only tools** — `desktop_*`, `wsl_*` and `fast_search` (Everything) execute on the
  Windows host, not on the Ubuntu client. That is usually what you want: remote hands on the
  knowledge machine. It is not a Linux-local file search.
