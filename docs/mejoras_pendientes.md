# Mejoras pendientes — backlog del tablero

Ideas evaluadas y postergadas, para retomar en orden de prioridad.

## 1. P/E histórico (bien hecho) — PRIORIDAD ALTA
**Qué:** comparar el P/E (y P/S) actual de cada empresa contra su **propio promedio/percentil de 5 años**, en lugar del "precio vs. su historia" que se removió.

**Por qué:** el "precio vs. su historia" usaba precios **nominales**, así que mezclaba dos distorsiones: la inflación del período y la deriva estructural del equity (crecimiento de ganancias + premio por riesgo). Un múltiplo es un **ratio** (precio ÷ ganancias): se neutraliza solo tanto la inflación como el crecimiento de ganancias. Por eso el P/E-vs-su-media es la métrica teóricamente correcta para decir si una acción está cara o barata respecto de su propia norma. Para EE.UU. la inflación es de segundo orden, pero la deriva de ganancias no, y el múltiplo la resuelve.

**Cómo (implementación):**
- Traer el historial de ganancias: `yf.Ticker(t).income_stmt` / `quarterly_income_stmt` (Net Income) y acciones en circulación para EPS, o `quarterly_financials`.
- Construir EPS TTM por fecha (suma móvil de 4 trimestres).
- Serie de P/E = precio_histórico ÷ EPS_TTM(fecha). Idem P/S con ingresos TTM.
- Métrica: P/E actual vs. su media y percentil de 5 años (barata = por debajo de su media).
- Mostrar como columna en Maduras/Otros (reemplaza la vieja "Rango") y en la ficha.

**Riesgos:** yfinance suele tener huecos en históricos de estados contables; hace falta fallback y validación. Para empresas sin ganancias, usar P/S histórico.

**Opción intermedia (si se quiere algo rápido):** deflactar la serie de precios por CPI de EE.UU. → precio real. Arregla la inflación pero NO la deriva de ganancias; es media solución.

## 2. Otras mejoras conocidas
- **Radar de nacientes:** distinguir el tipo de evento (spinoff vs IPO vs carve-out), hoy solo se marca "reciente" por antigüedad (<3 años).
- **Trayectoria del margen bruto:** medir si se expande o se erosiona (requiere series trimestrales), no solo el nivel actual.
- **Solvencia bancaria fina:** Tier 1 / capital regulatorio si aparece una fuente gratuita; hoy usamos ROA como proxy.
- **Ponderar en el score:** una vez hecho el P/E-vs-historia, decidir si suma puntos al fundamental (mega-cap barata vs. su norma) o queda solo como contexto.
