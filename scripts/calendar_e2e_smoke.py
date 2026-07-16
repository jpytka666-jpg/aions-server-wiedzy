"""E2E smoke test — Google Calendar with live token.

Prints today/tomorrow events + next 10 upcoming; verifies token refresh.
Never prints token contents, client_secret, or refresh_token.

Run:
  .\\scripts\\aions_python.ps1 scripts\\calendar_e2e_smoke.py
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.integrations import google_oauth  # noqa: E402
from runtime.integrations.calendar import (  # noqa: E402
    format_event_line,
    get_events,
    list_events,
    oauth_config_path,
    token_path,
    verify_token_refresh,
)


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    print("[calendar-e2e] Google Calendar smoke test")

    # Preconditions
    cfg = oauth_config_path()
    tok = token_path()
    if not cfg.is_file():
        print(f"[FAIL] Brak OAuth client: {cfg}")
        return 1
    if not tok.is_file():
        print(f"[FAIL] Brak tokena: {tok}")
        return 1
    print(f"[OK] config: .../secrets/{cfg.name} ({cfg.stat().st_size} B)")
    print(f"[OK] token:  .../secrets/{tok.name} ({tok.stat().st_size} B)")

    try:
        google_oauth.ensure_google_libs()
    except google_oauth.DependencyMissingError as exc:
        print(f"[FAIL] {exc}")
        return 1

    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)
    horizon_end = today + timedelta(days=30)

    # Today / tomorrow
    _section(f"DZIS ({today.isoformat()})")
    try:
        today_events = get_events(today, today, max_results=50)
        if not today_events:
            print("  (brak wydarzen)")
        for ev in today_events:
            print(f"  - {format_event_line(ev)}")
    except Exception as exc:
        print(f"[FAIL] dzis: {exc}")
        return 1

    _section(f"JUTRO ({tomorrow.isoformat()})")
    try:
        tomorrow_events = get_events(tomorrow, tomorrow, max_results=50)
        if not tomorrow_events:
            print("  (brak wydarzen)")
        for ev in tomorrow_events:
            print(f"  - {format_event_line(ev)}")
    except Exception as exc:
        print(f"[FAIL] jutro: {exc}")
        return 1

    # Next 10 upcoming (from now)
    _section("NASTEPNE 10 (od teraz)")
    try:
        upcoming = list_events(max_results=10)
        if not upcoming:
            print("  (brak wydarzen)")
        for ev in upcoming:
            print(f"  - {format_event_line(ev)}")
    except Exception as exc:
        print(f"[FAIL] upcoming: {exc}")
        return 1

    # Range query via get_events (sanity)
    _section(f"ZAKRES get_events ({today} .. {horizon_end})")
    try:
        ranged = get_events(today, horizon_end, max_results=10)
        print(f"  znaleziono: {len(ranged)} (max 10)")
    except Exception as exc:
        print(f"[FAIL] get_events range: {exc}")
        return 1

    # Token refresh
    _section("TOKEN REFRESH")
    try:
        refresh_status = verify_token_refresh(force=True)
        safe = {k: v for k, v in refresh_status.items() if k != "token_file"}
        print(f"  status: {safe}")
        if not refresh_status.get("has_refresh_token"):
            print("[WARN] brak refresh_token — auto-refresh moze nie dzialac pozniej")
        elif refresh_status.get("refreshed"):
            print("[OK] refresh wykonany, token zapisany ponownie")
        else:
            print("[OK] credentials zaladowane")
    except Exception as exc:
        print(f"[FAIL] refresh: {exc}")
        return 1

    print("\n[calendar-e2e] SMOKE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
