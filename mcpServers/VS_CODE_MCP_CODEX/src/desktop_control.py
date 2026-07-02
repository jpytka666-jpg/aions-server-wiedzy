"""
AIONS Desktop Control — Windows automation for MCP.

All pyautogui / pywin32 work runs on a dedicated single-worker thread
(never on the MCP asyncio loop). Imports are lazy inside executor tasks.
"""

from __future__ import annotations

import base64
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional

# Default enabled for Marcin; set DESKTOP_ENABLED=false to disable.
DESKTOP_ENABLED = os.environ.get("DESKTOP_ENABLED", "true").lower() not in (
    "0",
    "false",
    "no",
    "off",
)

SHELL_TIMEOUT_MAX = 30
_desktop_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="aions-desktop"
)
_desktop_init_error: Optional[str] = None
_deps_checked = False
_deps_ok = False

KNOWN_LAUNCH_NAMES = frozenset(
    {
        "notepad",
        "notepad.exe",
        "calc",
        "calc.exe",
        "mspaint",
        "mspaint.exe",
        "explorer",
        "explorer.exe",
        "cmd",
        "cmd.exe",
        "powershell",
        "powershell.exe",
        "wt",
        "wt.exe",
    }
)


def _log(msg: str) -> None:
    print(f"[AIONS-DESKTOP] {msg}", file=sys.stderr, flush=True)


def _check_deps() -> bool:
    """Lazy dependency probe — does not block MCP startup."""
    global _deps_checked, _deps_ok, _desktop_init_error
    if _deps_checked:
        return _deps_ok
    _deps_checked = True
    try:
        import mss  # noqa: F401
        import pyautogui  # noqa: F401
        import win32gui  # noqa: F401
        import win32process  # noqa: F401
        import win32con  # noqa: F401
        import win32api  # noqa: F401

        _deps_ok = True
    except ImportError as exc:
        _deps_ok = False
        _desktop_init_error = f"Missing desktop dependency: {exc}"
        _log(_desktop_init_error)
    return _deps_ok


def desktop_unavailable_msg() -> str:
    if not DESKTOP_ENABLED:
        return "Desktop control disabled (DESKTOP_ENABLED=false)"
    if not _check_deps():
        return f"Desktop unavailable: {_desktop_init_error or 'dependencies missing'}"
    return "Desktop unavailable"


def is_desktop_ready() -> bool:
    return DESKTOP_ENABLED and _check_deps()


def run_desktop(fn: Callable[[], Any], timeout: int = 60) -> Any:
    """Run fn on the dedicated desktop thread."""
    global _desktop_init_error
    if not DESKTOP_ENABLED:
        raise RuntimeError("Desktop control disabled (DESKTOP_ENABLED=false)")
    if not _check_deps():
        raise RuntimeError(_desktop_init_error or "Desktop dependencies missing")

    def _task() -> Any:
        return fn()

    try:
        return _desktop_executor.submit(_task).result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        raise RuntimeError(f"Desktop operation timed out after {timeout}s")
    except Exception as exc:
        _desktop_init_error = str(exc)
        raise


def _configure_pyautogui() -> None:
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05


def _process_name_from_pid(pid: int) -> str:
    import win32api
    import win32con
    import win32process

    try:
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False,
            pid,
        )
        try:
            exe = win32process.GetModuleFileNameEx(handle, 0)
            return os.path.basename(exe)
        finally:
            win32api.CloseHandle(handle)
    except Exception:
        return "unknown"


def _enum_visible_windows() -> List[Dict[str, Any]]:
    import win32gui
    import win32process

    windows: List[Dict[str, Any]] = []

    def callback(hwnd: int, _extra: Any) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title.strip():
            return True
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        windows.append(
            {
                "hwnd": hwnd,
                "title": title,
                "process": _process_name_from_pid(pid),
                "pid": pid,
            }
        )
        return True

    win32gui.EnumWindows(callback, None)
    return windows


