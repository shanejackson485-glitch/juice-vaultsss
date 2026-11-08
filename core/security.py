from pathlib import Path
import re

_PATTERNS = [
    re.compile(r"(?i)(token\s*[:=]\s*)[^\s,'\"]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,'\"]+"),
    re.compile(r"(?i)(password\s*[:=]\s*)[^\s,'\"]+"),
]

def redact(value):
    text = str(value)
    for pattern in _PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text

def safe_path(root, relative):
    root = Path(root).expanduser().resolve()
    target = (root / relative).expanduser().resolve()
    if target != root and root not in target.parents:
        raise ValueError("Path escapes the selected project folder.")
    return target

def sensitive(filename):
    name = filename.lower()
    return name in {".env", ".env.local", ".env.production", "secrets.json"} or "secret" in name
