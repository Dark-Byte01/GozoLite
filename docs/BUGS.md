# BUGS.md — Hallazgos técnicos (GozoLite)

## Resumen ejecutivo
Estado general **MVP sólido**, con buen **orquestador multi-lenguaje** y pruebas *offline smoke* bien pensadas.  
Sin embargo, para **venta enterprise** hay brechas duras en **aislamiento, observabilidad, límites de recursos y hardening** a nivel `docker-compose`.  
La **imagen monolítica** crece mucho y encarece tiempos de CI/CD.

## Prioridad CRÍTICA (antes de demos con compradores)
- **Aislamiento y límites por contenedor:**
  - Definir en `docker-compose.yml`: `security_opt` (`no-new-privileges:true`, `seccomp`), `cap_drop: ["ALL"]` + `cap_add` mínimos por lenguaje.
  - Aplicar `read_only: true`, `tmpfs` para `/tmp` y `/run`, `pids_limit`, `mem_limit`, `cpus`, `ulimits` (`nofile`, `nproc`, `fsize`).
  - Colas con **backpressure** (RQ/Redis ya está; añadir *timeouts* y *retries* por job).

- **Split de runtime:**
  - Evitar una sola **imagen monolítica**. Publicar **imágenes por lenguaje** o por *familia* (JVM, compiled, scripting) con etiquetas (`golang:ce`, `jvm:ce`, `script:ce`), reduciendo superficie y CVEs.

- **Observabilidad enterprise:**
  - Métricas Prometheus (tiempos, exit codes, uso por lenguaje), trazas OpenTelemetry, logs estructurados por *job_id*.
  - Auditoría por request: quién ejecutó, cuándo, qué lenguaje, consumo y resultado.

## Prioridad ALTA
- **Actualizaciones de framework:**
  - Migrar a **FastAPI + Uvicorn** recientes y **Pydantic v2** (o justificar pin por estabilidad).
- **Política de retención:**
  - Revisión del volumen `runner-home:/home/runner` para que las ejecuciones no persistan artefactos sensibles entre jobs.
- **SBOM + CVE Scanning:**
  - Generar SBOM (Syft) y escanear con Grype/Trivy en CI; reporte adjunto al *release*.

## Prioridad MEDIA
- **Warm-ups configurables:** permitir desactivar *warm-ups* en build para reducir tiempo y tamaño.
- **Compatibilidad Windows/macOS:** documentar *paths* y shells alternativos (pwsh).

## Señales POSITIVAS
- Orquestador `GozoLite` bien diseñado, con `LangSpec` por lenguaje y `stdin` soportado.
- `tests/offline_smoke.py` cubre una matriz amplia de lenguajes.
- Usuario no-root (`runner`) y salud básica con `/health`.

## Checklist de hardening mínimo
- `read_only: true` + `tmpfs` (/tmp, /run)
- `cap_drop: ["ALL"]` + `cap_add` por lenguaje solo si hace falta
- `no-new-privileges:true`
- `security_opt: ["seccomp=security/seccomp-min.json"]` (o default endurecido)
- `pids_limit`, `mem_limit`, `cpus`, `ulimits`
- *Job* por contenedor/namespace o *pool* por familia de lenguajes