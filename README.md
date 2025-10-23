# GozoLite — Modular Code Executor

**Autor:** Facundo Scandroli  
**Versión:** 1.0  
**Licencia:** Custom License v2 — *actualización bajo control del autor*  
**Estado:** MVP funcional y estable  

---

## 🧠 Qué es GozoLite

GozoLite es un **Code Executor modular, seguro y multiplataforma** capaz de ejecutar **código real en 29 lenguajes** dentro de entornos aislados y temporales.  
Nació como una base sólida para que empresas, instituciones educativas o equipos técnicos puedan correr código sin depender de terceros ni comprometer la seguridad del sistema.

Su enfoque no es ser una simple *sandbox*, sino una **infraestructura lista para integrar**:  
compacta, reproducible, portable y construida con un núcleo en Python que orquesta compiladores, intérpretes y entornos en contenedores Docker endurecidos.

---

## 🚀 Propósito

GozoLite busca resolver un problema común en la educación y la industria:  
**tener un entorno unificado, limpio y controlado para ejecutar código de cualquier lenguaje** sin tener que montar servidores separados o instalar toolchains manualmente.

Está pensado como una **base vendible y adaptable**, lista para integrarse en:

- Plataformas de enseñanza (como un backend de ejecución).  
- Sistemas de evaluación automática.  
- Laboratorios de programación virtuales.  
- Proyectos corporativos que requieran entornos aislados de ejecución.  

---

## 🧩 Características principales

- **Compatibilidad real con 29 lenguajes** modernos, legacy y de propósito mixto.  
- **Aislamiento total** por contenedor, sin acceso al host.  
- **Seguridad reforzada** (usuario sin privilegios, FS de solo lectura, `seccomp`, `cap_drop`, límites de memoria y CPU).  
- **Sistema modular:** agregar o quitar lenguajes sin modificar el núcleo.  
- **Imagen preconstruida (`.tar`)** lista para uso inmediato.  
- **Salida uniforme:** `ok`, `stdout`, `stderr`, `exit_code`, `time_ms`, `language`.  

> Cada ejecución vive y muere en segundos.  
> Sin basura, sin rastro, sin comprometer estabilidad.

---

## ⚙️ Visión

GozoLite fue diseñado como un **esqueleto profesional**, no como un producto cerrado.  
Su filosofía es simple: entregar una base robusta que otros puedan ampliar, mejorar o conectar a sus propios sistemas, **manteniendo transparencia y control**.

No busca reemplazar a plataformas como *Judge0* o *Replit*, sino ofrecer una **versión profesional, modular y portable** de lo que esas herramientas hacen, con una arquitectura más abierta y preparada para evolución corporativa.

---

## 🔒 Licencia — Custom License v2

Esta licencia permite a terceros **modificar, adaptar o mejorar el proyecto**,  
siempre bajo las siguientes condiciones:

1. Toda modificación debe ser **notificada al autor original** (Facundo Scandroli).  
2. Las actualizaciones que afecten la base del sistema deben **describirse o compartirse** (salvo las implementaciones privadas internas).  
3. Se prohíbe redistribuir o revender el proyecto sin autorización.  
4. El autor mantiene el **control total** sobre la base mientras el proyecto siga siendo de su propiedad.  
5. En caso de cesión o venta, la licencia y los derechos de actualización se transfieren formalmente.  

> “Mientras GozoLite sea mío, toda mejora tiene que ser visible.  
> Se puede escalar, pero no esconder.”  
> — *Facundo Scandroli*

---

## 📦 Estado actual

✅ Imagen funcional (`gozolite_image.tar`)  

✅ 29 lenguajes integrados  

✅ Sistema seguro y portable  

✅ Licencia v2 aplicada  

✅ Preparado para evaluación e integración  

---

## 💬 Contacto

**Facundo Scandroli**  
Autor y mantenedor de GozoLite    
📧 scandrolifacundo2012@gmail.com  

---

> **GozoLite es la base de un nuevo estándar:**  
> *una ejecución segura, transparente y universal del código.*
