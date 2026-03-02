MAIN_STYLE = """
QMainWindow {
    background-color: #ffffff;
    color: #0f172a;
}

QWidget#CentralWidget {
    background-color: #ffffff;
}

/* Group Box / Cards */
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 20px;
    padding-top: 25px;
    font-weight: 600;
    color: #64748b;
}

QLabel {
    color: #475569;
    font-size: 14px;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

QLabel#HeaderLabel {
    font-size: 26px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 20px;
}

QLabel#StatusBadge {
    background-color: #f0fdf4;
    color: #166534;
    padding: 6px 14px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 11px;
    border: 1px solid #bbf7d0;
}

QPushButton {
    background-color: #4f46e5;
    color: #ffffff;
    border: none;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #4338ca;
}

QPushButton#SecondaryButton {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #e2e8f0;
}

QPushButton#SecondaryButton:hover {
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
}

QPushButton#DangerButton {
    background-color: #ef4444;
}

QPushButton#DangerButton:hover {
    background-color: #dc2626;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 12px;
    border-radius: 8px;
    color: #0f172a;
    font-size: 14px;
}

QLineEdit:focus {
    border: 2px solid #4f46e5;
}

QListWidget {
    background-color: #fcfcfc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    color: #334155;
    padding: 8px;
}

QListWidget::item {
    padding: 12px;
    margin: 2px 0;
    border-radius: 6px;
    border-bottom: 1px solid #f1f5f9;
}

QListWidget::item:hover {
    background-color: #f1f5f9;
}

QListWidget::item:selected {
    background-color: #f1f5f9;
    color: #4f46e5;
    font-weight: 600;
    border: 1px solid #e0e7ff;
}

QCheckBox {
    color: #475569;
    font-size: 14px;
    spacing: 12px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
}

QCheckBox::indicator:checked {
    background-color: #4f46e5;
    border: 1px solid #4f46e5;
}
"""

OVERLAY_STYLE = """
QDialog#OverlayScreen {
    background-color: rgba(255, 255, 255, 100);
}

QLabel#OverlayTitle {
    font-size: 44px;
    font-weight: 900;
    color: #1e293b;
    letter-spacing: 2px;
}

QLabel#OverlayStatus {
    font-size: 18px;
    color: #64748b;
    margin-top: 10px;
}

QLineEdit#PinInput {
    background-color: rgba(255, 255, 255, 200);
    border: 2px solid #e2e8f0;
    font-size: 32px;
    letter-spacing: 20px;
    border-radius: 16px;
    color: #0f172a;
    padding: 20px;
    margin-top: 30px;
}

QLineEdit#PinInput:focus {
    border: 2px solid #4f46e5;
}
"""
