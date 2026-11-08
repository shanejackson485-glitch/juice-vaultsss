from __future__ import annotations
import os, shlex, signal, subprocess, threading, time
from collections import deque
from datetime import datetime
from pathlib import Path
from core.security import redact

class ProcessController:
    """Single-process supervisor with log capture, graceful stop and status tracking."""
    def __init__(self, log_dir, max_lines=6000):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "console.log"
        self.rows = deque(maxlen=max_lines)
        self.lock = threading.RLock()
        self.proc = None
        self.started = None
        self.exit_code = None
        self.command = ""
        self.reader = None
        self._log("Vanta process supervisor ready", "SYSTEM")

    @property
    def running(self):
        return bool(self.proc and self.proc.poll() is None)

    def _log(self, message, level="INFO"):
        row = {
            "time": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level.upper(), "message": redact(str(message).rstrip())
        }
        with self.lock:
            self.rows.append(row)
            try:
                with self.log_file.open("a", encoding="utf-8") as f:
                    f.write(f"[{row['time']}] [{row['level']}] {row['message']}\n")
            except OSError:
                pass

    def _pump(self, proc):
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                text = line.rstrip()
                low = text.lower()
                level = "ERROR" if any(x in low for x in ("traceback", "exception", "error:", "fatal")) else "INFO"
                self._log(text, level)
        except Exception as exc:
            self._log(f"Log stream error: {exc}", "ERROR")
        finally:
            code = proc.poll()
            with self.lock:
                if self.proc is proc:
                    self.exit_code = code
            if code is not None:
                self._log(f"Process exited with code {code}", "SYSTEM")

    def start(self, command, cwd, env=None):
        with self.lock:
            if self.running:
                return False, "A bot process is already running."
            cwd = Path(cwd).expanduser().resolve()
            if not cwd.is_dir():
                return False, f"Project folder does not exist: {cwd}"
            try:
                args = shlex.split(command, posix=os.name != "nt")
                if not args:
                    return False, "Startup command is empty."
                child_env = os.environ.copy()
                child_env.update(env or {})
                options = dict(cwd=str(cwd), env=child_env, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True,
                    encoding="utf-8", errors="replace", bufsize=1)
                if os.name == "nt":
                    options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    options["start_new_session"] = True
                self.command = command
                self.exit_code = None
                self._log("$ " + command, "COMMAND")
                self.proc = subprocess.Popen(args, **options)
                self.started = time.time()
                self._log(f"Started PID {self.proc.pid}", "SYSTEM")
                self.reader = threading.Thread(target=self._pump, args=(self.proc,), daemon=True)
                self.reader.start()
                return True, f"Bot started · PID {self.proc.pid}"
            except FileNotFoundError:
                self._log("Startup executable not found. Check runtime/PATH.", "ERROR")
                return False, "Executable not found. Check Python/Node and your startup command."
            except Exception as exc:
                self._log(f"Startup failed: {exc}", "ERROR")
                return False, str(exc)

    def stop(self, timeout=8):
        with self.lock:
            proc = self.proc
            if not proc or proc.poll() is not None:
                return False, "Bot is not running."
            self._log("Graceful stop requested", "SYSTEM")
            try:
                if os.name == "nt":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                try:
                    proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    self._log("Grace period expired; force stopping process", "WARN")
                    proc.kill()
                    proc.wait(timeout=3)
                self._log("Bot stopped", "SYSTEM")
                return True, "Bot stopped."
            except Exception as exc:
                self._log(f"Stop failed: {exc}", "ERROR")
                return False, str(exc)

    def restart(self, command, cwd, delay=2, env=None):
        self.stop()
        time.sleep(max(0, min(float(delay), 15)))
        return self.start(command, cwd, env)

    def status(self):
        return {
            "running": self.running,
            "pid": self.proc.pid if self.running else None,
            "uptime": int(time.time() - self.started) if self.running and self.started else 0,
            "exit_code": self.exit_code,
            "command": self.command
        }

    def snapshot(self, limit=5000):
        with self.lock:
            return list(self.rows)[-limit:]

    def clear(self):
        with self.lock:
            self.rows.clear()
            self.log_file.write_text("", encoding="utf-8")
        self._log("Console cleared", "SYSTEM")

    def log_text(self):
        try:
            return self.log_file.read_text(encoding="utf-8", errors="replace")[-1_000_000:]
        except OSError:
            return ""
