from typing import Optional, Set
from main import MainApp

def _supported_languages() -> Set[str]:
    try:
        app = MainApp()
        return set(app.orchestrator.registry.keys())
    except Exception:
        return {"python","node","bash","c","cpp","java","go","rust","sql","r","julia"}

# Compat Pydantic v1/v2
try:
    from pydantic import BaseModel, field_validator as _validator
    def _validate_language(cls, v: str) -> str:
        langs = _supported_languages()
        v2 = v.lower()
        if v2 not in langs:
            raise ValueError(f"Lenguaje no soportado: {v}. Soportados: {sorted(langs)}")
        return v2
    class JobRequest(BaseModel):
        language: str
        code: str
        stdin: Optional[str] = None
        timeout: int = 10
        cpu: int = 1
        mem_mb: int = 512
        _lang_ok = _validator("language")(_validate_language)
except Exception:
    from pydantic import BaseModel, validator
    class JobRequest(BaseModel):
        language: str
        code: str
        stdin: Optional[str] = None
        timeout: int = 10
        cpu: int = 1
        mem_mb: int = 512
        @validator("language")
        def _lang_ok(cls, v: str) -> str:
            langs = _supported_languages()
            v2 = v.lower()
            if v2 not in langs:
                raise ValueError(f"Lenguaje no soportado: {v}. Soportados: {sorted(langs)}")
            return v2
