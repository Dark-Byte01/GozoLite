# PRICE_INITIAL.md — Valoración inicial (GozoLite)

## Tesis de valor
GozoLite es una **infraestructura de ejecución multi-lenguaje** lista para integrar (API FastAPI, orquestador Python, runtime Docker con ~30 lenguajes).  
Su propuesta combina **portabilidad**, **seguridad razonable** y **automatización** (smoke tests, warm-ups).

## Comparables (alto nivel)
- **Judge0 (open-source)**: plataforma robusta y gratuita con 60+ lenguajes y API; usada como *baseline* por el mercado. Competís por **feature-set**, **hardening**, **SLA** y **integración enterprise** (no por costo de licencia).
- **Sphere Engine (SaaS)**: licencias anuales de **miles de USD/año** por módulos de compilación/ejecución gestionada.
- **GitHub Codespaces**: referencia de costo por hora de entornos aislados y escalables, útil para *benchmark* de TCO al compararte contra construir-vs-comprar.

## Metodologías de valuación combinadas
1. **Costo de replicación (Replacement Cost)**: estimá meses-persona para igualar:
   - Orquestador multi-lenguaje (`LangSpec` + runners) + runtime Docker endurecido
   - API, health, colas, smoke tests, documentación y tooling
   - Seguridad, observabilidad, SBOM, CI/CD
2. **Valor estratégico (Option Value)**: capacidad de vender como **componente** a EdTech/HRTech/IDE web/Cloud orgs o integrarlo en plataformas AI.
3. **Descuento por brechas**: restar % por cada gap enterprise (seguridad, SSO, auditoría, métricas, límites, split de imágenes, SLA).

## Rango propuesto por el autor
- **Precio listado:** USD 15M
- **Rango de negociación objetivo:** USD 12M
- **Mínimo aceptable:** USD 8M

## Juicio profesional (esta versión MVP)
- **Conclusión:** El **rango es agresivo** para un **MVP**, pero defendible.  
  Para justificar **USD 8–12M** ante compradores como Big Tech, recomendación: cerrar **bloque de seguridad + observabilidad + multi-imagen** y entregar **demo reproducible** con pruebas de carga.
- **Posición sugerida:** Anclar en **USD 12–15M** *condicionado* a un **Roadmap de 4–6 semanas** con entregables verificables.  
  Sin ese bloque cerrado, la valoración realista se ubica entre **USD 2–6M** (asset/tech-acq) dependiendo del interés estratégico del comprador.

## Entregables que disparan valor
- **Seguridad**: seccomp/AppArmor, caps, read-only, pids/mem/cpu, no-new-privileges, política por lenguaje y por job.
- **Observabilidad**: Prometheus + OpenTelemetry + auditoría por job + retención controlada.
- **Enterprise**: SSO (OIDC/SAML), roles, cuotas por org/usuario, rate-limits, metering/billing.
- **Infra**: imágenes por lenguaje, autoscaling por cola, backpressure, límites por job.
- **Confiabilidad**: suite de carga (p99), caos mínimo (kill -STOP/CONT), reintentos idempotentes, SLIs/SLOs.

## Narrativa para compradores
- **Riesgo técnico bajo**: arquitectura clara y portable (Docker + Python).
- **Tiempo-a-valor corto**: *drop-in* API y runners listos.
- **Cost Avoidance**: evitar 6–12 meses de ingeniería interna para llegar al mismo punto con seguridad y observabilidad.

## Recomendación de lista
Mantener **USD 15M** como *anchor*, ofrecer **descuento por cierre** tras cumplir el **milestone enterprise** (4–6 semanas).  
Mínimo negociable **USD 8M** solo si existe urgencia y *tech-acq* estratégica.