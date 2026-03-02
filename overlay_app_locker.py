import sys
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox
)
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor
from PySide6.QtCore import Qt, QSharedMemory

from config_manager import ConfigManager
from process_monitor import ProcessMonitor
from overlay_window import OverlayWindow
from main_window import MainWindow

class OverlayAppLocker:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Single instance protection
        self.shared_memory = QSharedMemory("OverlayAppLocker_Unique_ID")
        if not self.shared_memory.create(1):
            temp_app = QApplication.instance()
            QMessageBox.warning(None, "Already Running", "Overlay App Locker is already running in the system tray.")
            sys.exit(0)

        self.app.setQuitOnLastWindowClosed(False)

        self.config_manager = ConfigManager()
        self.monitor = ProcessMonitor(self.config_manager)
        
        self.overlays = []
        self.dashboard = MainWindow(self.config_manager)
        
        self.setup_tray()
        self.setup_connections()
        
        self.monitor.start()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self.app)
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        from PySide6.QtGui import QPainter, QBrush, QPen
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#1d4ed8")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRect(20, 28, 24, 20)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor("white"), 4))
        painter.drawArc(24, 16, 16, 24, 0 * 16, 180 * 16)
        painter.end()
        
        self.tray.setIcon(QIcon(pixmap))
        
        menu = QMenu()
        show_action = QAction("Dashboard", menu)
        show_action.triggered.connect(self.show_dashboard)
        
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.quit_app)
        
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def setup_connections(self):
        self.monitor.app_detected.connect(self.on_app_detected)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_dashboard()

    def show_dashboard(self):
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def on_app_detected(self, app_name):
        if not self.overlays:
            # Create overlays for all screens
            screens = self.app.screens()
            for i, screen in enumerate(screens):
                # Only the primary/first screen gets the PIN input
                is_primary = (i == 0)
                overlay = OverlayWindow(self.config_manager, is_primary=is_primary)
                overlay.unlocked.connect(self.on_unlocked)
                overlay.show_full_screen_on(screen)
                self.overlays.append(overlay)
        else:
            # Already showing
            for overlay in self.overlays:
                overlay.raise_()

    def on_unlocked(self):
        self.monitor.mark_unlocked()
        for overlay in self.overlays:
            overlay.close()
            overlay.deleteLater()
        self.overlays.clear()

    def quit_app(self):
        self.monitor.stop()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    locker = OverlayAppLocker()
    locker.run()
