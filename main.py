# moonlight_manager.py
# Full Moonlight Minecraft Server Manager Implementation

import os
import subprocess
import json
import shutil
import psutil
import requests
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QListWidget, QMessageBox, QLabel, QHBoxLayout, QLineEdit, QDialog, QFormLayout, QComboBox
from PyQt5.QtCore import QTimer

# --- Configuration ---
SERVERS_DIR = Path("servers")
TEMPLATES_DIR = Path("assets/templates")
STARTERS_DIR = Path("assets/Server Starters")

# --- Server Manager ---
class ServerManager:
    def __init__(self):
        self.server_path = SERVERS_DIR
        self.processes = {}  # name -> Popen
        os.makedirs(self.server_path, exist_ok=True)

    def list_servers(self):
        return [f for f in os.listdir(self.server_path) if os.path.isdir(self.server_path / f)]

    def list_templates(self):
        return [f.name for f in STARTERS_DIR.glob("*.jar")]

    def create_server(self, name, starter_jar):
        new_path = self.server_path / name
        os.makedirs(new_path, exist_ok=True)
        shutil.copy(STARTERS_DIR / starter_jar, new_path / "server.jar")
        with open(new_path / "server.properties", "w") as f:
            f.write("motd=Welcome to Moonlight Server\nmax-players=20\n")
        with open(new_path / "config.json", "w") as f:
            json.dump({"starter": starter_jar}, f)

    def edit_server(self, old_name, new_name):
        old_path = self.server_path / old_name
        new_path = self.server_path / new_name
        if old_path.exists() and not new_path.exists():
            os.rename(old_path, new_path)
            return True
        return False

    def update_settings(self, name, motd, max_players):
        props_path = self.server_path / name / "server.properties"
        lines = []
        if props_path.exists():
            with open(props_path, "r") as f:
                for line in f:
                    if line.startswith("motd="):
                        lines.append(f"motd={motd}\n")
                    elif line.startswith("max-players="):
                        lines.append(f"max-players={max_players}\n")
                    else:
                        lines.append(line)
        else:
            lines = [f"motd={motd}\n", f"max-players={max_players}\n"]
        with open(props_path, "w") as f:
            f.writelines(lines)

    def start_server(self, name):
        server_dir = self.server_path / name
        jar_path = server_dir / "server.jar"
        if not jar_path.exists():
            raise FileNotFoundError("server.jar not found")
        ram_mb = get_optimal_ram()
        flags = get_optimized_flags(ram_mb)
        cmd = ["java"] + flags + ["-jar", "server.jar", "nogui"]
        proc = subprocess.Popen(cmd, cwd=server_dir)
        self.processes[name] = proc

    def stop_server(self, name):
        proc = self.processes.get(name)
        if proc:
            proc.terminate()
            proc.wait()
            del self.processes[name]

# --- Performance Tuning ---
def get_optimal_ram():
    total = psutil.virtual_memory().total // (1024 * 1024)
    return max(1024, int(total * 0.5))

def get_optimized_flags(ram_mb):
    return [
        f"-Xms{ram_mb}M",
        f"-Xmx{ram_mb}M",
        "-XX:+UseG1GC",
        "-XX:+ParallelRefProcEnabled",
        "-XX:MaxGCPauseMillis=200"
    ]

# --- Backup Manager ---
def backup_server(server_dir):
    if not os.path.exists(server_dir):
        raise FileNotFoundError("Server directory not found")
    backup_dir = f"{server_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(server_dir, backup_dir)
    return backup_dir

# --- Plugin Manager ---
class PluginManager:
    def __init__(self, server_dir):
        self.plugins_dir = Path(server_dir) / "plugins"
        os.makedirs(self.plugins_dir, exist_ok=True)

    def install_plugin(self, plugin_url):
        filename = plugin_url.split("/")[-1]
        response = requests.get(plugin_url)
        with open(self.plugins_dir / filename, "wb") as f:
            f.write(response.content)

    def list_plugins(self):
        return os.listdir(self.plugins_dir)

    def remove_plugin(self, name):
        os.remove(self.plugins_dir / name)