def _bring_window_to_front(hwnd: int) -> None:
    import ctypes
    import win32con
    import win32gui
    import win32process

    if not win32gui.IsWindow(hwnd):
        raise ValueError(f"Invalid window handle: {hwnd}")

    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    foreground = win32gui.GetForegroundWindow()
    fg_thread, _ = win32process.GetWindowThreadProcessId(foreground)
    target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)

    if fg_thread and target_thread and fg_thread != target_thread:
        ctypes.windll.user32.AllowSetForegroundWindow(-1)
        attached = False
        try:
            win32process.AttachThreadInput(fg_thread, target_thread, True)
            attached = True
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)
        finally:
            if attached:
                win32process.AttachThreadInput(fg_thread, target_thread, False)
    else:
        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)


def _resolve_launch_target(path_or_name: str) -> str:
    raw = path_or_name.strip().strip('"')
    if not raw:
        raise ValueError("Empty launch target")

    expanded = os.path.expandvars(os.path.expanduser(raw))
    if os.path.isfile(expanded):
        return expanded

    name_lower = os.path.basename(expanded).lower()
    if name_lower in KNOWN_LAUNCH_NAMES:
        found = shutil.which(expanded) or shutil.which(name_lower)
        if found:
            return found

    if os.path.isdir(expanded):
        raise ValueError(f"Path is a directory, not an executable: {expanded}")

    raise ValueError(
        f"Launch target not found or not allowed: {path_or_name!r}. "
        "Provide an existing file path or a known app name (notepad, calc, etc.)."
    )


# ---------------------------------------------------------------------------
# Executor implementations (lazy imports)
# ---------------------------------------------------------------------------


def impl_snapshot(target: str = "screen") -> Dict[str, Any]:
    import mss

    target = (target or "screen").lower()
    with mss.mss() as sct:
        if target in ("active_window", "window", "active"):
            import win32gui

            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                raise RuntimeError("No active window")
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            width = max(1, right - left)
            height = max(1, bottom - top)
            monitor = {"left": left, "top": top, "width": width, "height": height}
            shot = sct.grab(monitor)
            window_title = win32gui.GetWindowText(hwnd)
        else:
            monitor = sct.monitors[0]
            shot = sct.grab(monitor)
            window_title = None
            width = shot.width
            height = shot.height

    png_bytes = mss.tools.to_png(shot.rgb, shot.size)
    result: Dict[str, Any] = {
        "target": target,
        "width": shot.width,
        "height": shot.height,
        "image_base64": base64.b64encode(png_bytes).decode("ascii"),
        "size_bytes": len(png_bytes),
    }
    if window_title is not None:
        result["window_title"] = window_title
    return result


def impl_click(
    x: int,
    y: int,
    button: str = "left",
    double: bool = False,
) -> Dict[str, Any]:
    _configure_pyautogui()
    import pyautogui

    btn = (button or "left").lower()
    if btn not in ("left", "right", "middle"):
        raise ValueError("button must be left, right, or middle")
    clicks = 2 if double else 1
    pyautogui.click(x=int(x), y=int(y), button=btn, clicks=clicks)
    return {"x": x, "y": y, "button": btn, "double": double}


def impl_type(
    text: str,
    clear_first: bool = False,
    x: Optional[int] = None,
    y: Optional[int] = None,
    press_enter: bool = False,
) -> Dict[str, Any]:
    _configure_pyautogui()
    import pyautogui

    if x is not None and y is not None:
        pyautogui.click(int(x), int(y))

    if clear_first:
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")

    if text:
        # ASCII fast path; unicode via clipboard paste (win32)
        if text.isascii():
            pyautogui.typewrite(text, interval=0.02)
        else:
            import win32clipboard

            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
            pyautogui.hotkey("ctrl", "v")

    if press_enter:
        pyautogui.press("enter")

    return {
        "typed_length": len(text),
        "clear_first": clear_first,
        "press_enter": press_enter,
    }


def impl_key(combo: str) -> Dict[str, Any]:
    _configure_pyautogui()
    import pyautogui

    raw = (combo or "").strip().lower()
    if not raw:
        raise ValueError("Empty key combo")

    parts = [p.strip() for p in re.split(r"[+\s]+", raw) if p.strip()]
    if len(parts) > 1:
        pyautogui.hotkey(*parts)
    else:
        pyautogui.press(parts[0])

    return {"combo": combo}


