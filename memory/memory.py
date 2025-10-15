# core2/memory/memory.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import time, os, json, threading

class Memory:
    """
    Registro ligero de eventos del sistema.
    Incluye timestamp, rol, contenido y metadatos.
    Autolimita el tamaño para evitar desbordes de memoria.
    Thread-safe: soporta múltiples hilos.
    """

    def __init__(self, max_events: int = 50):
        self.max_events = max_events
        self._events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def add(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """Agrega un evento con rol, contenido y metadatos opcionales."""
        event = {
            "ts": time.time(),
            "role": role,
            "content": content,
            "meta": meta or {}
        }
        with self._lock:
            self._events.append(event)
            # Mantener tamaño fijo
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events:]

    def get_context(self) -> List[Dict[str, Any]]:
        """Devuelve copia de los eventos actuales."""
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        """Limpia la memoria."""
        with self._lock:
            self._events.clear()

    def preamble(self) -> str:
        """Mensaje inicial de sistema con branding y seguridad."""
        org = os.getenv("ORG_NAME", "CodeExecutor")
        return f"[SYSTEM] {org}: orquestador seguro, sin red, límites activos."

    def export_json(self) -> str:
        """Exporta eventos a JSON (para auditoría/logs)."""
        with self._lock:
            return json.dumps(self._events, indent=2)

    def last_event(self) -> Optional[Dict[str, Any]]:
        """Devuelve el último evento, si existe."""
        with self._lock:
            return self._events[-1] if self._events else None
