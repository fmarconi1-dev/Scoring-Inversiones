# Bitácora — /config

## 2026-07-04 · Inicial (v0.1)
- **Qué:** `config.json` con universo de 20 activos (10 US + 10 ARG/ADR) y umbrales fundamentales/técnicos + cortes de clasificación. `config_loader.py` con validación.
- **Por qué:** centralizar todos los parámetros para que la lógica no hardcodee nada y Franco pueda calibrar sin tocar código.
- **Decisiones:** Pampa se usa como ADR `PAM` (NYSE, USD), no `PAMP` (local en pesos), para mantener todo en USD.
- **Falta:** parámetros por sector (bancos), y flag para excluir métricas no aplicables.

## 2026-07-04 · Sectores sin D/E
- **Qué:** agregado `umbrales_fundamentales.sectores_deuda_equity_na = ["Financial Services"]`.
- **Por qué:** parametrizar qué sectores excluyen Deuda/Equity del score, sin hardcodear en la lógica.
