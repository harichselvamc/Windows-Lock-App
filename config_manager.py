import os
import json
import bcrypt
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.app_data_dir = Path(os.getenv("APPDATA")) / "OverlayAppLocker"
        self.config_path = self.app_data_dir / "config.json"
        self.config = {
            "pin_hash": "",
            "protected_process_names": []
        }
        self.ensure_config_exists()
        self.load_config()

    def ensure_config_exists(self):
        if not self.app_data_dir.exists():
            self.app_data_dir.mkdir(parents=True)
        if not self.config_path.exists():
            # Default PIN is 1234
            self.set_pin("1234")
            self.save_config()

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_config()

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def set_pin(self, pin: str):
        salt = bcrypt.gensalt()
        self.config["pin_hash"] = bcrypt.hashpw(pin.encode(), salt).decode()
        self.save_config()

    def verify_pin(self, pin: str) -> bool:
        if not self.config["pin_hash"]:
            return False
        return bcrypt.checkpw(pin.encode(), self.config["pin_hash"].encode())

    def get_protected_apps(self):
        return self.config.get("protected_process_names", [])

    def add_protected_app(self, process_name: str):
        if process_name not in self.config["protected_process_names"]:
            self.config["protected_process_names"].append(process_name)
            self.save_config()

    def remove_protected_app(self, process_name: str):
        if process_name in self.config["protected_process_names"]:
            self.config["protected_process_names"].remove(process_name)
            self.save_config()

    def is_autostart_enabled(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "OverlayAppLocker")
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def set_autostart(self, enabled: bool):
        import winreg
        import sys
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if enabled:
                # Use sys.executable if running as script, or app path if exe
                app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                winreg.SetValueEx(key, "OverlayAppLocker", 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, "OverlayAppLocker")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error setting autostart: {e}")
