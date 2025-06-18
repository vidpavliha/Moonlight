import os
import shutil
from datetime import datetime

def backup_server(server_dir):
    if not os.path.exists(server_dir):
        raise FileNotFoundError("Server directory not found")
    backup_dir = f"{server_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(server_dir, backup_dir)
    return backup_dir
