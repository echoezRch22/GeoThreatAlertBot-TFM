# GeoThreatAlertBot-TFM 🚀
### Desarrollo de una herramienta para la difusión automatizada de inteligencia de amenazas cibernéticas segmentada geográficamente mediante la integración de MISP y Telegram.

Este repositorio aloja el código fuente y las recetas de orquestación de la solución de software desarrollada como **Trabajo Fin de Máster (TFM)** para el **Máster Universitario en Ciberseguridad** de la **Universidad Internacional de La Rioja (UNIR)**.

---

## 📌 Descripción del Proyecto
El sistema resuelve de forma automatizada la problemática de la sobrecarga de información (*alert fatigue*) en los Centros de Operaciones de Seguridad (SOC). Mediante un orquestador modular en Python, la herramienta consume Indicadores de Compromiso (IoCs) atómicos (direcciones IP y dominios) desde una instancia federada de **MISP**, los enriquece geográficamente en tiempo casi real y difunde alertas contextualizadas hacia canales específicos de **Telegram** dirigidos a usuarios suscritos por país, aplicando un filtrado estricto basado en el protocolo de confidencialidad **TLP:WHITE**.

---

## 📁 Estructura del Repositorio
La arquitectura del software sigue un diseño modular y estructurado de la siguiente manera:

*   `src/` : Código fuente principal del sistema de orquestación.
    *   `main.py` : Orquestador principal del flujo operativo y listener periódico.
    *   `extractor.py` : Cliente de PyMISP encargado de la ingesta y control perimetral TLP.
    *   `geo_module.py` : Módulo de análisis geoespacial y validación cruzada.
    *   `telegram_bot.py` : Lógica operativa de los comandos e interfaz interactiva del bot.
    *   `database.py` : Gestor transaccional y persistencia CRUD (SQLite).
*   `data/` : Directorio local para almacenamiento de persistencia (Excluido en control de cambios de Git).
*   `Dockerfile` : Receta de aprovisionamiento y empaquetamiento del contenedor Python.
*   `docker-compose.yml` : Manifiesto de orquestación para el despliegue del stack completo (MISP, DB, Redis, Bot).
*   `template.env` : Archivo guía de variables de entorno requerido para inicializar el sistema.
*   `requirements.txt` : Declaración formal de librerías y dependencias del sistema.

---

## 🛠️ Requisitos e Instalación

### 1. Clonar el repositorio
```bash
git clone [https://github.com/echoezRch22/GeoThreatAlertBot-TFM.git](https://github.com/echoezRch22/GeoThreatAlertBot-TFM.git)
cd GeoThreatAlertBot-TFM