"""
AIONS Tray Manager
==================
Ikonka w tray do zarządzania AIONS MCP Server i Claude Desktop.

Wymagania: pip install pystray pillow psutil

Autor: Marcin Szul / AIONS Project
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    import psutil
except ImportError:
    print("Instaluję wymagane pakiety...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pystray", "pillow", "psutil", "-q"])
    import pystray
    from PIL import Image, ImageDraw
    import psutil


# =============================================================================
# CONFIG
# =============================================================================

CLAUDE_DESKTOP_PATH = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Claude" / "Claude.exe"
AIONS_SERVER_LOG = Path(os.environ.get("APPDATA", "")) / "Claude" / "logs" / "mcp-server-aions-context.log"


# =============================================================================
# HELPERS
# =============================================================================

def is_claude_running() -> bool:
    """Check if Claude Desktop is running"""
    for proc in psutil.process_iter(['name']):
        try:
            if 'claude' in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def kill_claude():
    """Kill all Claude processes"""
    killed = 0
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if 'claude' in proc.info['name'].lower():
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed

def start_claude():
    """Start Claude Desktop"""
    if CLAUDE_DESKTOP_PATH.exists():
        subprocess.Popen([str(CLAUDE_DESKTOP_PATH)], shell=True)
        return True
    # Try default location
    alt_path = Path("C:/Users") / os.environ.get("USERNAME", "User") / "AppData/Local/Programs/Claude/Claude.exe"
    if alt_path.exists():
        subprocess.Popen([str(alt_path)], shell=True)
        return True
    return False

def restart_claude():
    """Restart Claude Desktop"""
    kill_claude()
    time.sleep(2)
    start_claude()

def open_logs():
    """Open AIONS server log"""
    if AIONS_SERVER_LOG.exists():
        os.startfile(str(AIONS_SERVER_LOG))
    else:
        # Open logs folder
        logs_dir = AIONS_SERVER_LOG.parent
        if logs_dir.exists():
            os.startfile(str(logs_dir))

def open_config():
    """Open Claude Desktop config"""
    config_path = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    if config_path.exists():
        os.startfile(str(config_path))


# =============================================================================
# TRAY ICON
# =============================================================================

def create_icon_image(running: bool) -> Image.Image:
    """Create tray icon - green if running, red if not"""
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle
    color = (0, 200, 0) if running else (200, 0, 0)  # Green or Red
    draw.ellipse([4, 4, size-4, size-4], fill=color)
    
    # "A" for AIONS
    draw.text((size//2 - 12, size//2 - 16), "A", fill=(255, 255, 255))
    
    return img

def get_status_text() -> str:
    """Get current status"""
    if is_claude_running():
        return "✅ Claude Desktop: Running"
    else:
        return "❌ Claude Desktop: Stopped"

class AIONSTray:
    def __init__(self):
        self.icon = None
        self.running = True
        
    def create_menu(self):
        """Create context menu"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: get_status_text(),
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "🔄 Restart Claude Desktop",
                self.on_restart
            ),
            pystray.MenuItem(
                "⏹️ Stop Claude Desktop", 
                self.on_stop
            ),
            pystray.MenuItem(
                "▶️ Start Claude Desktop",
                self.on_start
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "📋 Open Logs",
                self.on_logs
            ),
            pystray.MenuItem(
                "⚙️ Open Config",
                self.on_config
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "❌ Exit Tray Manager",
                self.on_exit
            ),
        )
    
    def on_restart(self, icon, item):
        """Restart Claude"""
        threading.Thread(target=restart_claude, daemon=True).start()
        
    def on_stop(self, icon, item):
        """Stop Claude"""
        kill_claude()
        self.update_icon()
        
    def on_start(self, icon, item):
        """Start Claude"""
        start_claude()
        time.sleep(3)
        self.update_icon()
        
    def on_logs(self, icon, item):
        """Open logs"""
        open_logs()
        
    def on_config(self, icon, item):
        """Open config"""
        open_config()
        
    def on_exit(self, icon, item):
        """Exit tray app"""
        self.running = False
        icon.stop()
        
    def update_icon(self):
        """Update icon based on status"""
        if self.icon:
            self.icon.icon = create_icon_image(is_claude_running())
            
    def status_monitor(self):
        """Background thread to update icon"""
        while self.running:
            self.update_icon()
            time.sleep(5)
            
    def run(self):
        """Run tray application"""
        self.icon = pystray.Icon(
            "AIONS Manager",
            create_icon_image(is_claude_running()),
            "AIONS MCP Manager",
            self.create_menu()
        )
        
        # Start status monitor
        monitor = threading.Thread(target=self.status_monitor, daemon=True)
        monitor.start()
        
        # Run tray icon
        self.icon.run()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("AIONS Tray Manager starting...")
    print("Look for the icon in your system tray!")
    print("")
    print("Right-click the icon to:")
    print("  - Restart/Stop/Start Claude Desktop")
    print("  - Open logs and config")
    print("")
    
    tray = AIONSTray()
    tray.run()
