# main.py
from __future__ import annotations
import os
from typing import Dict, Any, Optional, Iterable

# ---------------- Memory (shim si falta) ----------------
try:
    from memory.memory import Memory
except Exception:
    class Memory:  # type: ignore[override]
        def __init__(self, max_events: int = 20):
            self._ev = []
        def add(self, role: str, content: str):
            self._ev.append({"role": role, "content": content})
        def get_context(self):
            return list(self._ev)

# ---------------- Orquestador base ----------------
from core2.orchestrators.gozo_lite import GozoLite

# ---------------- Utils ENV ----------------
def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _parse_csv(s: Optional[str]) -> set[str]:
    if not s:
        return set()
    return {x.strip().lower() for x in s.split(",") if x.strip()}

# ---------------- SecureMiddleware (real o shim) ----------------
# Preferimos tus módulos en ./security/*
try:
    # Ruta local que creaste: security/secure_middleware.py
    from security.secure_middleware import SecureMiddleware  # type: ignore
    SECURE_AVAILABLE = True
except Exception:
    SECURE_AVAILABLE = False

# Fallback “guard” minimalista (por compatibilidad si faltan módulos)
class _ClampGuard:
    def __init__(self, allowed_languages: Iterable[str]):
        wl_env = _parse_csv(os.getenv("SEC_LANG_WHITELIST"))
        self.allowed = set(allowed_languages) if not wl_env else set(allowed_languages).intersection(wl_env)
        self.max_timeout   = _env_int("SEC_MAX_TIMEOUT", 15)
        self.max_memory_mb = _env_int("SEC_MAX_MEMORY_MB", 512)

    def enforce(self, payload: Dict[str, Any]) -> Dict[str, Any] | Dict[str, Any]:
        lang = str(payload.get("language", "")).strip().lower()
        if self.allowed and lang and (lang not in self.allowed and lang != "auto"):
            return {
                "ok": False,
                "exit_code": 2,
                "stdout": "",
                "stderr": f"Lenguaje no permitido por política: {lang or '(vacío)'}",
                "time_ms": 0,
                "mode": "guard-block",
                "language": lang or "-",
            }
        # Clamp
        t  = int(payload.get("timeout", 10))
        mb = int(payload.get("memory_mb", 256))
        payload["timeout"]   = max(1, min(t, self.max_timeout))
        payload["memory_mb"] = max(16, min(mb, self.max_memory_mb))
        return payload


# ---------------- Main ----------------
class MainApp:
    def __init__(self):
        self.memory = Memory(max_events=int(os.getenv("MEMORY_MAX_EVENTS", "20")))
        base = GozoLite(self.memory)

        if SECURE_AVAILABLE:
            # Seguridad avanzada: validator + policy + audit + rusage
            self.orchestrator = SecureMiddleware(base)  # expone .submit(...)
            self.mode_name = "gozo-lite+secure"
            self.memory.add("system", "[Main] Orchestrator=GozoLite + SecureMiddleware ON")
        else:
            # Fallback: clamps básicos, sin auditoría avanzada
            self._guard = _ClampGuard(allowed_languages=base.registry.keys())
            self._base  = base
            self.orchestrator = None
            self.mode_name = "gozo-lite+clamp"
            self.memory.add("system", "[Main] Orchestrator=GozoLite + ClampGuard (fallback)")

    def submit(self, language: str, code: str, timeout: int = 10, memory_mb: int = 256) -> Dict[str, Any]:
        # Camino con seguridad avanzada
        if self.orchestrator is not None:
            res = self.orchestrator.submit(
                language=(language or "python"),
                code=code,
                timeout=timeout,
                memory_mb=memory_mb,
            )
            # Normalización
            ok = bool(res.get("ok", res.get("exit_code", 1) == 0))
            exit_code = int(res.get("exit_code", 1))
            mode = str(res.get("mode", self.mode_name))
            self.memory.add("system", f"[Main.submit] mode={mode} ok={ok} exit={exit_code} lang={language}")
            return {
                "ok": ok,
                "exit_code": exit_code,
                "stdout": str(res.get("stdout", "")),
                "stderr": str(res.get("stderr", "")),
                "time_ms": int(res.get("time_ms", 0)),
                "mode": mode,
            }

        # Fallback sencillo con clamps
        raw_payload = {
            "language": language,
            "code": code,
            "timeout": timeout,
            "memory_mb": memory_mb,
        }
        guarded = self._guard.enforce(raw_payload)
        if isinstance(guarded, dict) and guarded.get("mode") == "guard-block":
            self.memory.add("system", f"[Guard.block] lang={language} reason={guarded.get('stderr','')}")
            return {
                "ok": False,
                "exit_code": int(guarded.get("exit_code", 2)),
                "stdout": str(guarded.get("stdout", "")),
                "stderr": str(guarded.get("stderr", "Bloqueado por política de seguridad")),
                "time_ms": int(guarded.get("time_ms", 0)),
                "mode": "guard-block",
            }

        payload = guarded if isinstance(guarded, dict) else raw_payload
        res = self._base.execute(payload)  # GozoLite
        ok = bool(res.get("ok", False))
        exit_code = int(res.get("exit_code", 1))
        mode = str(res.get("mode", self.mode_name))
        self.memory.add("system", f"[Main.submit] mode={mode} ok={ok} exit={exit_code} lang={payload.get('language')}")
        return {
            "ok": ok,
            "exit_code": exit_code,
            "stdout": str(res.get("stdout", "")),
            "stderr": str(res.get("stderr", "")),
            "time_ms": int(res.get("time_ms", 0)),
            "mode": mode,
        }

    def status(self, job_id: str):
        try:
            # GozoLite es síncrono; mantenemos la firma
            return {"job_id": job_id, "state": "unsupported", "detail": "GozoLite es síncrono"}
        except Exception as e:
            return {"job_id": job_id, "state": "error", "detail": str(e)}

    def history(self):
        try:
            return self.memory.get_context()
        except Exception as e:
            return [{"role": "system", "content": f"history error: {e}"}]

# export
main = MainApp()

def normalize_response(exit_code: int, stdout: str = "", stderr: str = "") -> dict:
    return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}

def health() -> dict:
    return {"status": "ok"}