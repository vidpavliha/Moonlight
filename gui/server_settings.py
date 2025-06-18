from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
from ..core.config import load_config, save_config

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.java_label = QLabel(f"Java Path:\n{self.config.get('java_path')}")
        layout.addWidget(self.java_label)

        self.select_java_btn = QPushButton("Select Java Executable")
        self.select_java_btn.clicked.connect(self.select_java)
        layout.addWidget(self.select_java_btn)

        self.setLayout(layout)

    def select_java(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Java Executable", "", "Executable (*.exe)")
        if path:
            self.config["java_path"] = path
            save_config(self.config)
            self.java_label.setText(f"Java Path:\n{path}")
            QMessageBox.information(self, "Java Path Set", f"Java path saved:\n{path}")
