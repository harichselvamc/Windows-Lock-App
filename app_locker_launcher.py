import os
import sys
import json
import subprocess
from pathlib import Path

import bcrypt
import win32com.client  # pywin32

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QPushButton, QLabel, QMessageBox, QInputDialog,
    QSystemTrayIcon, QMenu, QStyle
)


APP_NAME = "AppLockerLauncher"
DATA_DIR = Path(os.environ.get("APPDATA", ".")) / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "pins.json"

START_MENU_DIRS = [
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / r"Microsoft\Windows\Start Menu\Programs",
    Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs",
]


def load_db():
    if DB_PATH.exists():
        try:
            return json.loads(DB_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_db(db):
    DB_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")


def hash_pin(pin: str) -> str:
    h = bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt())
    return h.decode("utf-8")


def check_pin(pin: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), stored_hash.encode("utf-8"))
    except Exception:
        return False


def find_start_menu_shortcuts():
    shortcuts = []
    for base in START_MENU_DIRS:
        if not base.exists():
            continue
        for p in base.rglob("*.lnk"):
            shortcuts.append((p.stem, str(p)))
    shortcuts.sort(key=lambda x: x[0].lower())
    return shortcuts


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Locker Launcher (PIN-gated)")
        self.resize(1000, 650)

        self.db = load_db()
        self.all_items = find_start_menu_shortcuts()  # (name, lnk_path)

        central = QWidget()
        root = QVBoxLayout(central)

        # Search bar
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search Start Menu apps...")
        self.search.textChanged.connect(self.apply_filter)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_list)

        top.addWidget(self.search)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        # List
        self.listw = QListWidget()
        self.listw.itemSelectionChanged.connect(self.update_status)
        root.addWidget(self.listw)

        # Buttons
        btns = QHBoxLayout()
        self.setpin_btn = QPushButton("Set/Change PIN")
        self.setpin_btn.clicked.connect(self.set_pin)

        self.clearpin_btn = QPushButton("Remove PIN")
        self.clearpin_btn.clicked.connect(self.remove_pin)

        self.launch_btn = QPushButton("Launch (ask PIN if set)")
        self.launch_btn.clicked.connect(self.launch_selected)

        btns.addWidget(self.setpin_btn)
        btns.addWidget(self.clearpin_btn)
        btns.addStretch(1)
        btns.addWidget(self.launch_btn)
        root.addLayout(btns)

        # Status
        self.status = QLabel("Select an app.")
        root.addWidget(self.status)

        self.setCentralWidget(central)
        self.populate_list(self.all_items)

        # System tray
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("App Locker Launcher")

        # FIX: use a standard icon that exists in PySide6
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        self.tray.setIcon(icon)

        menu = QMenu()
        act_show = menu.addAction("Open")
        act_show.triggered.connect(self.show_normal)

        menu.addSeparator()

        act_quit = menu.addAction("Quit")
        act_quit.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_normal()

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        # minimize to tray
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "App Locker Launcher",
            "Still running in the system tray.",
            QSystemTrayIcon.Information,
            2000
        )

    def refresh_list(self):
        self.all_items = find_start_menu_shortcuts()
        self.apply_filter()

    def populate_list(self, items):
        self.listw.clear()
        for name, path in items:
            key = path.lower()
            locked = "🔒 " if key in self.db else "   "
            self.listw.addItem(f"{locked}{name}  —  {path}")

    def apply_filter(self):
        q = self.search.text().strip().lower()
        if not q:
            filtered = self.all_items
        else:
            filtered = [(n, p) for (n, p) in self.all_items if q in n.lower() or q in p.lower()]
        self.populate_list(filtered)
        self.update_status()

    def get_current_filtered(self):
        q = self.search.text().strip().lower()
        if not q:
            return self.all_items
        return [(n, p) for (n, p) in self.all_items if q in n.lower() or q in p.lower()]

    def get_selected(self):
        row = self.listw.currentRow()
        if row < 0:
            return None
        filtered = self.get_current_filtered()
        if row >= len(filtered):
            return None
        return filtered[row]

    def update_status(self):
        sel = self.get_selected()
        if not sel:
            self.status.setText("Select an app.")
            return
        name, path = sel
        if path.lower() in self.db:
            self.status.setText(f"Selected: {name} (PIN is set)")
        else:
            self.status.setText(f"Selected: {name} (no PIN)")

    def set_pin(self):
        sel = self.get_selected()
        if not sel:
            QMessageBox.information(self, "No selection", "Please select an app first.")
            return
        name, path = sel

        pin, ok = QInputDialog.getText(self, "Set PIN", f"Set PIN for:\n{name}", QLineEdit.Password)
        if not ok:
            return
        pin = pin.strip()
        if len(pin) < 4:
            QMessageBox.warning(self, "PIN too short", "Use at least 4 characters.")
            return

        confirm, ok2 = QInputDialog.getText(self, "Confirm PIN", "Re-enter PIN:", QLineEdit.Password)
        if not ok2:
            return
        if confirm.strip() != pin:
            QMessageBox.warning(self, "Mismatch", "PINs do not match.")
            return

        self.db[path.lower()] = hash_pin(pin)
        save_db(self.db)
        self.apply_filter()
        QMessageBox.information(self, "Saved", f"PIN set for:\n{name}")

    def remove_pin(self):
        sel = self.get_selected()
        if not sel:
            QMessageBox.information(self, "No selection", "Please select an app first.")
            return
        name, path = sel
        key = path.lower()

        if key not in self.db:
            QMessageBox.information(self, "No PIN", "This app does not have a PIN set.")
            return

        reply = QMessageBox.question(self, "Remove PIN", f"Remove PIN for:\n{name} ?")
        if reply != QMessageBox.Yes:
            return

        self.db.pop(key, None)
        save_db(self.db)
        self.apply_filter()

    def launch_selected(self):
        sel = self.get_selected()
        if not sel:
            QMessageBox.information(self, "No selection", "Please select an app first.")
            return
        name, path = sel
        key = path.lower()

        if key in self.db:
            pin, ok = QInputDialog.getText(self, "Unlock", f"Enter PIN for:\n{name}", QLineEdit.Password)
            if not ok:
                return
            if not check_pin(pin.strip(), self.db[key]):
                QMessageBox.critical(self, "Denied", "Wrong PIN.")
                return

        # Launch the shortcut
        try:
            subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
        except Exception as e:
            QMessageBox.critical(self, "Launch failed", str(e))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()