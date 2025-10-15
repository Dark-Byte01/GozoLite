# Security Policy — Code Executor

## Supported Versions

El proyecto **Code Executor** se encuentra en desarrollo activo.  
Actualmente la rama principal (`main`) y la imagen `code-executor-ubuntu:latest` reciben actualizaciones de seguridad.  

| Versión | Soportada |
|---------|-----------|
| latest  | ✅ |
| dev/*   | ⚠️ soporte limitado |
| legacy  | ❌ |

---

## Reportar Vulnerabilidades

Si descubrís una vulnerabilidad de seguridad en **Code Executor**:

1. **No abras un issue público.**  
   Los reportes de seguridad deben mantenerse privados hasta que se corrijan.

2. Contactanos directamente:  
   - 📧 Email: `security@code-executor.dev` (placeholder, reemplazar al publicar)  
   - 🔒 Alternativa: enviar reporte encriptado (PGP key disponible en `docs/pgp.asc`).  

3. Incluí:  
   - Descripción detallada del problema.  
   - Pasos para reproducir.  
   - Impacto estimado (ej: RCE, fuga de datos, bypass sandbox).  
   - Lenguaje/módulo afectado.  

---

## Alcance de Seguridad

El **Code Executor** corre código de terceros en entornos aislados (Gozo-Lite).  
Aun así, se aplican las siguientes protecciones:

- 🛡️ **Sandboxing**: cada ejecución ocurre en `/tmp/ce-*` con limpieza automática.  
- 🛡️ **Sin acceso a red** por defecto (se puede habilitar bajo whitelist).  
- 🛡️ **Límites de CPU/RAM/Tiempo** configurables por job.  
- 🛡️ **Contenedores efímeros (Docker)**: se crean y destruyen por ejecución.  
- 🛡️ **Validación de entradas**: tamaño máximo de código y sanitización.  

---

## Responsabilidad del Usuario

El equipo de **Code Executor** no se hace responsable por:  

- Daños derivados de ejecutar código malicioso cargado por el usuario.  
- Uso en producción sin configuraciones de seguridad adicionales.  
- Integraciones externas que alteren la política de aislamiento.  

---

## Divulgación Responsable

- Se solicita un **plazo de embargo de 30 días** antes de publicar un exploit.  
- Reconocemos públicamente a los investigadores que reporten vulnerabilidades críticas (hall of fame en `docs/SECURITY_ACKS.md`).  

---

✍️ **Última actualización:** Octubre 2025
