# Bitácora — /src

## 2026-07-04 · Inicial (v0.1)
- **Qué:** `technicals.py` (SMA, RSI Wilder, MACD, OBV) y `scoring.py` (score fundamental 0-100 ponderado, score técnico 0-100, clasificación en 4 categorías + Triple Corona).
- **Por qué:** separar cálculo puro (testeable, sin I/O) de la obtención de datos.
- **Decisiones:**
  - Score fundamental = interpolación lineal por métrica (excelente→1, aceptable→0.5) ponderada; se reescala por peso de métricas presentes para no castigar datos faltantes.
  - Score técnico = suma de 5 señales ponderadas; RSI sobreventa da puntaje parcial (oportunidad si hay calidad).
  - No se clasifica con < 3 métricas fundamentales presentes (config).
- **Falta:** tests unitarios formales; backtesting de las señales.

## 2026-07-04 · Ajuste sectorial D/E + yf en output
- **Qué:** `score_fundamental` ahora acepta `sector`; para sectores en `sectores_deuda_equity_na` (config) excluye Deuda/Equity y reparte su peso entre las 4 métricas restantes. La métrica se marca `na_sector` (se muestra N/A).
- **Por qué:** en bancos/financieras el D/E de la fuente no es significativo (depósitos ≠ deuda de apalancamiento) y penalizaba de más. Metodología documentada en investigacion_financiera.docx §4.1.
- **Falta:** métricas de solvencia propias de bancos (Tier 1/capital regulatorio) cuando haya fuente.

## 2026-07-04 · Fix P/E (métricas menor_mejor)
- **Bug:** en `_puntaje_metrica`, la rama `valor >= aceptable` reiniciaba el puntaje en 1.0 y bajaba lento → P/E 37 puntuaba 0.75 (verde) mientras P/E 23 daba 0.59 (naranja). Discontinuidad en el umbral.
- **Fix:** curva monótona y continua: 1.0 en excelente, 0.5 en aceptable, sigue bajando a 0 más allá con la misma pendiente. Ahora un P/E menor nunca puntúa peor que uno mayor.
- **Impacto:** AAPL (P/E 37) cae de Triple Corona a Técnico; KO (P/E 26,5) de Triple Corona a Técnico. Triple Corona pasó de 6 a 4.

## 2026-07-04 · Ajustes v0.3 (umbrales 70, valuación, saneo, cruce, cambios)
- Umbrales subidos a 70 (fund, téc, emergente) en config.
- Saneo de datos en provider: P/E, P/B, PEG, margen bruto no positivos o absurdos (BRK-B P/B=0,001) -> None. Agregado P/S.
- Emergente: métrica "valuacion" adaptativa (PEG si hay ganancias; si no, P/S÷crecimiento). Margen bruto excluido en sector financiero.
- Técnico: `dias_cruce` (antigüedad del cruce MM50/200 en ruedas) + tipo golden/death.
- build_snapshot: seguimiento de cambios de categoría entre corridas (data/estado_anterior.json + docs/historial_cambios.md + campo "cambio" y lista "cambios").
- Target price de consenso incorporado (columna Obj. + ficha).

## 2026-07-04 · Filtro anti-trampa (techo + recorrido) v0.4
- technicals: `max_precio`, `dist_ath`, `en_techo` (<=3% del máximo), `ruptura_confirmada` (nuevo máximo + OBV en su máximo).
- score_tecnico: castiga -penal_techo si está en techo SIN ruptura confirmada por volumen (distingue doble techo de rompimiento). Castiga -penal_sin_recorrido / -penal_poco_recorrido según el upside al target de analistas. Todo parametrizado en config.
- UI: señales "Techo" y "Recorrido" en la ficha + tag "⚠ techo" en la tabla.
- Efecto: JPM (99,8% de máximos, sin volumen, +3% al target) baja de téc 100 a 80.

## 2026-07-04 · Confirmación de ruptura por volumen (v0.4.1)
- Cambiada la regla de ruptura confirmada: antes exigía OBV en su máximo (muy estricto). Ahora: volumen del día >= 150% del promedio de las últimas 50 ruedas (config: ruptura_vol_factor=1.5, ruptura_vol_ventana=50). Se guarda `vol_ratio` y se muestra en el detalle de "Techo".

## 2026-07-04 · Mejoras v0.5
- Divergencia bajista de RSI: precio con máximo más alto y RSI con máximo más bajo → castigo `penal_divergencia` en el score técnico + señal en la ficha.
- ROA para bancos: en sector financiero el peso del D/E (excluido) va a ROA (`umbrales_fundamentales.roa`). JPM/NU mejoran; GGAL sigue bajo por ROA real bajo.
- Radar de nacientes: antigüedad en bolsa desde `history_metadata.firstTradeDate`; flag `recien_listada` (<3 años, config) + badge 🌱.
- Precio vs. su historia: historial extendido a 5 años; `precio_pct_rango` (percentil en el rango) y `precio_vs_media` (% vs promedio). Columna "Rango" en Maduras/Otros + sección en la ficha. Mega-caps hoy caras vs. su historia (KO 100%, JPM 99,7%).

## 2026-07-04 · Revert "precio vs su historia" (v0.5.1)
- Se removió la métrica precio-vs-historia (columna "Rango" + sección en ficha + cálculos en technicals) por ser NOMINAL: mezcla inflación y deriva de ganancias. Ver docs/mejoras_pendientes.md para la versión correcta (P/E histórico).
- Se mantienen: divergencia RSI, radar 🌱 (antigüedad), ROA en bancos, y el historial a 5 años (invisible, mejora el ATH del filtro de techo).
- En la ficha queda solo la línea de "Antigüedad en bolsa" (parte del radar).
