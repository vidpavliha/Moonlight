import subprocess
import os
import json
import time
from pathlib import Path
from .config import load_config, save_config
import logging
import psutil

# Setup logging
logging.basicConfig(
    filename="server_manager.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class ServerManager:
    def __init__(self, server_path="servers", starters_path="assets/Server Starters"):
        self.server_path = Path(server_path)
        self.starters_path = Path(starters_path)
        self.config = load_config()

        # Use java from PATH (assumes PATH is configured properly)
        self.JAVA_PATH = "java"

        self.server_path.mkdir(exist_ok=True)
        self.starters_path.mkdir(exist_ok=True)
        print(f"[INIT] Server path: {self.server_path}")
        print(f"[INIT] Starters path: {self.starters_path}")
        print(f"[INIT] Using Java executable: {self.JAVA_PATH}")
        logging.info(f"ServerManager initialized. Java path: {self.JAVA_PATH}")

    def _accept_eula(self, server_dir):
        eula_path = server_dir / "eula.txt"
        if not eula_path.exists() or "false" in eula_path.read_text():
            with open(eula_path, "w") as f:
                f.write("eula=true\n")
            print("[EULA] Automatically accepted Minecraft EULA.")
            logging.info(f"EULA accepted at {eula_path}")

    def _run_jar_once(self, server_dir):
        cmd = [self.JAVA_PATH, "-jar", "server.jar", "nogui"]
        print(f"[RUN ONCE] Running command: {' '.join(cmd)} in {server_dir}")
        logging.info(f"Run once command: {' '.join(cmd)} in {server_dir}")
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = proc.communicate(timeout=30)
            print(f"[RUN ONCE STDOUT]\n{out}")
            print(f"[RUN ONCE STDERR]\n{err}")
            logging.info(f"Run once stdout:\n{out}")
            logging.error(f"Run once stderr:\n{err}")
        except subprocess.TimeoutExpired:
            proc.kill()
            print("[RUN ONCE] Process timed out and was killed.")
            logging.error("Run once process timed out and killed.")

    def start_server(self, name, xms=1024, xmx=8192, extra_flags=None):
        if extra_flags is None:
            extra_flags = []

        server_dir = self.server_path / name
        if not server_dir.exists():
            raise FileNotFoundError(f"Server directory {server_dir} does not exist.")

        self._accept_eula(server_dir)

        # Automatically adjust memory if over system limit
        system_ram = psutil.virtual_memory().total // (1024 * 1024)
        if xmx > system_ram - 2048:
            xmx = system_ram - 2048
            print(f"[WARN] Max RAM reduced to {xmx}MB to fit system limit.")
            logging.warning(f"Adjusted max RAM to {xmx}MB to avoid crash.")

        cmd = [
            self.JAVA_PATH,
            f"-Xms{xms}M",
            f"-Xmx{xmx}M",
            *extra_flags,
            "-jar",
            "server.jar",
            "nogui"
        ]

        print(f"[START SERVER] Starting server '{name}' with command:")
        print("  " + " ".join(cmd))
        logging.info(f"Starting server '{name}' with command: {' '.join(cmd)}")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Save PID for later stop/restart
            pid_file = server_dir / "server.pid"
            with open(pid_file, "w") as f:
                f.write(str(proc.pid))
            print(f"[PID] Server PID saved to {pid_file}")
            logging.info(f"Server PID {proc.pid} saved to {pid_file}")

            print("[START SERVER] Waiting for initial logs...")
            time.sleep(5)
            out, err = proc.communicate(timeout=10)
            print(f"[START SERVER STDOUT]\n{out}")
            print(f"[START SERVER STDERR]\n{err}")
            logging.info(f"Start server stdout:\n{out}")
            logging.error(f"Start server stderr:\n{err}")
        except subprocess.TimeoutExpired:
            print("[START SERVER] Server started in background.")
            logging.info("Server running in background (timeout)")
        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
            logging.error(f"Exception during server start: {e}")

    def stop_server(self, name):
        server_dir = self.server_path / name
        pid_file = server_dir / "server.pid"
        if pid_file.exists():
            with open(pid_file, "r") as f:
                pid = int(f.read())
            try:
                os.kill(pid, 9)  # Force kill
                print(f"[STOP SERVER] Killed process {pid}")
                logging.info(f"Stopped server '{name}', PID {pid}")
                pid_file.unlink()
            except Exception as e:
                print(f"[ERROR] Could not stop server: {e}")
                logging.error(f"Failed to stop server {name}: {e}")
        else:
            print(f"[STOP SERVER] No PID file found for {name}.")
            logging.warning(f"No PID file found to stop {name}.")

    def restart_server(self, name, xms=1024, xmx=8192, extra_flags=None):
        print(f"[RESTART SERVER] Restarting server '{name}'...")
        self.stop_server(name)
        time.sleep(2)
        self.start_server(name, xms, xmx, extra_flags)
