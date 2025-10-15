from __future__ import annotations
import os, re
from typing import Tuple, Optional, Dict, Pattern, Iterable

# ===== Config (ENV) =====
MAX_CODE_BYTES = int(os.getenv("SEC_MAX_CODE_BYTES", "65536"))     # 64 KiB
MAX_LINES      = int(os.getenv("SEC_MAX_LINES", "1200"))
MAX_BLOCKS     = int(os.getenv("SEC_MAX_BLOCKS", "20"))            # si usás fences
ALLOW_NET      = os.getenv("SEC_ALLOW_NET", "false").lower() in ("1","true","yes")

# Si querés whitelistear lenguajes: "python,node,c,cpp,go,rust,java,sql,..."
LANG_WHITELIST = {x.strip().lower() for x in os.getenv("SEC_LANG_WHITELIST","").split(",") if x.strip()}

# Patrones peligrosos por lenguaje (defensa en profundidad; no pretende ser perfecto)
_GLOBAL_DENY: Iterable[Pattern] = [
    re.compile(r"\b(base64\s*\.\s*b64decode|marshal\.loads|pickle\.loads)\b", re.I),
    re.compile(r"\b(eval|exec)\s*\(", re.I),
]
_PY_DENY: Iterable[Pattern] = [
    re.compile(r"\b(os|sys|subprocess|socket|fcntl|resource|pty|shlex|ctypes)\b", re.I),
    re.compile(r"\bopen\s*\(\s*['\"]/etc/", re.I),
]
_NODE_DENY: Iterable[Pattern] = [
    re.compile(r"\brequire\s*\(\s*['\"](child_process|fs|net|dgram|tls|vm)['\"]\s*\)", re.I),
]
_SHELL_DENY: Iterable[Pattern] = [
    re.compile(r";\s*(curl|wget)\b", re.I),
    re.compile(r"\b(exec|sudo|setfacl|mount|insmod|modprobe)\b", re.I),
]

LANG_DENY_MAP: Dict[str, Iterable[Pattern]] = {
    "python": _PY_DENY,
    "node": _NODE_DENY,
    "javascript": _NODE_DENY,
    "bash": _SHELL_DENY,
    "sh": _SHELL_DENY,
}

def validate_request(language: str, code: str, blocks: int = 1) -> Tuple[bool, Optional[str]]:
    lang = (language or "").strip().lower()
    if LANG_WHITELIST and lang and (lang not in LANG_WHITELIST and lang != "auto"):
        return False, f"Lenguaje '{lang}' no permitido por política (SEC_LANG_WHITELIST)."

    if blocks > MAX_BLOCKS:
        return False, f"Exceso de bloques ({blocks}>{MAX_BLOCKS})."

    enc = code.encode("utf-8", errors="ignore")
    if len(enc) > MAX_CODE_BYTES:
        return False, f"Code demasiado grande ({len(enc)} bytes > {MAX_CODE_BYTES})."

    if code.count("\n") + 1 > MAX_LINES:
        return False, f"Demasiadas líneas de código (> {MAX_LINES})."

    # Deny patterns
    for pat in _GLOBAL_DENY:
        if pat.search(code):
            return False, f"Patrón global bloqueado: /{pat.pattern}/"

    lang_pats = LANG_DENY_MAP.get(lang, [])
    for pat in lang_pats:
        if pat.search(code):
            return False, f"Patrón bloqueado para {lang}: /{pat.pattern}/"

    # Red (solo si NO se permite explícitamente)
    if not ALLOW_NET and re.search(r"\b(socket|requests|urllib|fetch|http\.|https\.)\b", code, re.I):
        return False, "Acceso de red bloqueado por política (SEC_ALLOW_NET=false)."

    return True, None