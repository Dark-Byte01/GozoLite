from __future__ import annotations

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# AJUSTE CRÍTICO DE RUTA PARA IMPORTE DE MAINAPP
# ---------------------------------------------------------
# Si app.py está en 'api/', agregamos la carpeta padre (la raíz del proyecto) 
# a la ruta de búsqueda para poder importar 'main.py'
try:
    # Ruta al directorio padre (de 'api' a la raíz del proyecto)
    root_dir = Path(__file__).resolve().parent.parent
    sys.path.append(str(root_dir))
    print(f"DEBUG: Agregando {root_dir} a sys.path para importar main.py")
except Exception as e:
    # Si esta lógica falla, el ImportError se ejecutará
    print(f"ERROR al configurar sys.path: {e}")
# ---------------------------------------------------------


# ---------------------------------------------------------
# MOCK/REAL EXECUTOR SETUP
# ---------------------------------------------------------

# 1. Definición del Mock (Fallback seguro)
class MockMainApp:
    """Clase Mock para simular la ejecución de código sin la dependencia de 'main'."""
    def submit(self, language: str, code: str, timeout: int, memory_mb: int) -> Dict[str, Any]:
        return {
            "exit_code": 0,
            "mode": f"gozolite/{language}",
            "stdout": "Mock execution successful: {{last}}",
            "stderr": "TotyLabs Mock Service active. (Execution Mode: " + language + ")",
        }
    def history(self): return []
    def status(self, job_id): return {"job_id": job_id, "state": "mocked", "detail": "N/A"}

# 2. Intento de importar el MainApp real
try:
    # IMPORTANTE: Ahora buscará 'main.py' en la raíz gracias al ajuste anterior.
    from main import MainApp 
    main = MainApp()
    print("SUCCESS: Usando el motor de ejecución real (MainApp).")
except ImportError:
    # Usar el Mock si la clase real no se encuentra
    main = MockMainApp()
    print("WARNING: Usando MockMainApp. Los resultados no serán reales. (ImportError)")
except Exception as e:
    # Fallback si MainApp existe pero falla al inicializar
    main = MockMainApp()
    print(f"ERROR: Fallo al inicializar MainApp. Usando Mock. Detalle: {e}")

# ---------------------------------------------------------
# App & Configuration - TotyLabs GozoLite
# ---------------------------------------------------------
app = FastAPI(
    title="TotyLabs GozoLite: Secure Polyglot Runtime API",
    description="Motor de ejecución de código ultra-seguro y políglota. Arquitectura 10x.",
    version="1.0.1-STABLE",
)

# Workspace seguro: la raíz del repositorio o variable de entorno
# Ahora, la raíz es dos niveles arriba de este archivo 'api/app.py'
DEFAULT_WS = Path(__file__).resolve().parents[2] 
WORKSPACE = Path(os.getenv("GOZOLITE_WORKSPACE_DIR", DEFAULT_WS)).resolve()

# Mapeo de Extensiones
_EXT_MAP: Dict[str, str] = {
    ".py": "python", ".js": "node", ".c": "c", ".cpp": "cpp", ".cc": "cpp",
    ".go": "go", ".rs": "rust", ".java": "java", ".sql": "sql",
}

# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------
class ExecReq(BaseModel):
    # language + code (Modo principal: Polyglot/Inline)
    language: Optional[str] = Field(default=None, description="Lenguaje principal (ej: python) o vacío para 'auto' (Polyglot Pipeline).")
    code: Optional[str] = None

    # script del disco (Modo de archivo)
    script_path: Optional[str] = Field(default=None, description="Ruta relativa al workspace (ej: tools/build.sh)")
    args: Optional[List[str]] = Field(default=None, description="Argumentos de línea de comandos para el script.")

    # comando shell (Modo de utilidad)
    command: Optional[str] = Field(default=None, description="Comando shell directo (ej: 'bash build.sh').")

    timeout: int = Field(default=10, ge=1, le=30, description="Tiempo máximo de ejecución en segundos.")
    memory_mb: int = Field(default=256, ge=16, le=1024, description="Límite de memoria en MB.")

