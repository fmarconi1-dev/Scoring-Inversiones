# Bitácora — /ui

## 2026-07-04 · Inicial (v0.1)
- **Qué:** `index.html` — tablero dark (skill ui-ux-web-moderno): KPIs, tabla ordenable con barras de score, chips de filtro (categoría + grupo), buscador, y modal de detalle por empresa con desglose fundamental/técnico.
- **Por qué:** entregar el tablero `.html` pedido, abrible con doble clic.
- **Decisiones:** tokens dark (#0F172A / #192134), verde/rojo siempre con ícono (check/x), cifras tabulares, íconos SVG (no emojis). Lee `data.js`.
- **Falta:** mini-gráfico de precio en el modal; export a CSV; responsive fino <375px.

## 2026-07-04 · Rediseño: múltiplos + señales visibles
- **Qué:** la tabla ahora muestra los múltiplos (P/E, P/B, ROE, D/E, Mg) coloreados por cumplimiento y las 5 señales técnicas (MM200, 50/200, RSI, MACD, OBV) como check/x, con el veredicto Triple Corona al final. El D/E financiero se muestra "N/A". El ticker linkea a Yahoo Finance (y botón "Ver en Yahoo Finance" en el modal).
- **Por qué:** Franco quería ver los datos crudos, no solo el puntaje; y poder saltar a la ficha de Yahoo.
- **Nota técnica:** OneDrive puede tardar en sincronizar; validar el HTML con el Read tool, no solo por el mount de bash.
