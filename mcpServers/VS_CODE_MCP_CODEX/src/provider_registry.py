"""AIONS provider registry — platform-native search and desktop backends."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Sequence

try:
    from .desktop_provider import (
        BaseDesktopProvider,
        DisabledDesktopProvider,
        LinuxDesktopProvider,
        WindowsDesktopProvider,
    )
    from .filesystem_provider import AionsLinuxIndexProvider
except ImportError:
    from desktop_provider import (
        BaseDesktopProvider,
        DisabledDesktopProvider,
        LinuxDesktopProvider,
        WindowsDesktopProvider,
    )
    from filesystem_provider import AionsLinuxIndexProvider


LINUX_SEARCH_PROVIDER_NAME = AionsLinuxIndexProvider.provider_name
WINDOWS_SEARCH_PROVIDER_NAME = "everything"


def resolve_search_provider_name(
    *,
    platform_name: str,
    everything_available: bool,
    provider_override: str = "",
) -> str:
    """Pick the active filesystem search backend without fd/plocate fallbacks."""
    override = (provider_override or "").strip().lower()
    if override:
        return override
    if everything_available:
        return WINDOWS_SEARCH_PROVIDER_NAME
    if not platform_name.startswith("win"):
        return LINUX_SEARCH_PROVIDER_NAME
    return "unavailable"


def create_linux_search_provider(
    roots: Sequence[Path],
    index_path: Path,
    *,
    auto_refresh_seconds: int = 900,
) -> AionsLinuxIndexProvider:
    """Construct the AIONS-owned Linux/WSL filesystem index provider."""
    return AionsLinuxIndexProvider(
        roots,
        index_path,
        auto_refresh_seconds=auto_refresh_seconds,
    )


def get_desktop_provider(*, desktop_enabled: bool, platform_name: str) -> BaseDesktopProvider:
    """Return the platform desktop provider (Windows primary, Linux native slices)."""
    if not desktop_enabled:
        return DisabledDesktopProvider("Desktop control disabled (DESKTOP_ENABLED=false)")

    if platform_name.startswith("win"):
        try:
            return WindowsDesktopProvider()
        except Exception as exc:
            return DisabledDesktopProvider(f"Windows desktop provider unavailable: {exc}")

    return LinuxDesktopProvider()


def search_provider_status(
    provider_name: str,
    *,
    linux_provider: Optional[AionsLinuxIndexProvider] = None,
    everything_available: bool = False,
) -> Dict[str, Any]:
    """Summarize configured search providers for health checks."""
    payload: Dict[str, Any] = {
        "active": provider_name,
        "everything_available": everything_available,
        "linux_index_available": linux_provider is not None,
    }
    if linux_provider is not None:
        payload["linux_index"] = linux_provider.status()
    return payload


def desktop_provider_capabilities(provider: BaseDesktopProvider) -> Dict[str, Any]:
    """Expose desktop capability map for health checks and docs."""
    capabilities = {
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
    probe = getattr(provider, "capabilities", None)
    if callable(probe):
        reported = probe()
        if isinstance(reported, dict):
            capabilities.update({key: bool(value) for key, value in reported.items()})
    return {
        "provider": getattr(provider, "provider_name", "unknown"),
        "ready": provider.is_ready(),
        "capabilities": capabilities,
    }