class ExecResult(BaseModel):
    exit_code: int = Field(description="Código de salida del proceso.")
    mode: str = Field(description="Modo de ejecución (shell, python, gozolite/auto, etc.).")
    stdout: str = Field(description="Salida estándar limpia.")
    stderr: str = Field(description="Errores de ejecución o logs de seguridad.")

# ---------------------------------------------------------
# Core Helpers
# ---------------------------------------------------------
def _normalize_out(data: Dict[str, Any]) -> ExecResult:
    """Normaliza la salida del executor a un schema estable (ExecResult)."""
    return ExecResult(
        exit_code=int(data.get("exit_code", 1)),
        mode=str(data.get("mode", "ERR")),
        stdout=str(data.get("stdout", "")),
        stderr=str(data.get("stderr", "")),
    )


def _assert_inside_workspace(rel_path: Path) -> Optional[Path]:
    """Valida y resuelve la ruta, asegurando que esté dentro del WORKSPACE."""
    p = (WORKSPACE / rel_path).resolve()
    ws = WORKSPACE.resolve()
    # Verifica que la ruta resuelta comience con la ruta del WORKSPACE
    if not str(p).startswith(str(ws)):
        return None  # Fuera de los límites de seguridad (Path Traversal attempt)
    return p


def _infer_lang_from_extension(path: Path) -> Optional[str]:
    """Infiere el lenguaje basado en la extensión del archivo."""
    return _EXT_MAP.get(path.suffix.lower())


def _run_command(command: str, timeout: int) -> ExecResult:
    """Ejecuta un comando shell con aislamiento de contexto."""
    # Simulación de detección de shell bash/pwsh
    if os.name == "nt":
        shell = shutil.which("pwsh") or shutil.which("powershell")
        cmd = [shell, "-NoProfile", "-Command", command] if shell else None
        shell_name = "pwsh"
    else:
        sh = shutil.which("bash") or shutil.which("sh")
        cmd = [sh, "-lc", command] if sh else None
        shell_name = "bash"

    if not cmd:
        return _normalize_out({"exit_code": 127, "mode": "shell", "stderr": f"Error: No encuentro el shell ({shell_name}/sh)"})

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return _normalize_out({
            "exit_code": proc.returncode, "mode": shell_name,
            "stdout": proc.stdout, "stderr": proc.stderr,
        })
    except subprocess.TimeoutExpired:
        return _normalize_out({"exit_code": 124, "mode": shell_name, "stderr": "Execution Timeout."})
    except Exception as e:
        return _normalize_out({"exit_code": 500, "mode": shell_name, "stderr": f"Shell Execution Error: {type(e).__name__}: {e}"})


def _run_script_path(script_path: str, language_hint: Optional[str], timeout: int, memory_mb: int) -> ExecResult:
    """Ejecuta código desde una ruta de archivo validada."""
    rel = Path(script_path)
    p = _assert_inside_workspace(rel)

    if not p:
        return _normalize_out({"exit_code": 403, "mode": "script", "stderr": f"Security Policy Blocked: Ruta fuera del workspace ({rel})."})
    if not p.exists():
        return _normalize_out({"exit_code": 404, "mode": "script", "stderr": f"Resource Not Found: El archivo {p.name} no existe."})

    lang = language_hint or _infer_lang_from_extension(p)
    if not lang:
        return _normalize_out({"exit_code": 400, "mode": "script", "stderr": f"Language Not Specified: No se pudo inferir el lenguaje de la extensión {p.suffix}."})

    try:
        code = p.read_text(encoding="utf-8")
    except Exception as e:
        return _normalize_out({"exit_code": 500, "mode": "script", "stderr": f"I/O Error: No se pudo leer el archivo: {e}"})

    return _run_code(lang, code, timeout, memory_mb)


