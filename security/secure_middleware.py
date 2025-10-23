from __future__ import annotations
from typing import Dict, Any, Optional

from .input_validator import validate_request
from .policy_enforcer import build_policy, policy_dict
from .audit_logger import AuditTrail
from .resource_monitor import snapshot_rusage, diff_usage

class SecureMiddleware:
    """
    Envoltorio de seguridad para un orquestador estilo GozoLite.
    - Valida input (deny patterns, tamaño, líneas, bloques)
    - Ajusta timeout/memoria (clamp) según política
    - Audita START/END/REJECT a JSONL
    - Toma rusage (aprox) antes/después
    """

    def __init__(self, orchestrator: Any):
        self.orch = orchestrator

    def submit(self, *, language: str, code: str, timeout: int, memory_mb: int, stdin: Optional[str] = None) -> Dict[str, Any]:
        req = {"language": language, "code": code}
        audit = AuditTrail(req)

        ok, reason = validate_request(language, code, blocks=1)
        if not ok:
            audit.reject(reason)
            return {
                "exit_code": 2,
                "mode": getattr(self.orch, "MODE", "secure"),
                "stdout": "",
                "stderr": f"Bloqueado por política: {reason}",
            }

        pol = build_policy(timeout, memory_mb)
        audit.start(policy_dict(pol))

        # rusage antes
        before = snapshot_rusage()

        payload = {
            "language": (language or "").strip().lower(),
            "code": code,
            "timeout": pol.timeout,
            "memory_mb": pol.memory_mb,
        }
        if stdin is not None:
            payload["stdin"] = stdin

        try:
            # GozoLite expone execute(payload) o run/submit con kwargs
            if hasattr(self.orch, "execute"):
                res = self.orch.execute(payload=payload)
            elif hasattr(self.orch, "run"):
                res = self.orch.run(**payload)
            elif hasattr(self.orch, "submit"):
                res = self.orch.submit(**payload)
            else:
                res = {"exit_code": 2, "stdout": "", "stderr": "Orquestador no expone execute/run/submit", "mode": "secure"}

        except Exception as e:
            res = {"exit_code": 1, "stdout": "", "stderr": f"orchestrator error: {e}", "mode": "secure"}

        # rusage después
        after = snapshot_rusage()
        usage = diff_usage(before, after)
        audit.end(res, resources=usage)
        return res