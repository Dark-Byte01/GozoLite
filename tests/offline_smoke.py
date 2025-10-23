#!/usr/bin/env python3
# offline_smoke.py — Prueba offline de ~30 lenguajes vía MainApp.submit()

from __future__ import annotations
import os, sys, json, importlib, types, time

# ---------------------------
# 0) Descontaminación temprana
# ---------------------------
def _contains_llm_models(p: str) -> bool:
    if not p:
        return False
    pl = p.replace("\\", "/").lower()
    return ("llm_models" in pl) or ("llm models" in pl)

raw_pp = os.environ.get("PYTHONPATH")
if raw_pp:
    parts = [x for x in raw_pp.split(os.pathsep) if not _contains_llm_models(x)]
    if parts:
        os.environ["PYTHONPATH"] = os.pathsep.join(parts)
    else:
        os.environ.pop("PYTHONPATH", None)

sys.path[:] = [p for p in sys.path if not _contains_llm_models(p)]

# ---------------------------
# 1) SHIM de llm_models
# ---------------------------
class _MemoryShim:
    def __init__(self, max_events: int = 20):
        self._ev = []
        self.max_events = max_events
    def add(self, role: str, content: str):
        self._ev.append({"role": role, "content": content})
        if len(self._ev) > self.max_events:
            self._ev = self._ev[-self.max_events:]
    def get_context(self):
        return list(self._ev)

def _get_memory_shim(*a, **k): return _MemoryShim()

llm_mod = types.ModuleType("llm_models")
llm_mod.get_memory = _get_memory_shim
llm_mod.Memory = _MemoryShim
llm_mem = types.ModuleType("llm_models.memory")
llm_mem.get_memory = _get_memory_shim
llm_mem.Memory = _MemoryShim

sys.modules["llm_models"] = llm_mod
sys.modules["llm_models.memory"] = llm_mem

# ---------------------------
# 2) Importar MainApp
# ---------------------------
try:
    from main import MainApp
except Exception as e:
    print(json.dumps({"fatal": f"No pude importar main.MainApp: {e}"}))
    sys.exit(2)

# ---------------------------
# 3) Config y Snippets
# ---------------------------
TIMEOUT = int(os.getenv("SMOKE_TIMEOUT", "10"))
MEMMB   = int(os.getenv("SMOKE_MEM_MB", "256"))

# Permitir elegir subconjunto de lenguajes
only_langs = set()
env_langs = os.getenv("SMOKE_LANGS", "").strip()
if env_langs:
    only_langs = {x.strip().lower() for x in env_langs.split(",") if x.strip()}

skip_langs = set()
env_skip = os.getenv("SMOKE_SKIP", "").strip()
if env_skip:
    skip_langs = {x.strip().lower() for x in env_skip.split(",") if x.strip()}

SNIPPETS = {
    "python":  'print("hello python")',
    "node":    'console.log("hello node")',
    "bash":    'echo "hello bash"',
    "c":       '#include <stdio.h>\nint main(){ puts("hello c"); return 0; }',
    "cpp":     '#include <iostream>\nint main(){ std::cout<<"hello cpp\\n"; return 0; }',
    "java":    'public class Main{ public static void main(String[]a){ System.out.println("hello java"); }}',
    "go":      'package main\nimport "fmt"\nfunc main(){ fmt.Println("hello go") }',
    "rust":    'fn main(){ println!("hello rust"); }',
    "sql":     'select "hello sql";',
    "ruby":    'puts "hello ruby"',
    "php":     '<?php echo "hello php\\n"; ?>',
    "r":       'cat("hello R\\n")',
    "lua":     'print("hello lua")',
    "perl":    'print "hello perl\\n";',
    "tcl":     'puts "hello tcl"',
    "awk":     '{print "hello awk"}',
    "sed":     's/.*/hello sed/',
    "make":    '.PHONY: all\nall:\n\t@echo hello make',
    "bc":      '2+2',
    "kotlin":  'fun main(){ println("hello kotlin") }',
    "scala":   'object Main extends App { println("hello scala") }',
    "haskell": 'main = putStrLn "hello haskell"',
    "ocaml":   'print_endline "hello ocaml";;',
    "dart":    'void main(){ print("hello dart"); }',
    "fortran": 'program hello\nprint *, "hello fortran"\nend program hello',
    "pascal":  "program Hello; begin writeln('hello pascal'); end.",
    "ada":     'with Ada.Text_IO; use Ada.Text_IO; procedure Hello is begin Put_Line("hello ada"); end Hello;',
    "cobol":   '       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n       PROCEDURE DIVISION.\n           DISPLAY "hello cobol".\n           STOP RUN.',
    "zig":     'pub fn main() void { @import("std").debug.print("hello zig\\n", .{}); }',
    "nim":     'echo "hello nim"',
}

# Algunos toolchains escriben warnings a stderr aun con exit 0; no fallar por eso
NOISY_OK = {"bc", "zig", "nim", "cobol", "ada", "pascal", "make"}

# ---------------------------
# 4) Runner
# ---------------------------
def run_all() -> int:
    app = MainApp()

    languages = list(SNIPPETS.keys())
    if only_langs:
        languages = [l for l in languages if l in only_langs]
    if skip_langs:
        languages = [l for l in languages if l not in skip_langs]

    failures = 0
    per_lang = []
    t0_total = time.time()

    for lang in languages:
        code = SNIPPETS[lang]
        payload = {"language": lang, "code": code, "timeout": TIMEOUT, "memory_mb": MEMMB}
        t0 = time.time()
        try:
            res = app.submit(**payload)
            ok = bool(res.get("ok", (res.get("exit_code", 1) == 0)))
            exit_code = int(res.get("exit_code", 0 if ok else 1))
            stdout, stderr = str(res.get("stdout", "")), str(res.get("stderr", ""))
            mode = str(res.get("mode", "dev"))
            # Si exit_code==0, considerar OK, incluso si hay ruido en stderr para toolchains conocidos
            if exit_code == 0:
                ok = True
        except Exception as e:
            ok, exit_code, stdout, stderr, mode = False, 1, "", f"[exception] {e}", "dev"

        elapsed_ms = int((time.time() - t0) * 1000)
        # Ajuste de ruido aceptable
        if not ok and exit_code == 0 and lang in NOISY_OK:
            ok = True

        status = "OK" if ok else "FAIL"
        print(f"\n=== [{lang}] {status} exit={exit_code} mode={mode} time_ms={elapsed_ms}")
        if stdout.strip():
            print("--- stdout ---\n" + stdout.strip())
        if (not ok) or stderr.strip():
            print("--- stderr ---\n" + stderr.strip())
        if not ok:
            failures += 1

        per_lang.append({"lang": lang, "ok": ok, "exit_code": exit_code, "time_ms": elapsed_ms})

    total_ms = int((time.time() - t0_total) * 1000)
    summary = {
        "total": len(languages),
        "failures": failures,
        "time_ms_total": total_ms,
        "langs": per_lang,
    }
    print("\n=== Summary ===")
    print(json.dumps(summary, indent=2))
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    sys.exit(run_all())