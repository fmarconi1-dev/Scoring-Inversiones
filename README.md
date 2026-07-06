# Tablero de Scoring · Fundamental + Técnico

Tablero web para monitorear acciones de EE.UU., el panel líder argentino (vía ADRs) y empresas globales, clasificándolas en tres categorías:

- **Atractivas por Fundamentales** — value investing estilo Buffett (múltiplos: P/E, P/B, ROE, Deuda/Equity, márgenes).
- **Atractivas por Técnico** — 5 indicadores combinados (MM200, cruce MM50/200, RSI, MACD, OBV).
- **Triple Corona** — cumplen ambas condiciones a la vez.

## Cómo se usa

1. **Generar/actualizar datos (batch EOD):**
   ```bash
   pip install -r requirements.txt
   python data/build_snapshot.py
   ```
   Esto recorre el universo, calcula los scores y escribe `ui/data.json` + `ui/data.js`.

2. **Ver el tablero:** abrí `ui/index.html` con doble clic (no requiere servidor). El HTML lee `data.js`.

## Arquitectura

`Python (batch EOD) → data.json/data.js → tablero HTML estático`. El único proceso que toca la red es el batch; el tablero solo lee datos. Fuente: **yfinance** (gratis, sin API key). ADRs argentinos en USD.

```
scoring-acciones/
├── config/   → universo de tickers + umbrales (config.json). Nada hardcodeado.
├── data/     → DataProvider (yfinance + caché CSV) y build_snapshot.py
├── src/      → technicals.py (indicadores) + scoring.py (scores y clasificación)
├── ui/       → index.html (tablero dark) + data.json/data.js (generados)
├── docs/     → investigacion_financiera.docx + análisis
├── config.json, claude.md, README.md, requirements.txt
```

Cada módulo tiene su `bitacora_de_trabajo.md`.

## Umbrales (editables en `config/config.json`)

| Fundamental | Excelente | Aceptable | | Técnico (aporta al score) |
|---|---|---|---|---|
| P/E | < 15 | < 25 | | Precio > MM200 · 30 pts |
| P/B | < 1,5 | < 3 | | MM50 > MM200 · 20 pts |
| ROE | > 20% | > 15% | | RSI(14) sano 40–65 · 20 pts |
| Deuda/Equity | < 0,5 | < 1 | | MACD > señal · 15 pts |
| Margen neto | > 20% | > 10% | | OBV en alza · 15 pts |

Clasificación: Fundamental ≥ 60 y/o Técnico ≥ 60. Triple Corona = ambos. Nunca se clasifica una empresa con menos de 3 métricas fundamentales disponibles.

## Automatización (GitHub Actions + Pages)

El repo incluye `.github/workflows/actualizar-tablero.yml`, que corre **en la nube de GitHub** (no depende de tu PC ni de Claude):

- **Cuándo:** de lunes a viernes a las 22:00 UTC (después del cierre del mercado US), y también manualmente desde la pestaña *Actions* (*Run workflow*).
- **Qué hace:** instala dependencias, corre `data/build_snapshot.py`, commitea `ui/data.json` y `ui/data.js` si cambiaron, y **publica el tablero en GitHub Pages**.
- **URL del tablero:** una vez activado, queda en `https://fmarconi1-dev.github.io/Scoring-Inversiones/`.

**Activación (una sola vez):**

1. Commiteá y pusheá el proyecto a `main`.
2. En GitHub: *Settings → Pages → Build and deployment → Source: **GitHub Actions***.
3. En *Settings → Actions → General → Workflow permissions*: dejá *Read and write permissions*.
4. Corré el workflow una vez a mano (*Actions → Actualizar tablero → Run workflow*) para publicarlo ya.

No requiere API keys ni secretos: yfinance es de acceso público.

## Estado (v0.1.0)

- [x] Estructura modular + gestión (README, claude.md, bitácoras)
- [x] Config de universo (20 activos) y umbrales
- [x] DataProvider yfinance + caché CSV + manejo de errores
- [x] Scoring fundamental + técnico + clasificación
- [x] Tablero HTML dark con KPIs, tabla, filtros y modal de detalle
- [x] docs/investigacion_financiera.docx
- [x] Tratamiento sectorial del D/E (bancos: se excluye y reponderan las demás)
- [x] Tablero muestra múltiplos + señales técnicas + link a Yahoo Finance
- [x] Automatizar el batch EOD (GitHub Actions, cron 22:00 UTC hábiles)
- [x] Publicar el tablero (GitHub Pages)
- [ ] Automatizar el batch EOD (tarea programada)
- [ ] Escalar el universo

## Limitaciones conocidas

- En bancos/financieras el Deuda/Equity de yfinance no es significativo → se **excluye** del score y se muestra N/A (ver `docs/investigacion_financiera.docx` §4.1). Falta incorporar métricas de solvencia propias (Tier 1).
- Algunos ADRs traen métricas incompletas; esas empresas quedan marcadas "s/d", no se fuerza clasificación.
- No es recomendación de inversión.
