# core2/orchestrators/security_guard.py
from __future__ import annotations

import os
import re
import resource
import signal
from typing import Dict, Any, Iterable, Optional, Set

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _parse_csv(s: Optional[str]) -> Set[str]:
    if not s:
        return set()
    return {x.strip().lower() for x in s.split(",") if x.strip()}

class SecurityGuard:
    """
    Guard corporativo:
    - Política: whitelist de lenguajes, clamp de timeout/memoria
    - Sanitización básica de código
    - Utilidades de rlimit/timeout para runners nativos
    """

    def __init__(
        self,
        *,
        allowed_languages: Optional[Iterable[str]] = None,
        max_timeout: Optional[int] = None,
        max_memory_mb: Optional[int] = None,
        # Límites POSIX opcionales por si se usan en subprocess (no obligatorios)
        cpu_seconds: Optional[int] = None,
        mem_mb: Optional[int] = None,
        fsize_mb: int = 100,
    ):
        # --- Política de lenguajes ---
        allowed = set(x.lower() for x in (allowed_languages or []))
        wl_env = _parse_csv(os.getenv("SEC_LANG_WHITELIST"))
        if wl_env:
            allowed = allowed.intersection(wl_env) if allowed else wl_env
        self.allowed_languages: Set[str] = allowed

        # --- Clamps de recursos a nivel payload ---
        self.max_timeout   = max_timeout if max_timeout is not None else _env_int("SEC_MAX_TIMEOUT", 10)
        self.max_memory_mb = max_memory_mb if max_memory_mb is not None else _env_int("SEC_MAX_MEMORY_MB", 256)

        # --- rlimits opcionales (para usar en runners si querés) ---
        self.cpu_seconds = cpu_seconds if cpu_seconds is not None else _env_int("SEC_RLIM_CPU", 5)
        self.mem_bytes   = (mem_mb if mem_mb is not None else _env_int("SEC_RLIM_MEM_MB", 256)) * 1024 * 1024
        self.fsize_bytes = fsize_mb * 1024 * 1024

    # --------- Interfaz que usa MainApp ---------
    def enforce(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida lenguaje y ajusta timeout/memoria del payload.
        Si bloquea, devuelve un dict con ok=False y mode='pre-guard'.
        """
        lang = str(payload.get("language", "")).strip().lower()
        if self.allowed_languages and lang not in self.allowed_languages:
            return {
                "ok": False,
                "exit_code": 2,
                "stdout": "",
                "stderr": f"Lenguaje no permitido por política: {lang or '(vacío)'}",
                "time_ms": 0,
                "mode": "pre-guard",
                "language": lang or "-",
            }

        # Ajustes de recursos
        try:
            t  = int(payload.get("timeout", 10))
        except Exception:
            t = 10
        try:
            mb = int(payload.get("memory_mb", 256))
        except Exception:
            mb = 256

        payload["timeout"]   = max(1, min(t, self.max_timeout))
        payload["memory_mb"] = max(16, min(mb, self.max_memory_mb))
        return payload

    # --------- Utilidades opcionales para runners ---------
    def apply_limits(self) -> None:
        """Aplica rlimits POSIX al proceso actual."""
        # CPU
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_seconds, self.cpu_seconds))
        # Memoria virtual total
        resource.setrlimit(resource.RLIMIT_AS, (self.mem_bytes, self.mem_bytes))
        # Tamaño máximo de archivos
        resource.setrlimit(resource.RLIMIT_FSIZE, (self.fsize_bytes, self.fsize_bytes))

    @staticmethod
    def sanitize_code(code: str) -> str:
        """
        Bloquea patrones obvios de abuso (puede ampliarse por lenguaje).
        """
        forbidden = [r"import\s+os", r"subprocess", r"socket", r"open\(", r"exec\("]
        for pat in forbidden:
            if re.search(pat, code, flags=re.IGNORECASE):
                raise ValueError(f"Código bloqueado por seguridad: patrón '{pat}'")
        return code

    @staticmethod
    def set_timeout(seconds: int = 10) -> None:
        """Arma un watchdog de tiempo de CPU/real con señales."""
        def handler(signum, frame):
            raise TimeoutError("Timeout alcanzado")
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(int(seconds))