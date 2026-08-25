from __future__ import annotations

import base64
import importlib.util
import re
import shlex
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class DesktopProviderError(RuntimeError):
    """Raised when a desktop provider cannot execute an action."""


class BaseDesktopProvider:
    provider_name = "unavailable"

    def is_ready(self) -> bool:
        return False

    def unavailable_message(self) -> str:
        return "Desktop provider unavailable"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "snapshot": False,
            "click": False,
            "type": False,
            "key": False,
            "scroll": False,
            "windows": False,
            "focus": False,
            "launch": False,
            "shell": False,
            "clipboard": False,
            "ui_tree": False,
        }

    def snapshot(self, target: str = "screen") -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def click(self, x: int, y: int, button: str = "left", double: bool = False) -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def type(self, text: str, clear_first: bool = False, x: Optional[int] = None, y: Optional[int] = None, press_enter: bool = False) -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def key(self, combo: str) -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def windows(self) -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def focus(self, title: str = "", hwnd: Optional[int] = None) -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def launch(self, path_or_name: str, args: str = "") -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def scroll(self, x: int, y: int, amount: int = 3, direction: str = "vertical") -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def shell(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def clipboard(self, action: str, text: str = "") -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())

    def ui_tree(self, max_depth: int = 4, max_nodes: int = 80) -> Dict[str, Any]:
        raise DesktopProviderError(self.unavailable_message())


class WindowsDesktopProvider(BaseDesktopProvider):
    provider_name = "windows-desktop"

    def __init__(self) -> None:
        # NOTE: desktop_control.py lives beside this file, inside the `src`
        # package. When this module is imported as `src.desktop_provider`
        # (the normal packaged path — see server.py's package-relative
        # imports), a bare `import desktop_control` is NOT on sys.path and
        # raises ModuleNotFoundError, which get_desktop_provider() in
        # provider_registry.py/desktop_provider.py silently downgrades to a
        # DisabledDesktopProvider("Windows desktop provider unavailable: No
        # module named 'desktop_control'") — masking a real dependency
        # (pywin32/pyautogui/mss) check behind an import-path bug. Mirror the
        # relative-then-absolute fallback pattern already used at the top of
        # server.py and provider_registry.py.
        try:
            from .desktop_control import (
                desktop_unavailable_msg,
                impl_click,
                impl_clipboard,
                impl_focus,
                impl_key,
                impl_launch,
                impl_scroll,
                impl_shell,
                impl_snapshot,
                impl_type,
                impl_ui_tree,
                impl_windows,
                is_desktop_ready,
                run_desktop,
            )
        except ImportError:
            from desktop_control import (
                desktop_unavailable_msg,
                impl_click,
                impl_clipboard,
                impl_focus,
                impl_key,
                impl_launch,
                impl_scroll,
                impl_shell,
                impl_snapshot,
                impl_type,
                impl_ui_tree,
                impl_windows,
                is_desktop_ready,
                run_desktop,
            )

        self._desktop_unavailable_msg = desktop_unavailable_msg
        self._is_desktop_ready = is_desktop_ready
        self._run_desktop = run_desktop
        self._impl_snapshot = impl_snapshot
        self._impl_click = impl_click
        self._impl_type = impl_type
        self._impl_key = impl_key
        self._impl_windows = impl_windows
        self._impl_focus = impl_focus
        self._impl_launch = impl_launch
        self._impl_scroll = impl_scroll
        self._impl_shell = impl_shell
        self._impl_clipboard = impl_clipboard
        self._impl_ui_tree = impl_ui_tree

    def is_ready(self) -> bool:
        return self._is_desktop_ready()

    def unavailable_message(self) -> str:
        return self._desktop_unavailable_msg()

    def capabilities(self) -> Dict[str, bool]:
        return {
            "snapshot": self.is_ready(),
            "click": self.is_ready(),
            "type": self.is_ready(),
            "key": self.is_ready(),
            "scroll": self.is_ready(),
            "windows": self.is_ready(),
            "focus": self.is_ready(),
            "launch": self.is_ready(),
            "shell": self.is_ready(),
            "clipboard": self.is_ready(),
            "ui_tree": self.is_ready(),
        }

    def snapshot(self, target: str = "screen") -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_snapshot(target=target), timeout=30)

    def click(self, x: int, y: int, button: str = "left", double: bool = False) -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_click(x, y, button, double), timeout=15)

    def type(self, text: str, clear_first: bool = False, x: Optional[int] = None, y: Optional[int] = None, press_enter: bool = False) -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_type(text, clear_first, x, y, press_enter), timeout=30)

    def key(self, combo: str) -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_key(combo), timeout=15)

    def windows(self) -> Dict[str, Any]:
        return self._run_desktop(self._impl_windows, timeout=15)

    def focus(self, title: str = "", hwnd: Optional[int] = None) -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_focus(title, hwnd), timeout=15)

    def launch(self, path_or_name: str, args: str = "") -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_launch(path_or_name, args), timeout=20)

    def scroll(self, x: int, y: int, amount: int = 3, direction: str = "vertical") -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_scroll(x, y, amount, direction), timeout=15)

    def shell(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_shell(command, timeout), timeout=35)

    def clipboard(self, action: str, text: str = "") -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_clipboard(action, text), timeout=10)

    def ui_tree(self, max_depth: int = 4, max_nodes: int = 80) -> Dict[str, Any]:
        return self._run_desktop(lambda: self._impl_ui_tree(max_depth, max_nodes), timeout=30)


