Benchmarks — Code Executor

## Último Smoke Test (Offline, Gozo-Lite)

Ejecutado dentro de la imagen `code-executor-ubuntu:latest` con 30 lenguajes soportados.

### Comando utilizado

```bash
docker run --rm -it -p 8000:8000 \
  -v "${PWD}:/app" -w /app code-executor-ubuntu:latest \
  bash -lc "SMOKE_TIMEOUT=60 PYTHONPATH=/app python3 tests/offline_smoke.py"

Resultado

=== Summary ===
{
  "total": 30,
  "failures": 0
}

Lenguajes probados

✅ Python

✅ Node.js

✅ Bash

✅ C

✅ C++

✅ Java

✅ Go

✅ Rust

✅ SQL (SQLite)

✅ Ruby

✅ PHP

✅ R

✅ Lua

✅ Perl

✅ Tcl

✅ Awk

✅ Sed

✅ Make

✅ BC

✅ Kotlin

✅ Scala

✅ Haskell

✅ OCaml

✅ Dart

✅ Fortran

✅ Pascal

✅ Ada

✅ Cobol

✅ Zig

✅ Nim


Observaciones

Crystal fue eliminado del registro (no soportado actualmente).

Todos los lenguajes listados pasaron con éxito (ok = true).

Tiempo de ejecución configurado: 60s (SMOKE_TIMEOUT=60).



---

📌 Conclusión: el Code Executor pasó la prueba completa con 30 lenguajes funcionando, sin fallas.

---
