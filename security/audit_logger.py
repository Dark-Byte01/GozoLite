from __future__ import annotations
import json, os, uuid, time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

AUDIT_PATH = os.getenv("SEC_AUDIT_PATH", "/tmp/gozolite_audit.jsonl")

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_audit(entry: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
        with open(AUDIT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # nunca rompemos la ejecución por el logger

class AuditTrail:
    def __init__(self, request: Dict[str, Any]):
        self.job_id = str(uuid.uuid4())
        self.request = request
        self.started_monotonic = time.monotonic()

    def start(self, policy: Dict[str, Any]) -> None:
        write_audit({
            "ts": _ts(), "evt": "START",
            "job_id": self.job_id,
            "request": {"language": self.request.get("language"), "code_len": len((self.request.get("code") or "").encode("utf-8"))},
            "policy": policy,
        })

    def end(self, result: Dict[str, Any], resources: Optional[Dict[str, Any]] = None) -> None:
        elapsed_ms = int((time.monotonic() - self.started_monotonic) * 1000)
        write_audit({
            "ts": _ts(), "evt": "END",
            "job_id": self.job_id,
            "elapsed_ms": elapsed_ms,
            "result": {
                "exit_code": result.get("exit_code"),
                "stdout_len": len((result.get("stdout") or "")),
                "stderr_len": len((result.get("stderr") or "")),
                "mode": result.get("mode"),
                "language": result.get("language"),
            },
            "resources": resources or {},
        })

    def reject(self, reason: str) -> None:
        write_audit({
            "ts": _ts(), "evt": "REJECT",
            "job_id": self.job_id,
            "reason": reason,
            "request": {"language": self.request.get("language")},
        })