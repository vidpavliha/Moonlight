from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QListWidget, QMessageBox
from PyQt5.QtGui import QIcon
from core.server_manager import ServerManager
import os

icon_path = os.path.abspath("assets/icons/favicon.ico")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moonlight Server Manager")
        self.setGeometry(200, 200, 600, 400)
        self.setWindowIcon(QIcon(icon_path))
        self.manager = ServerManager()
        self.init_ui()

    def init_ui(self):
        self.list_widget = QListWidget()
        self.refresh_servers()

        self.create_button = QPushButton("Create Server")
        self.create_button.clicked.connect(self.create_server)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.create_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def refresh_servers(self):
        self.list_widget.clear()
        for server in self.manager.list_servers():
            self.list_widget.addItem(server)

    def create_server(self):
        self.manager.create_server(f"Server_{len(self.manager.list_servers())+1}")
        self.refresh_servers()
        QMessageBox.information(self, "Success", "New server created!")