def impl_windows() -> Dict[str, Any]:
    windows = _enum_visible_windows()
    return {"count": len(windows), "windows": windows}


def impl_focus(title: str = "", hwnd: Optional[int] = None) -> Dict[str, Any]:
    target_hwnd: Optional[int] = None
    matched_title = ""

    if hwnd:
        target_hwnd = int(hwnd)
        import win32gui

        matched_title = win32gui.GetWindowText(target_hwnd)
    elif title:
        needle = title.lower()
        for win in _enum_visible_windows():
            if needle in win["title"].lower():
                target_hwnd = win["hwnd"]
                matched_title = win["title"]
                break
        if target_hwnd is None:
            raise ValueError(f"No window matching title substring: {title!r}")
    else:
        raise ValueError("Provide title substring or hwnd")

    _bring_window_to_front(target_hwnd)
    return {"hwnd": target_hwnd, "title": matched_title}


def impl_launch(path_or_name: str, args: str = "") -> Dict[str, Any]:
    exe = _resolve_launch_target(path_or_name)
    cmd = [exe]
    if args.strip():
        cmd.extend(args.split())

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
    )
    return {"launched": exe, "pid": proc.pid, "args": args or None}


def impl_scroll(
    x: int,
    y: int,
    amount: int = 3,
    direction: str = "vertical",
) -> Dict[str, Any]:
    _configure_pyautogui()
    import pyautogui

    pyautogui.moveTo(int(x), int(y))
    clicks = int(amount)
    direction = (direction or "vertical").lower()

    if direction == "horizontal":
        pyautogui.hscroll(clicks)
    else:
        pyautogui.scroll(clicks)

    return {"x": x, "y": y, "amount": clicks, "direction": direction}


def impl_shell(command: str, timeout: int = 30) -> Dict[str, Any]:
    timeout = min(max(int(timeout), 1), SHELL_TIMEOUT_MAX)
    encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )
    return {
        "returncode": result.returncode,
        "stdout": (result.stdout or "")[:8000],
        "stderr": (result.stderr or "")[:2000],
        "timeout": timeout,
    }


def impl_clipboard(action: str, text: str = "") -> Dict[str, Any]:
    """Read or write system clipboard text (win32clipboard)."""
    import win32clipboard

    act = (action or "").strip().lower()
    if act == "get":
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                    raw = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    data = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
                else:
                    data = ""
            finally:
                win32clipboard.CloseClipboard()
            return {"action": "get", "text": data if data is not None else ""}
        except Exception as exc:
            raise RuntimeError(f"Clipboard read failed: {exc}") from exc

    if act == "set":
        payload = text if text is not None else ""
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(payload, win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
            return {"action": "set", "length": len(payload)}
        except Exception as exc:
            raise RuntimeError(f"Clipboard write failed: {exc}") from exc

    raise ValueError("action must be 'get' or 'set'")


def impl_ui_tree(max_depth: int = 4, max_nodes: int = 80) -> Dict[str, Any]:
    """Simplified accessibility tree of the active window (pywinauto)."""
    from pywinauto import Desktop

    desktop = Desktop(backend="uia")
    win = desktop.window(active_only=True)
    if not win.exists(timeout=2):
        raise RuntimeError("No active window for UI tree")

    nodes: List[Dict[str, Any]] = []

    def walk(element: Any, depth: int) -> None:
        if len(nodes) >= max_nodes or depth > max_depth:
            return
        try:
            info = element.element_info
            name = (info.name or "")[:120]
            ctrl = info.control_type or ""
            rect = info.rectangle
            nodes.append(
                {
                    "depth": depth,
                    "name": name,
                    "control_type": ctrl,
                    "automation_id": (info.automation_id or "")[:80],
                    "rectangle": {
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                    },
                }
            )
            for child in element.children():
                if len(nodes) >= max_nodes:
                    break
                walk(child, depth + 1)
        except Exception:
            return

    walk(win, 0)
    return {
        "window_title": win.window_text(),
        "node_count": len(nodes),
        "nodes": nodes,
    }