# --- GUI ---
class EditServerDialog(QDialog):
    def __init__(self, current_name):
        super().__init__()
        self.setWindowTitle("Edit Server")
        self.new_name = QLineEdit()
        self.new_name.setText(current_name)
        layout = QFormLayout()
        layout.addRow("New Server Name:", self.new_name)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

class SettingsDialog(QDialog):
    def __init__(self, server_name, manager):
        super().__init__()
        self.setWindowTitle("Server Settings")
        self.name = server_name
        self.manager = manager
        self.motd = QLineEdit()
        self.max_players = QLineEdit("20")
        layout = QFormLayout()
        layout.addRow("MOTD:", self.motd)
        layout.addRow("Max Players:", self.max_players)
        self.ok_button = QPushButton("Save")
        self.ok_button.clicked.connect(self.save)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

    def save(self):
        self.manager.update_settings(self.name, self.motd.text(), self.max_players.text())
        self.accept()

class CreateServerDialog(QDialog):
    def __init__(self, manager):
        super().__init__()
        self.setWindowTitle("Create Server")
        self.name_input = QLineEdit("MyServer")
        self.template_box = QComboBox()
        for t in manager.list_templates():
            self.template_box.addItem(t)
        layout = QFormLayout()
        layout.addRow("Server Name:", self.name_input)
        layout.addRow("Starter Jar:", self.template_box)
        self.ok_button = QPushButton("Create")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Moonlight Server Manager")
        self.setGeometry(200, 200, 800, 500)

        self.manager = ServerManager()
        self.init_ui()
        self.start_monitor_timer()

    def init_ui(self):
        self.list_widget = QListWidget()
        self.status_label = QLabel("System Monitor")

        self.refresh_servers()

        self.create_button = QPushButton("Create Server")
        self.edit_button = QPushButton("Edit Selected")
        self.settings_button = QPushButton("Settings")
        self.start_button = QPushButton("Start Selected")
        self.stop_button = QPushButton("Stop Selected")

        self.create_button.clicked.connect(self.create_server)
        self.edit_button.clicked.connect(self.edit_selected)
        self.settings_button.clicked.connect(self.open_settings)
        self.start_button.clicked.connect(self.start_selected)
        self.stop_button.clicked.connect(self.stop_selected)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.status_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.create_button)
        btn_layout.addWidget(self.edit_button)
        btn_layout.addWidget(self.settings_button)
        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.stop_button)

        layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def refresh_servers(self):
        self.list_widget.clear()
        for server in self.manager.list_servers():
            self.list_widget.addItem(server)

    def create_server(self):
        dialog = CreateServerDialog(self.manager)
        if dialog.exec_():
            name = dialog.name_input.text()
            starter = dialog.template_box.currentText()
            self.manager.create_server(name, starter)
            self.refresh_servers()
            QMessageBox.information(self, "Success", f"Created server '{name}'")

    def edit_selected(self):
        item = self.list_widget.currentItem()
        if item:
            current_name = item.text()
            dialog = EditServerDialog(current_name)
            if dialog.exec_():
                new_name = dialog.new_name.text().strip()
                if new_name and self.manager.edit_server(current_name, new_name):
                    self.refresh_servers()
                    QMessageBox.information(self, "Renamed", f"Server renamed to '{new_name}'")
                else:
                    QMessageBox.warning(self, "Error", "Rename failed.")

    def open_settings(self):
        item = self.list_widget.currentItem()
        if item:
            dialog = SettingsDialog(item.text(), self.manager)
            dialog.exec_()

    def start_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self.manager.start_server(item.text())

    def stop_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self.manager.stop_server(item.text())

    def start_monitor_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_monitor)
        self.timer.start(2000)

    def update_monitor(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        self.status_label.setText(f"CPU: {cpu:.1f}% | RAM: {mem:.1f}%")

# --- Main Entry Point ---
def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
