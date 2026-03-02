import psutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QPushButton, QInputDialog,
    QMessageBox, QDialog, QListWidgetItem, QLineEdit,
    QCheckBox, QGroupBox, QFrame, QFileIconProvider
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QFileInfo, QSize
from styles import MAIN_STYLE
import ctypes

def get_visible_window_pids():
    pids = {}
    
    def enum_windows_proc(hwnd, lParam):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                
                # Only keep the first (likely main) window for each PID
                if pid.value not in pids:
                    pids[pid.value] = buff.value
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
    return pids

class AppSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Application")
        self.resize(600, 750)
        self.setStyleSheet(MAIN_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Search and Toggle Header
        header_layout = QVBoxLayout()
        search_label = QLabel("Search Applications:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find by name or window title...")
        self.search_input.textChanged.connect(self.filter_list)
        
        self.show_all_check = QCheckBox("Show background services and drivers")
        self.show_all_check.setStyleSheet("font-size: 12px; color: #475569;")
        self.show_all_check.stateChanged.connect(lambda: self.update_list())
        
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.show_all_check)
        layout.addLayout(header_layout)
        
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(24, 24))
        
        self.icon_provider = QFileIconProvider()
        
        # Populate with running apps
        self.available_apps = []
        visible_pids = get_visible_window_pids()
        
        for proc in psutil.process_iter(['name', 'exe', 'pid']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                exe_path = proc.info['exe']
                
                # Deduplicate by exe path/name
                title = visible_pids.get(pid, "")
                self.available_apps.append({
                    'name': name,
                    'title': title,
                    'path': exe_path,
                    'is_gui': bool(title),
                    'pid': pid
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        layout.addWidget(self.list_widget)
        
        self.add_btn = QPushButton("Add Protection")
        self.add_btn.setMinimumHeight(50)
        self.add_btn.clicked.connect(self.accept)
        
        hint = QLabel("Tip: Protection applies to the entire application session.")
        hint.setStyleSheet("font-size: 11px; font-style: italic; color: #64748b;")
        layout.addWidget(hint)
        layout.addWidget(self.add_btn)
        
        self.update_list()

    def filter_list(self, text):
        self.update_list()

    def update_list(self):
        search_text = self.search_input.text().lower()
        show_all = self.show_all_check.isChecked()
        
        self.list_widget.clear()
        
        # Filter logic
        filtered = []
        for app in self.available_apps:
            matches_search = search_text in app['name'].lower() or search_text in app['title'].lower()
            if not matches_search:
                continue
                
            if app['is_gui'] or show_all:
                filtered.append(app)
        
        # Sort: GUIs first, then alphabetical by Title/Name
        filtered.sort(key=lambda x: (not x['is_gui'], (x['title'] or x['name']).lower()))
        
        for app in filtered:
            if app['is_gui']:
                display_text = f"{app['title']} ({app['name']})"
            else:
                display_text = f"{app['name']} (Background)"
                
            item = QListWidgetItem(display_text, self.list_widget)
            item.setData(Qt.UserRole, app['name'])
            
            if app['path']:
                icon = self.icon_provider.icon(QFileInfo(app['path']))
                item.setIcon(icon)
            
            if not app['is_gui']:
                item.setForeground(Qt.gray)

    def get_selected_app(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
        self.setWindowTitle("Overlay App Locker - Dashboard")
        self.resize(600, 500)
        self.setStyleSheet(MAIN_STYLE)
        
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Header with Status
        header_layout = QHBoxLayout()
        header = QLabel("Overlay App Locker")
        header.setObjectName("HeaderLabel")
        
        status_badge = QLabel("ENFORCEMENT ACTIVE")
        status_badge.setObjectName("StatusBadge")
        status_badge.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(status_badge)
        layout.addLayout(header_layout)

        # Monitoring Section
        monitor_group = QGroupBox("Protected Applications")
        monitor_layout = QVBoxLayout(monitor_group)
        monitor_layout.setContentsMargins(20, 20, 20, 20)
        monitor_layout.setSpacing(15)

        # List Filter
        self.app_filter = QLineEdit()
        self.app_filter.setPlaceholderText("Filter protected applications...")
        self.app_filter.textChanged.connect(self.refresh_list)
        monitor_layout.addWidget(self.app_filter)

        self.app_list = QListWidget()
        self.app_list.setMinimumHeight(200)
        monitor_layout.addWidget(self.app_list)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add New Application")
        add_btn.setMinimumHeight(45)
        add_btn.clicked.connect(self.show_app_selector)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.setObjectName("DangerButton")
        remove_btn.setMinimumHeight(45)
        remove_btn.clicked.connect(self.remove_app)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        monitor_layout.addLayout(btn_layout)
        layout.addWidget(monitor_group)

        # Settings Section
        settings_group = QGroupBox("General Security Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)

        self.startup_check = QCheckBox("Run on Windows Startup (Recommended)")
        self.startup_check.setChecked(self.config_manager.is_autostart_enabled())
        self.startup_check.stateChanged.connect(self.toggle_startup)
        settings_layout.addWidget(self.startup_check)

        pin_btn = QPushButton("Change Security Unlock PIN")
        pin_btn.setObjectName("SecondaryButton")
        pin_btn.setMinimumHeight(45)
        pin_btn.clicked.connect(self.change_pin)
        settings_layout.addWidget(pin_btn)
        
        layout.addWidget(settings_group)
        layout.addStretch()

        self.setCentralWidget(central)

    def refresh_list(self):
        filter_text = self.app_filter.text().lower()
        self.app_list.clear()
        apps = self.config_manager.get_protected_apps()
        for app in apps:
            if filter_text in app.lower():
                self.app_list.addItem(app)

    def show_app_selector(self):
        dlg = AppSelectorDialog(self)
        if dlg.exec() == QDialog.Accepted:
            app_name = dlg.get_selected_app()
            if app_name:
                self.config_manager.add_protected_app(app_name)
                self.refresh_list()

    def remove_app(self):
        item = self.app_list.currentItem()
        if item:
            self.config_manager.remove_protected_app(item.text())
            self.refresh_list()

    def change_pin(self):
        current_pin, ok = QInputDialog.getText(
            self, "Security", "Enter current PIN:", QLineEdit.Password
        )
        if not ok: return
        
        if self.config_manager.verify_pin(current_pin):
            new_pin, ok = QInputDialog.getText(
                self, "Security", "Enter new 4-digit PIN:", QLineEdit.Password
            )
            if ok and len(new_pin) == 4 and new_pin.isdigit():
                self.config_manager.set_pin(new_pin)
                QMessageBox.information(self, "Success", "PIN updated successfully.")
            else:
                QMessageBox.warning(self, "Error", "Invalid PIN format. Must be 4 digits.")
        else:
            QMessageBox.warning(self, "Error", "Incorrect current PIN.")

    def toggle_startup(self, state):
        enabled = (state == Qt.Checked)
        self.config_manager.set_autostart(enabled)

    def closeEvent(self, event):
        # Don't quit, just hide to tray
        self.hide()
        event.ignore()
