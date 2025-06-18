import os
import shutil
import requests

class PluginManager:
    def __init__(self, server_dir):
        self.plugins_dir = os.path.join(server_dir, "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)

    def install_plugin(self, plugin_url):
        filename = plugin_url.split("/")[-1]
        response = requests.get(plugin_url)
        with open(os.path.join(self.plugins_dir, filename), "wb") as f:
            f.write(response.content)

    def list_plugins(self):
        return os.listdir(self.plugins_dir)

    def remove_plugin(self, name):
        os.remove(os.path.join(self.plugins_dir, name))