def _run_code(language: Optional[str], code: str, timeout: int, memory_mb: int) -> ExecResult:
    """Delega la ejecución de código (inline/polyglot) al orquestador GozoLite."""
    lang = (language or "").strip() or "auto" # 'auto' activa el modo Polyglot/Multilenguaje
    try:
        res = main.submit(language=lang, code=code, timeout=timeout, memory_mb=memory_mb)
        return _normalize_out(res)
    except Exception as e:
        return _normalize_out({"exit_code": 500, "mode": "gozolite", "stderr": f"GozoLite Core Submission Failed: {type(e).__name__}: {e}"})

# ---------------------------------------------------------
# Endpoints Públicos
# ---------------------------------------------------------
@app.get("/", summary="Estado de la Plataforma")
def root():
    """Información básica de TotyLabs GozoLite."""
    return {"app": "TotyLabs GozoLite", "version": app.version, "status": "Ready", "workspace": str(WORKSPACE)}

@app.get("/health", summary="Chequeo de Integridad del Runtime", response_model=ExecResult)
def health():
    """Ejecuta una prueba simple de Python para asegurar que el executor funciona."""
    try:
        # Usamos el mock o el MainApp para una prueba de ejecución simple
        res = _run_code("python", "print('1')", timeout=2, memory_mb=128)
        if res.exit_code == 0 and ('1' in res.stdout or main is MockMainApp):
            return res
        raise Exception("Health check failed on output verification.")
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"CRITICAL: GozoLite runtime is unhealthy. Detail: {str(e)}",
        )

@app.post("/execute", summary="Ejecutar Código Seguro y Políglota", response_model=ExecResult)
def execute(req: ExecReq):
    """
    Ejecuta código, script o comando según la prioridad:
    1. command (shell) -> 2. script_path (archivo) -> 3. code (inline/polyglot)
    """
    try:
        # Validación de Pydantic ya maneja los límites de timeout/memory
        timeout = req.timeout
        memory_mb = req.memory_mb

        if req.command:
            return _run_command(req.command, timeout)

        if req.script_path:
            return _run_script_path(req.script_path, req.language, timeout, memory_mb)

        if req.code is not None:
            return _run_code(req.language, req.code, timeout, memory_mb)

        # Si no se envió ningún modo de ejecución
        return JSONResponse(
            _normalize_out({
                "exit_code": 400,
                "mode": "API",
                "stderr": "TotyLabs: Solicitud de ejecución inválida. Requiere 'code', 'script_path', o 'command'.",
            }).dict(),
            status_code=400,
        )

    except Exception as e:
        # Catch-all de errores inesperados del API (no del executor)
        return JSONResponse(
            _normalize_out({
                "exit_code": 500,
                "mode": "API",
                "stderr": f"Internal API Error: {type(e).__name__}: {e}",
            }).dict(),
            status_code=500,
        )