class _LinuxSystemSlice:
    """Linux-native shell, launch, window inventory, and clipboard."""

    provider_name = "linux-system"

    def is_ready(self) -> bool:
        return True

    def windows(self) -> Dict[str, Any]:
        wmctrl = shutil.which("wmctrl")
        if not wmctrl:
            return {
                "provider": self.provider_name,
                "count": 0,
                "windows": [],
                "warning": "wmctrl not installed; window inventory unavailable",
            }

        result = subprocess.run(
            [wmctrl, "-lp"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            shell=False,
        )
        if result.returncode != 0:
            raise DesktopProviderError(result.stderr.strip() or "wmctrl failed")

        windows: List[Dict[str, Any]] = []
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split(None, 4)
            if len(parts) < 5:
                continue
            window_id, desktop_id, pid, host, title = parts
            windows.append(
                {
                    "hwnd": window_id,
                    "desktop": desktop_id,
                    "pid": int(pid) if pid.isdigit() else None,
                    "host": host,
                    "title": title,
                    "process": None,
                }
            )

        return {"provider": self.provider_name, "count": len(windows), "windows": windows}

    def launch(self, path_or_name: str, args: str = "") -> Dict[str, Any]:
        target = (path_or_name or "").strip()
        if not target:
            raise DesktopProviderError("Empty launch target")
        executable = shutil.which(target) or target
        cmd = [executable, *shlex.split(args or "")]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        return {"provider": self.provider_name, "launched": executable, "pid": proc.pid, "args": args or None}

    def shell(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        result = subprocess.run(
            ["/usr/bin/env", "bash", "-lc", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(1, min(int(timeout), 30)),
            shell=False,
        )
        return {
            "provider": self.provider_name,
            "returncode": result.returncode,
            "stdout": (result.stdout or "")[:8000],
            "stderr": (result.stderr or "")[:2000],
            "timeout": max(1, min(int(timeout), 30)),
        }

    def clipboard(self, action: str, text: str = "") -> Dict[str, Any]:
        action = (action or "").strip().lower()
        copy_bin = shutil.which("wl-copy") or shutil.which("xclip") or shutil.which("xsel")
        paste_bin = shutil.which("wl-paste") or shutil.which("xclip") or shutil.which("xsel")

        if action == "get":
            if not paste_bin:
                raise DesktopProviderError("Clipboard read unavailable: install wl-clipboard, xclip, or xsel")
            cmd = [paste_bin]
            if paste_bin.endswith("xclip"):
                cmd.extend(["-selection", "clipboard", "-o"])
            elif paste_bin.endswith("xsel"):
                cmd.extend(["--clipboard", "--output"])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                shell=False,
            )
            if result.returncode != 0:
                raise DesktopProviderError(result.stderr.strip() or "Clipboard read failed")
            return {"provider": self.provider_name, "action": "get", "text": result.stdout}

        if action == "set":
            if not copy_bin:
                raise DesktopProviderError("Clipboard write unavailable: install wl-clipboard, xclip, or xsel")
            cmd = [copy_bin]
            if copy_bin.endswith("xclip"):
                cmd.extend(["-selection", "clipboard"])
            elif copy_bin.endswith("xsel"):
                cmd.extend(["--clipboard", "--input"])
            result = subprocess.run(
                cmd,
                input=text if text is not None else "",
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                shell=False,
            )
            if result.returncode != 0:
                raise DesktopProviderError(result.stderr.strip() or "Clipboard write failed")
            return {"provider": self.provider_name, "action": "set", "length": len(text or "")}

        raise DesktopProviderError("action must be 'get' or 'set'")


class _LinuxAutomationSlice:
    """Linux-native screenshot (mss) and pointer/keyboard input (xdotool)."""

    provider_name = "linux-desktop"

    def _xdotool(self) -> str:
        path = shutil.which("xdotool")
        if not path:
            raise DesktopProviderError("Pointer/keyboard automation requires xdotool (X11 session)")
        return path

    @staticmethod
    def _mss_available() -> bool:
        return importlib.util.find_spec("mss") is not None

    def is_ready(self) -> bool:
        return self._mss_available()

    def capabilities(self) -> Dict[str, bool]:
        has_xdotool = bool(shutil.which("xdotool"))
        has_mss = self._mss_available()
        has_wmctrl = bool(shutil.which("wmctrl"))
        return {
            "snapshot": has_mss,
            "click": has_xdotool,
            "type": has_xdotool,
            "key": has_xdotool,
            "scroll": has_xdotool,
            "focus": has_xdotool or has_wmctrl,
            "ui_tree": False,
        }

    def _run_xdotool(self, *args: str, timeout: int = 10) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self._xdotool(), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            check=False,
        )

    def _active_window_geometry(self) -> Dict[str, int]:
        result = self._run_xdotool("getactivewindow", "getwindowgeometry", "--shell")
        if result.returncode != 0:
            raise DesktopProviderError(result.stderr.strip() or "Could not read active window geometry")
        values: Dict[str, int] = {}
        for line in result.stdout.splitlines():
            if "=" not in line:
                continue
            key, raw = line.split("=", 1)
            if raw.isdigit():
                values[key.strip()] = int(raw)
        try:
            return {
                "left": values["X"],
                "top": values["Y"],
                "width": max(1, values["WIDTH"]),
                "height": max(1, values["HEIGHT"]),
            }
        except KeyError as exc:
            raise DesktopProviderError("Active window geometry incomplete") from exc

    def snapshot(self, target: str = "screen") -> Dict[str, Any]:
        if not self._mss_available():
            raise DesktopProviderError("Screenshot requires the mss Python package")

        import mss
        import mss.tools

        target = (target or "screen").lower()
        window_title: Optional[str] = None
        with mss.mss() as sct:
            if target in ("active_window", "window", "active"):
                geometry = self._active_window_geometry()
                monitor = {
                    "left": geometry["left"],
                    "top": geometry["top"],
                    "width": geometry["width"],
                    "height": geometry["height"],
                }
                title_result = self._run_xdotool("getactivewindow", "getwindowname")
                if title_result.returncode == 0:
                    window_title = title_result.stdout.strip() or None
                shot = sct.grab(monitor)
            else:
                monitor = sct.monitors[0]
                shot = sct.grab(monitor)

        png_bytes = mss.tools.to_png(shot.rgb, shot.size)
        payload: Dict[str, Any] = {
            "provider": self.provider_name,
            "target": target,
            "width": shot.width,
            "height": shot.height,
            "image_base64": base64.b64encode(png_bytes).decode("ascii"),
            "size_bytes": len(png_bytes),
        }
        if window_title is not None:
            payload["window_title"] = window_title
        return payload

    @staticmethod
    def _button_code(button: str) -> str:
        mapping = {"left": "1", "middle": "2", "right": "3"}
        code = mapping.get((button or "left").lower())
        if not code:
            raise DesktopProviderError("button must be left, right, or middle")
        return code

    def click(self, x: int, y: int, button: str = "left", double: bool = False) -> Dict[str, Any]:
        btn = self._button_code(button)
        repeat = "2" if double else "1"
        result = self._run_xdotool(
            "mousemove",
            "--sync",
            str(int(x)),
            str(int(y)),
            "click",
            "--repeat",
            repeat,
            btn,
        )
        if result.returncode != 0:
            raise DesktopProviderError(result.stderr.strip() or "xdotool click failed")
        return {
            "provider": self.provider_name,
            "x": int(x),
            "y": int(y),
            "button": (button or "left").lower(),
            "double": double,
        }

    def type(self, text: str, clear_first: bool = False, x: Optional[int] = None, y: Optional[int] = None, press_enter: bool = False) -> Dict[str, Any]:
        if x is not None and y is not None:
            self.click(int(x), int(y))

        if clear_first:
            self.key("ctrl+a")
            self.key("BackSpace")

        typed = text or ""
        if typed:
            if typed.isascii():
                result = self._run_xdotool("type", "--delay", "12", "--", typed)
            else:
                # Unicode path: clipboard paste is more reliable than xdotool type.
                _LinuxSystemSlice().clipboard("set", typed)
                result = self._run_xdotool("key", "ctrl+v")
            if result.returncode != 0:
                raise DesktopProviderError(result.stderr.strip() or "xdotool type failed")

        if press_enter:
            self.key("Return")

        return {
            "provider": self.provider_name,
            "typed_length": len(typed),
            "clear_first": clear_first,
            "press_enter": press_enter,
            "x": x,
            "y": y,
        }

    def key(self, combo: str) -> Dict[str, Any]:
        raw = (combo or "").strip()
        if not raw:
            raise DesktopProviderError("Empty key combo")
        parts = re.split(r"\s*\+\s*", raw)
        xdotool_arg = "+".join(part.strip() for part in parts if part.strip())
        result = self._run_xdotool("key", "--clearmodifiers", xdotool_arg)
        if result.returncode != 0:
            raise DesktopProviderError(result.stderr.strip() or "xdotool key failed")
        return {"provider": self.provider_name, "combo": raw}

    def scroll(self, x: int, y: int, amount: int = 3, direction: str = "vertical") -> Dict[str, Any]:
        clicks = max(1, int(amount))
        direction = (direction or "vertical").lower()
        button = "6" if direction == "horizontal" else "4"
        result = self._run_xdotool(
            "mousemove",
            "--sync",
            str(int(x)),
            str(int(y)),
            "click",
            "--repeat",
            str(clicks),
            button,
        )
        if result.returncode != 0:
            raise DesktopProviderError(result.stderr.strip() or "xdotool scroll failed")
        return {
            "provider": self.provider_name,
            "x": int(x),
            "y": int(y),
            "amount": clicks,
            "direction": direction,
        }

    def focus(self, title: str = "", hwnd: Optional[int] = None) -> Dict[str, Any]:
        if hwnd is not None:
            window_id = str(hwnd)
            result = self._run_xdotool("windowactivate", "--sync", window_id)
            if result.returncode != 0:
                raise DesktopProviderError(result.stderr.strip() or "xdotool windowactivate failed")
            return {"provider": self.provider_name, "hwnd": window_id, "title": title or None}

        needle = (title or "").strip()
        if not needle:
            raise DesktopProviderError("Provide title substring or hwnd")

        wmctrl = shutil.which("wmctrl")
        if wmctrl:
            result = subprocess.run(
                [wmctrl, "-a", needle],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                shell=False,
            )
            if result.returncode == 0:
                return {"provider": self.provider_name, "title": needle}

        result = self._run_xdotool("search", "--name", needle, "windowactivate", "--sync")
        if result.returncode != 0:
            raise DesktopProviderError(result.stderr.strip() or f"No window matching title substring: {needle!r}")
        return {"provider": self.provider_name, "title": needle}


class LinuxDesktopProvider(BaseDesktopProvider):
    """Composite Linux provider: system slice + desktop automation slice."""

    provider_name = "linux-desktop"

    def __init__(self) -> None:
        self._system = _LinuxSystemSlice()
        self._automation = _LinuxAutomationSlice()

    def is_ready(self) -> bool:
        return self._system.is_ready()

    def unavailable_message(self) -> str:
        caps = self.capabilities()
        missing = [name for name, enabled in caps.items() if not enabled]
        if not missing:
            return "Linux desktop provider ready"
        return (
            "Linux desktop provider active; missing capabilities: "
            + ", ".join(missing)
        )

    def capabilities(self) -> Dict[str, bool]:
        caps = {
            "windows": bool(shutil.which("wmctrl")),
            "launch": True,
            "shell": True,
            "clipboard": bool(
                shutil.which("wl-copy")
                or shutil.which("wl-paste")
                or shutil.which("xclip")
                or shutil.which("xsel")
            ),
        }
        caps.update(self._automation.capabilities())
        return caps

    def snapshot(self, target: str = "screen") -> Dict[str, Any]:
        return self._automation.snapshot(target=target)

    def click(self, x: int, y: int, button: str = "left", double: bool = False) -> Dict[str, Any]:
        return self._automation.click(x, y, button, double)

    def type(self, text: str, clear_first: bool = False, x: Optional[int] = None, y: Optional[int] = None, press_enter: bool = False) -> Dict[str, Any]:
        return self._automation.type(text, clear_first, x, y, press_enter)

    def key(self, combo: str) -> Dict[str, Any]:
        return self._automation.key(combo)

    def windows(self) -> Dict[str, Any]:
        return self._system.windows()

    def focus(self, title: str = "", hwnd: Optional[int] = None) -> Dict[str, Any]:
        return self._automation.focus(title, hwnd)

    def launch(self, path_or_name: str, args: str = "") -> Dict[str, Any]:
        return self._system.launch(path_or_name, args)

    def scroll(self, x: int, y: int, amount: int = 3, direction: str = "vertical") -> Dict[str, Any]:
        return self._automation.scroll(x, y, amount, direction)

    def shell(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        return self._system.shell(command, timeout)

    def clipboard(self, action: str, text: str = "") -> Dict[str, Any]:
        return self._system.clipboard(action, text)

    def ui_tree(self, max_depth: int = 4, max_nodes: int = 80) -> Dict[str, Any]:
        raise DesktopProviderError("Linux accessibility/ui_tree slice is not implemented yet")


class DisabledDesktopProvider(BaseDesktopProvider):
    provider_name = "disabled"

    def __init__(self, message: str) -> None:
        self._message = message

    def unavailable_message(self) -> str:
        return self._message


def get_desktop_provider(*, desktop_enabled: bool, platform_name: str) -> BaseDesktopProvider:
    if not desktop_enabled:
        return DisabledDesktopProvider("Desktop control disabled (DESKTOP_ENABLED=false)")

    if platform_name.startswith("win"):
        try:
            return WindowsDesktopProvider()
        except Exception as exc:
            return DisabledDesktopProvider(f"Windows desktop provider unavailable: {exc}")

    return LinuxDesktopProvider()
