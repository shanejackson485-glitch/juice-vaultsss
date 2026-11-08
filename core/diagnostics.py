from pathlib import Path
import importlib.util, shutil, subprocess, sys

class ProjectDiagnostics:
    def inspect(self, project):
        project = Path(project).expanduser().resolve()
        checks = []
        def add(name, ok, detail, severity="WARN"):
            checks.append({"name": name, "ok": bool(ok), "detail": str(detail), "severity": severity})
        add("Project directory", project.is_dir(), project, "ERROR")
        add("Python executable", bool(shutil.which("python") or sys.executable), sys.executable)
        add("Node.js", bool(shutil.which("node")), shutil.which("node") or "Not found")
        has_discord = importlib.util.find_spec("discord") is not None
        add("discord.py import", has_discord, "Available in dashboard interpreter" if has_discord else "Not installed in dashboard interpreter")
        entries = [x for x in ("bot.py", "main.py", "index.js", "src/index.js") if (project/x).exists()]
        add("Entry point", bool(entries), ", ".join(entries) if entries else "No common entry file found")
        manifests = [x for x in ("requirements.txt", "pyproject.toml", "package.json") if (project/x).exists()]
        add("Dependency manifest", bool(manifests), ", ".join(manifests) if manifests else "No manifest found")
        add("Environment file", (project/".env").exists(), ".env configured" if (project/".env").exists() else "No .env file")
        return checks

    def code_stats(self, project):
        ignored = {".git", ".venv", "venv", "node_modules", "__pycache__", ".bot_studio"}
        suffixes = {".py", ".js", ".ts", ".json", ".toml", ".yaml", ".yml", ".html", ".css"}
        count, lines = 0, 0
        for path in Path(project).rglob("*"):
            if path.is_file() and path.suffix.lower() in suffixes and not any(x in ignored for x in path.parts):
                try:
                    lines += sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
                    count += 1
                except OSError:
                    pass
        return count, lines
