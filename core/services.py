from pathlib import Path
import json
import threading
import streamlit as st
from core.process import ProcessController
from core.templates import TemplateCatalog
from core.diagnostics import ProjectDiagnostics

class Settings:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.data = {
            "project": str(Path.cwd()), "command": "python bot.py",
            "runtime": "Python", "entry": "bot.py", "restart_delay": 2,
            "auto_restart": False, "backup_excludes": [".git", ".venv", "venv",
            "__pycache__", "node_modules", ".bot_studio"]
        }
        self.load()

    def load(self):
        try:
            self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass

    def save(self):
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            temp.replace(self.path)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set_many(self, **values):
        self.data.update(values)
        self.save()

class Services:
    def __init__(self):
        self.data = Path.cwd() / ".bot_studio"
        self.data.mkdir(exist_ok=True)
        self.settings = Settings(self.data / "settings.json")
        self.process = ProcessController(self.data / "logs")
        self.templates = TemplateCatalog()
        self.diagnostics = ProjectDiagnostics()

@st.cache_resource
def services():
    return Services()
