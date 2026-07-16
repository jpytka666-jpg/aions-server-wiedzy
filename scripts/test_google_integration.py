"""Smoke test for Gmail + Calendar integrations (no live credentials required).

Proves: modules import, google libs present, scopes are read+write, and the
functions reach config-loading and raise NotConfiguredError when secrets are
absent. Does NOT print any secret values.

Run:  .\scripts\aions_python.ps1 scripts\test_google_integration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.integrations import google_oauth  # noqa: E402
from runtime.integrations.calendar import oauth_skeleton as cal  # noqa: E402
from runtime.integrations.gmail import oauth_skeleton as gm  # noqa: E402


def main() -> int:
    ok = True

    # 1) google libs installed
    try:
        google_oauth.ensure_google_libs()
        print("[OK] google libs importowalne")
    except google_oauth.DependencyMissingError as exc:
        print(f"[FAIL] brak libs: {exc}")
        return 1

    # 2) scopes are read+write
    assert gm.SCOPES == (
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
    ), gm.SCOPES
    assert cal.GOOGLE_SCOPES == ("https://www.googleapis.com/auth/calendar",), cal.GOOGLE_SCOPES
    print(f"[OK] Gmail scopes: {gm.SCOPES}")
    print(f"[OK] Calendar scope: {cal.GOOGLE_SCOPES}")

    # 3) config paths resolve inside runtime/secrets/
    for label, p in [
        ("gmail_oauth", gm.oauth_config_path()),
        ("gmail_token", gm.token_path()),
        ("calendar_oauth", cal.oauth_config_path()),
        ("calendar_token", cal.token_path()),
    ]:
        assert "secrets" in str(p).replace("\\", "/"), p
        print(f"[OK] path {label}: ...{Path(p).parent.name}/{Path(p).name}")

    # 4) without secrets, calls raise NotConfiguredError (wiring reaches config load)
    have_gmail_cfg = gm.oauth_config_path().is_file()
    if have_gmail_cfg:
        print("[INFO] gmail_oauth.json obecny — pomijam test braku configu")
    else:
        try:
            gm.list_messages(max_results=1)
            print("[FAIL] list_messages nie rzucil bledu mimo braku configu")
            ok = False
        except google_oauth.NotConfiguredError:
            print("[OK] gmail.list_messages -> NotConfiguredError (brak configu, zgodnie z oczekiwaniem)")

    # 5) outlook placeholder rejected
    try:
        cal.list_events(provider="outlook")
        print("[FAIL] outlook powinien byc odrzucony")
        ok = False
    except google_oauth.NotConfiguredError:
        print("[OK] calendar outlook -> NotConfiguredError (placeholder)")

    # 6) callable write functions exist
    for fn in (gm.send_message, cal.create_event, cal.delete_event):
        assert callable(fn), fn
    print("[OK] funkcje write (send_message / create_event / delete_event) dostepne")

    print("\nSMOKE TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
