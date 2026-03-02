import ctypes
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from styles import OVERLAY_STYLE

# Windows DWM Constants
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWM_SBT_ACRYLICBACKDROP = 3

class OverlayWindow(QDialog):
    unlocked = Signal()

    def __init__(self, config_manager, is_primary=True, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.is_primary = is_primary
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("OverlayScreen")
        self.setStyleSheet(OVERLAY_STYLE)
        
        self.setup_ui()
        self.apply_blur_effect()
        
        # Fade animation
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(500)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        if self.is_primary:
            container = QWidget()
            container.setFixedSize(500, 450)
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(15)
            container_layout.setAlignment(Qt.AlignCenter)

            title = QLabel("ACCESS RESTRICTED")
            title.setObjectName("OverlayTitle")
            title.setAlignment(Qt.AlignCenter)

            self.status = QLabel("This device is managed by Overlay App Locker.")
            self.status.setObjectName("OverlayStatus")
            self.status.setAlignment(Qt.AlignCenter)

            self.pin_input = QLineEdit()
            self.pin_input.setObjectName("PinInput")
            self.pin_input.setPlaceholderText("••••")
            self.pin_input.setEchoMode(QLineEdit.Password)
            self.pin_input.setMaxLength(4)
            self.pin_input.setAlignment(Qt.AlignCenter)
            self.pin_input.setFocus()
            self.pin_input.returnPressed.connect(self.check_pin)

            unlock_btn = QPushButton("UNRESTRICT ACCESS")
            unlock_btn.setMinimumHeight(60)
            unlock_btn.setCursor(Qt.PointingHandCursor)
            unlock_btn.clicked.connect(self.check_pin)

            container_layout.addWidget(title)
            container_layout.addWidget(self.status)
            container_layout.addWidget(self.pin_input)
            container_layout.addWidget(unlock_btn)
            layout.addWidget(container)
        else:
            # Secondary monitors just show a message or nothing
            label = QLabel("Locked by Overlay App Locker")
            label.setStyleSheet("font-size: 24px; color: rgba(255,255,255,0.3);")
            layout.addWidget(label)

        self.setLayout(layout)

    def apply_blur_effect(self):
        # Apply Windows 11 Acrylic blur
        hwnd = self.winId()
        dark_mode = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode)
        )
        backdrop_type = ctypes.c_int(DWM_SBT_ACRYLICBACKDROP)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(backdrop_type), ctypes.sizeof(backdrop_type)
        )

    def check_pin(self):
        pin = self.pin_input.text()
        if self.config_manager.verify_pin(pin):
            self.unlocked.emit()
            self.accept()
        else:
            self.status.setText("INVALID PIN. TRY AGAIN.")
            self.status.setStyleSheet("color: #ef4444;")
            self.pin_input.clear()
            self.pin_input.setFocus()

    def show_full_screen_on(self, screen):
        self.setWindowOpacity(0.0)
        self.setGeometry(screen.geometry())
        self.show()
        self.fade_anim.start()
        if self.is_primary:
            self.activateWindow()
            self.raise_()
            self.pin_input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            return
        if event.key() == Qt.Key_F4 and event.modifiers() & Qt.AltModifier:
            return
        super().keyPressEvent(event)
