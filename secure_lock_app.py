import sys
import ctypes
import bcrypt

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QLineEdit, QDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer


# ===============================
# WINDOWS SYSTEM LOCK
# ===============================

def lock_windows():
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception as e:
        print("Windows lock failed:", e)


# ===============================
# IDLE TIME DETECTION
# ===============================

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint)
    ]


def get_idle_seconds():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0


# ===============================
# SECURITY MANAGER
# ===============================

class SecurityManager:
    def __init__(self):
        # Store pre-generated hash of PIN "1234"
        self.password_hash = bcrypt.hashpw(b"1234", bcrypt.gensalt())
        self.failed_attempts = 0

    def verify(self, pin):
        if bcrypt.checkpw(pin.encode(), self.password_hash):
            self.failed_attempts = 0
            return True
        else:
            self.failed_attempts += 1
            return False


# ===============================
# LOCK SCREEN
# ===============================

class LockScreen(QDialog):
    def __init__(self, security):
        super().__init__()
        self.security = security

        self.setWindowTitle("Unlock Application")
        self.setFixedSize(400, 200)
        self.setWindowModality(Qt.ApplicationModal)

        layout = QVBoxLayout()

        label = QLabel("🔒 Enter PIN to Unlock")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size:18px;")

        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setPlaceholderText("PIN")
        self.pin_input.returnPressed.connect(self.try_unlock)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)

        unlock_btn = QPushButton("Unlock")
        unlock_btn.clicked.connect(self.try_unlock)

        layout.addWidget(label)
        layout.addWidget(self.pin_input)
        layout.addWidget(unlock_btn)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def try_unlock(self):
        if self.security.verify(self.pin_input.text()):
            self.accept()
        else:
            self.info_label.setText(
                f"Wrong PIN ({self.security.failed_attempts})"
            )

            if self.security.failed_attempts >= 3:
                QMessageBox.warning(self, "Locked", "Too many attempts. Locking Windows.")
                lock_windows()


# ===============================
# MAIN WINDOW
# ===============================

class MainWindow(QMainWindow):

    AUTO_LOCK_SECONDS = 30

    def __init__(self):
        super().__init__()

        self.security = SecurityManager()
        self.is_locked = True

        self.setWindowTitle("Secure Lock App")
        self.resize(800, 500)

        # ---------------- UI ----------------
        central = QWidget()
        layout = QVBoxLayout()

        self.status_label = QLabel("Status: Locked")
        self.status_label.setAlignment(Qt.AlignCenter)

        lock_btn = QPushButton("Lock App")
        lock_btn.clicked.connect(self.lock_app)

        winlock_btn = QPushButton("Lock Windows")
        winlock_btn.clicked.connect(lock_windows)

        feature_btn = QPushButton("Sensitive Feature")
        feature_btn.clicked.connect(self.sensitive_feature)

        layout.addWidget(self.status_label)
        layout.addWidget(lock_btn)
        layout.addWidget(winlock_btn)
        layout.addWidget(feature_btn)

        central.setLayout(layout)
        self.setCentralWidget(central)

        # ---------------- Timer ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_idle)
        self.timer.start(2000)

        # Lock at startup
        QTimer.singleShot(100, self.lock_app)

    # ==========================
    # LOCK / UNLOCK
    # ==========================

    def lock_app(self):
        self.is_locked = True
        self.status_label.setText("Status: Locked")

        dlg = LockScreen(self.security)
        if dlg.exec() == QDialog.Accepted:
            self.unlock_app()

    def unlock_app(self):
        self.is_locked = False
        self.status_label.setText("Status: Unlocked")

    # ==========================
    # INACTIVITY AUTO LOCK
    # ==========================

    def check_idle(self):
        if not self.is_locked:
            if get_idle_seconds() > self.AUTO_LOCK_SECONDS:
                self.lock_app()

    # ==========================
    # SENSITIVE FEATURE
    # ==========================

    def sensitive_feature(self):
        if self.is_locked:
            QMessageBox.warning(self, "Locked", "Unlock first!")
            return

        QMessageBox.information(self, "Feature", "Sensitive feature opened.")

    # ==========================
    # BASIC KIOSK PROTECTION
    # ==========================

    def closeEvent(self, event):
        if self.is_locked:
            event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        # block ALT+F4
        if event.key() == Qt.Key_F4 and event.modifiers() & Qt.AltModifier:
            return
        super().keyPressEvent(event)


# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())