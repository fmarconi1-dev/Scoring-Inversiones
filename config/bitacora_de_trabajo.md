# Bitácora — /config

## 2026-07-04 · Inicial (v0.1)
- **Qué:** `config.json` con universo de 20 activos (10 US + 10 ARG/ADR) y umbrales fundamentales/técnicos + cortes de clasificación. `config_loader.py` con validación.
- **Por qué:** centralizar todos los parámetros para que la lógica no hardcodee nada y Franco pueda calibrar sin tocar código.
- **Decisiones:** Pampa se usa como ADR `PAM` (NYSE, USD), no `PAMP` (local en pesos), para mantener todo en USD.
- **Falta:** parámetros por sector (bancos), y flag para excluir métricas no aplicables.

## 2026-07-04 · Sectores sin D/E
- **Qué:** agregado `umbrales_fundamentales.sectores_deuda_equity_na = ["Financial Services"]`.
- **Por qué:** parametrizar qué sectores excluyen Deuda/Equity del score, sin hardcodear en la lógica.

## 2026-07-06 · Universo a 50 + rename
- Universo ampliado a 50 (agregadas 20: CEG, IONQ, AMD, MU, ASML, ARM, PLTR, CRWD, PANW, ORCL, NOW, MA, COIN, SOFI, NVO, ISRG, LMT, GEV, VST, BABA).
- "Triple Corona" renombrada a "Consagradas" (solo etiqueta visible; la clave interna sigue siendo triple_corona_madura para no romper el tracking).

## 2026-07-06 · Universo a 100
- Agregadas 50 (semis, software, farma, financieras, energía, defensa, consumo, China y más LatAm: GLOB, BMA, PAM, TGS, TX). Total 100, 11 ARG.
- Resultado: 4 Consagradas (JPM, QCOM, PAM, TGS), 10 Emergentes, 86 Otros.