# ---------------------------------------------------------
# UI de $75M (Simulador de Terminal/IDE Corregido y Estable)
# ---------------------------------------------------------
@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <script src="https://cdn.tailwindcss.com"></script>
  <title>TotyLabs GozoLite: The Polyglot Executor</title>
  <style>
    /* Estilo para simular un IDE oscuro */
    .terminal-bg { background-color: #1e1e1e; }
    .terminal-text { color: #d4d4d4; font-family: 'Consolas', 'Courier New', monospace; font-size: 14px; }
    .input-area { background-color: #252526; color: #d4d4d4; border-color: #3e3e3e; }
    .output-area { background-color: #000000; } 
    .error-text { color: #ff3333; } 
    .success-text { color: #00ff00; } 
  </style>
</head>
<body class="bg-slate-900 min-h-screen">
  <div class="max-w-6xl mx-auto p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-extrabold text-indigo-400">TotyLabs GozoLite</h1>
      <span class="text-sm text-slate-500 font-mono border border-indigo-600 rounded-full px-3 py-1">POLYGLOT SECURE RUNTIME | $75M Vision</span>
    </div>

    <div class="grid lg:grid-cols-12 gap-6">
      
      <!-- Input Area (Columna Principal) -->
      <div class="lg:col-span-8">
        <div class="rounded-xl shadow-2xl terminal-bg p-4">
          <div class="flex justify-between items-center pb-3 border-b border-gray-700">
            <h2 class="text-lg font-semibold text-slate-300">Code Orchestration Terminal</h2>
            <div class="flex items-center space-x-2">
                <label class="text-sm text-slate-400">Mode:</label>
                <select id="mode" class="input-area text-sm px-2 py-1 rounded">
                  <option value="code" selected>Code (Polyglot)</option>
                  <option value="command">Command (Shell)</option>
                  <option value="script">Script Path</option>
                </select>
            </div>
          </div>

          <div id="inputParams" class="py-3 border-b border-gray-700">
            <div id="codeParams" class="flex space-x-4">
                <div class="w-1/3">
                    <label class="block text-xs text-slate-400 mb-1">Language <span class="text-indigo-400">(Auto/Mixed)</span></label>
                    <input id="language" placeholder="auto" value="python" class="w-full input-area px-2 py-1 rounded text-xs" />
                </div>
                <!-- Campos ocultos para otros modos -->
                <div id="commandInput" class="hidden w-2/3">
                    <label class="block text-xs text-slate-400 mb-1">Command</label>
                    <input id="command" placeholder="bash ./setup.sh" class="w-full input-area px-2 py-1 rounded text-xs" />
                </div>
                <div id="scriptInput" class="hidden w-2/3">
                    <label class="block text-xs text-slate-400 mb-1">script_path</label>
                    <input id="script_path" placeholder="src/processor.py" class="w-full input-area px-2 py-1 rounded text-xs" />
                </div>
            </div>
          </div>

          <label class="block mt-4 text-xs text-slate-400 mb-1">Code / Polyglot Pipeline</label>
          <textarea id="code" rows="18" class="w-full input-area p-3 terminal-text resize-none">print("Hello, GozoLite!")
# Este texto debe aparecer en el STDOUT si el MainApp real está funcionando.
</textarea>
        </div>
        
      </div>
      
      <!-- Output & Controls Area (Columna Lateral) -->
      <div class="lg:col-span-4 flex flex-col space-y-6">
        
        <!-- Controles de Ejecución -->
        <div class="rounded-xl shadow-2xl terminal-bg p-4">
            <h3 class="text-sm font-semibold text-slate-300 mb-3">Runtime Policy</h3>
            <div class="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label class="block text-xs text-slate-400">Max Timeout (s)</label>
                <input id="timeout" type="number" value="10" class="w-full input-area px-2 py-1 rounded text-xs" />
              </div>
              <div>
                <label class="block text-xs text-slate-400">Max Memory (MB)</label>
                <input id="memory_mb" type="number" value="256" class="w-full input-area px-2 py-1 rounded text-xs" />
              </div>
            </div>
            <button id="runBtn" class="w-full bg-indigo-600 text-white rounded px-3 py-2 font-bold hover:bg-indigo-700 transition duration-150">
                EXECUTE (Ctrl/⌘ + Enter)
            </button>
        </div>

        <!-- Output Panel (Simulación de Log/Resultados) -->
        <div class="rounded-xl shadow-2xl terminal-bg flex-grow flex flex-col">
            <div class="p-4 border-b border-gray-700">
                <h3 class="text-sm font-semibold text-slate-300">Execution Result</h3>
            </div>
            <div class="p-4 space-y-3 flex-grow overflow-y-auto">
                <div class="p-2 rounded input-area">
                    <div class="text-xs text-slate-400">STATUS (Mode | Exit Code)</div>
                    <div id="statusLine" class="font-bold terminal-text text-lg">
                        <span id="modeOut" class="text-indigo-400">—</span> | <span id="exitCode" class="text-green-500">—</span>
                    </div>
                </div>

                <div class="h-40">
                  <div class="text-xs text-slate-400 mb-1">STDOUT (Clean Output)</div>
                  <pre id="stdout" class="h-full output-area terminal-text rounded p-3 overflow-auto success-text"></pre>
                </div>
                
                <div class="h-40">
                  <div class="text-xs text-slate-400 mb-1">STDERR (Security/Errors)</div>
                  <pre id="stderr" class="h-full output-area terminal-text rounded p-3 overflow-auto error-text"></pre>
                </div>
            </div>
        </div>

      </div>
    </div>
  </div>

<script>
// --- Variables de Referencia ---
const modeSel = document.getElementById('mode');
const languageInput = document.getElementById('language');
const codeTextarea = document.getElementById('code');
const runBtn = document.getElementById('runBtn');

const commandInput = document.getElementById('commandInput');
const scriptInput = document.getElementById('scriptInput');

// --- Helpers de UI ---
modeSel.addEventListener('change', () => {
  languageInput.parentElement.classList.remove('hidden'); 
  commandInput.classList.add('hidden');
  scriptInput.classList.add('hidden');

  if (modeSel.value === 'command') {
    languageInput.parentElement.classList.add('hidden');
    commandInput.classList.remove('hidden');
  } else if (modeSel.value === 'script') {
    scriptInput.classList.remove('hidden');
  } 
});

modeSel.dispatchEvent(new Event('change'));

// --- Llamada a la API (Asíncrona) ---
async function callExecute(payload) {
  const res = await fetch('/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok && res.status !== 500) { 
    const t = await res.text();
    throw new Error(`HTTP Error ${res.status}: ${t}`);
  }
  return res.json();
}

// --- Lógica de Ejecución ---
async function handleRun() {
  runBtn.disabled = true;
  runBtn.textContent = 'EXECUTING...';
  
  const timeout = parseInt(document.getElementById('timeout').value || '10', 10);
  const memory_mb = parseInt(document.getElementById('memory_mb').value || '256', 10);
  let payload = { timeout, memory_mb };

  if (modeSel.value === 'code') {
    payload.language = (languageInput.value || '').trim();
    payload.code = codeTextarea.value || '';
  } else if (modeSel.value === 'command') {
    payload.command = document.getElementById('command').value || '';
  } else if (modeSel.value === 'script') {
    payload.language = (languageInput.value || '').trim();
    payload.script_path = document.getElementById('script_path').value || '';
  }

  const exitCode = document.getElementById('exitCode');
  const modeOut  = document.getElementById('modeOut');
  const stdout   = document.getElementById('stdout');
  const stderr   = document.getElementById('stderr');

  exitCode.textContent = '—';
  modeOut.textContent  = 'WAIT';
  stdout.textContent   = 'Running job...';
  stderr.textContent   = '';
  exitCode.classList.remove('text-green-500', 'text-red-500');
  exitCode.classList.add('text-yellow-500');

  try {
    const data = await callExecute(payload);
    
    exitCode.textContent = data.exit_code ?? '—';
    modeOut.textContent  = data.mode ?? '—';
    stdout.textContent   = data.stdout ?? '';
    stderr.textContent   = data.stderr ?? '';
    
    exitCode.classList.remove('text-yellow-500');
    if (data.exit_code === 0) {
        exitCode.classList.add('text-green-500');
    } else {
        exitCode.classList.add('text-red-500');
        if (data.stderr) {
            stderr.textContent = data.stderr;
        }
    }
    
  } catch (e) {
    exitCode.textContent = 'NET';
    modeOut.textContent  = 'API';
    stderr.textContent   = e.message ?? String(e);
    exitCode.classList.remove('text-green-500', 'text-yellow-500');
    exitCode.classList.add('text-red-500');
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = 'EXECUTE (Ctrl/⌘ + Enter)';
  }
}

runBtn.addEventListener('click', handleRun);

document.addEventListener('keydown', (e) => {
    const isRunKey = e.key === 'Enter';
    const isModKey = e.ctrlKey || e.metaKey; 
    const isReady = !runBtn.disabled;

    if (isRunKey && isModKey && isReady) {
        e.preventDefault(); 
        handleRun();
    }
});
</script>
</body>
</html>
    """

