# Bitácora — /data

## 2026-07-04 · Inicial (v0.1)
- **Qué:** `provider.py` (DataProvider yfinance con caché e historia) y `build_snapshot.py` (batch EOD que genera `ui/data.json` + `ui/data.js`).
- **Por qué:** aislar toda la I/O de red en un solo lugar; el scoring y la UI nunca llaman a yfinance directo.
- **Decisiones:**
  - Caché en **CSV** (no parquet) para no depender de pyarrow/fastparquet — portable sin instalar nada extra.
  - Cache válida por el día (EOD). Ante fallo de red, se usa caché vieja como fallback y se avisa por consola.
  - `debtToEquity` de yfinance viene en % (150 = 1.5x); se normaliza dividiendo por 100.
  - Se emite `data.js` (`window.SCORING_DATA=...`) además del JSON, para que el HTML abra con doble clic sin servidor (evita CORS de file://).
- **Falta:** bancos traen Deuda/Equity poco significativo; considerar excluir por sector.

## 2026-07-04 · 5 años + metadatos
- Historial extendido a 5y (mejor ATH y contexto). Cache renombrado a `{ticker}_hist5y.csv` (el rm no puede borrar en el mount de OneDrive).
- `anios_cotizando()` lee `{ticker}_meta.json` (firstTradeDate capturado en el fetch). Agregado ROA a fundamentals.
