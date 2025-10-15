Code Executor — Arquitectura

## Visión General
Code Executor es un sistema modular de ejecución de código diseñado para soportar múltiples lenguajes de programación de forma aislada, segura y eficiente.

La arquitectura está pensada para ser **escalable**, **portable** y fácil de integrar en pipelines o entornos educativos/empresariales.

---

## Componentes

1. **API Layer (FastAPI + Uvicorn)**
   - Expone los endpoints REST para enviar código, definir lenguaje y recibir resultados.
   - Comunicación JSON estándar.

2. **Orchestrator (Gozo Lite)**
   - Determina cómo ejecutar cada request.
   - Selecciona el runner apropiado según el lenguaje.
   - Maneja timeouts y memoria límite.

3. **Runners**
   - Cada lenguaje se ejecuta en su propio entorno aislado.
   - Uso de intérpretes/compiladores nativos (`python3`, `node`, `g++`, `go`, etc).
   - Salida estándar y errores capturados.

4. **Sandbox**
   - Directorios temporales (`/tmp/ce-*`).
   - Limpieza automática tras cada job.
   - Sin acceso a red por defecto.

5. **UI mínima**
   - Interfaz simple para probar el sistema vía navegador.
   - Permite seleccionar lenguaje, escribir código y visualizar resultado.

---

## Flujo de Ejecución
1. El usuario envía código + lenguaje vía API/UI.
2. El orquestador recibe el request y crea un directorio temporal.
3. Se guarda el código en un archivo con sufijo correspondiente (`.py`, `.cpp`, `.rs`, etc).
4. Se compila o ejecuta según corresponda.
5. Se retorna un JSON estándar:
   ```json
   {
     "ok": true,
     "exit_code": 0,
     "stdout": "hello world",
     "stderr": "",
     "time_ms": 32,
     "mode": "gozo-lite",
     "language": "python"
   }


---

Ventajas Clave

Modularidad: agregar lenguajes es sencillo.

Seguridad: procesos aislados, límites de tiempo y memoria.

Escalabilidad: puede crecer hacia contenedores/MicroVMs.


---
