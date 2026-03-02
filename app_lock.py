import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget,
    QVBoxLayout, QLabel, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt


PIN_CODE = "1234"   # change this


class PinDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unlock App")
        self.setModal(True)
        self.setFixedSize(320, 160)

        layout = QVBoxLayout()

        title = QLabel("🔒 Enter PIN to open the app")
        title.setAlignment(Qt.AlignCenter)

        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("PIN")
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.returnPressed.connect(self.check_pin)

        self.msg = QLabel("")
        self.msg.setAlignment(Qt.AlignCenter)

        btn = QPushButton("Unlock")
        btn.clicked.connect(self.check_pin)

        layout.addWidget(title)
        layout.addWidget(self.pin_input)
        layout.addWidget(btn)
        layout.addWidget(self.msg)

        self.setLayout(layout)

    def check_pin(self):
        if self.pin_input.text() == PIN_CODE:
            self.accept()
        else:
            self.msg.setText("❌ Wrong PIN")
            self.pin_input.selectAll()
            self.pin_input.setFocus()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Locked App (Unlocked Now)")
        self.resize(600, 400)

        w = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("✅ App is unlocked and running."))
        w.setLayout(layout)
        self.setCentralWidget(w)


def main():
    app = QApplication(sys.argv)

    dlg = PinDialog()
    if dlg.exec() != QDialog.Accepted:
        sys.exit(0)

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()