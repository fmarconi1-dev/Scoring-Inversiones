# Instrucciones de sistema — Tablero de Scoring de Acciones

Este archivo dicta cómo trabajar en este proyecto en futuras sesiones.

## Antes de codificar
1. Leé la `bitacora_de_trabajo.md` de la carpeta que vas a tocar.
2. Revisá el `README.md` de la raíz para el estado global y las decisiones tomadas.
3. No asumas: si una decisión de arquitectura no está registrada, preguntá.

## Reglas de código
- **Modularidad estricta:** `/config` (parámetros), `/data` (APIs/caché), `/src` (lógica), `/ui` (vista), `/docs`. No mezclar responsabilidades entre carpetas.
- **No sobrescribir código funcional sin permiso explícito de Franco.** Si algo anda, se extiende, no se reemplaza.
- **Manejo de errores obligatorio en toda conexión a API:** try/except, timeout, reintentos con backoff, y fallback a caché. El tablero nunca debe romperse por una llamada de red.
- **Umbrales y universo viven en `config/config.json`**, nunca hardcodeados en la lógica.
- **Nunca clasificar una empresa con datos incompletos:** marcar `None`/`s/d` (mínimo de métricas en config).
- El único proceso que toca la red es `data/build_snapshot.py`. El tablero (`ui/`) solo lee datos.

## Después de cada cambio sustancial
1. Actualizá la `bitacora_de_trabajo.md` del módulo (qué, por qué, qué falta) con fecha.
2. Proponé a Franco la versión nueva del `README.md` de la raíz.

## Estilo de interacción
- Respuestas concisas y directas (preferencia de Franco).
- UI: aplicar la skill `ui-ux-web-moderno` (dark, tablas responsivas, verde/rojo con signo/ícono, modales, cifras tabulares).
- Preferir datos reales verificados sobre supuestos.
