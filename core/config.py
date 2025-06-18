import json
from pathlib import Path

CONFIG_PATH = Path("moonlight/config.json")

DEFAULT_CONFIG = {
    "java_path": "C:/Program Files/Java/jdk-21/bin/java.exe"
}

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
