"""Batch EOD: recorre el universo, calcula scores y escribe ui/data.json.
Este es el unico proceso que toca la red. El tablero solo lee el JSON."""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config.config_loader import cargar_config            # noqa: E402
from data.provider import obtener_historia, obtener_fundamentals  # noqa: E402
from src.technicals import calcular_indicadores            # noqa: E402
from src.scoring import score_fundamental, score_tecnico, score_emergente, clasificar  # noqa: E402

SALIDA = RAIZ / "ui" / "data.json"


def procesar_ticker(item: dict, cfg: dict) -> dict:
    yf_sym = item["yf"]
    fund = obtener_fundamentals(yf_sym)
    hist = obtener_historia(yf_sym)
    tec_ind = calcular_indicadores(hist, cfg["umbrales_tecnicos"])

    sf = score_fundamental(fund, cfg, sector=fund.get("sector"))
    st = score_tecnico(tec_ind, cfg, target_mean=fund.get("target_mean"),
                       precio=tec_ind.get("precio") or fund.get("precio_actual"))
    se = score_emergente(fund, cfg, tec_ind)
    clase = clasificar(sf, st, cfg, se)

    return {
        "ticker": item["ticker"],
        "yf": yf_sym,
        "nombre": item["nombre"],
        "grupo": item["grupo"],
        "sector": fund.get("sector"),
        "precio": tec_ind.get("precio"),
        "fundamentales": fund,
        "score_fundamental": sf["score"],
        "score_tecnico": st["score"],
        "score_emergente": se["score"],
        "metricas_fund_presentes": sf["metricas_presentes"],
        "categoria": clase["categoria"],
        "sub_veredicto": clase["sub_veredicto"],
        "riesgo_liquidez": se.get("riesgo_liquidez", False),
        "runway": se.get("runway"),
        "detalle_fundamental": sf["detalle"],
        "detalle_tecnico": st["detalle"],
        "detalle_emergente": se["detalle"],
        "tecnicos_raw": tec_ind,
        "target": {
            "mean": fund.get("target_mean"), "high": fund.get("target_high"),
            "low": fund.get("target_low"), "actual": fund.get("precio_actual") or tec_ind.get("precio"),
            "n": fund.get("n_analistas"),
        },
    }


def main():
    cfg = cargar_config()
    universo = cfg["universo"]
    print(f"Procesando {len(universo)} tickers...")
    filas = []
    for i, item in enumerate(universo, 1):
        print(f"[{i}/{len(universo)}] {item['ticker']}...", flush=True)
        try:
            filas.append(procesar_ticker(item, cfg))
        except Exception as e:  # noqa: BLE001
            print(f"  [ERROR] {item['ticker']}: {e}")
            filas.append({"ticker": item["ticker"], "nombre": item["nombre"],
                          "grupo": item["grupo"], "categoria": "error", "error": str(e)})

    # --- Seguimiento de cambios de categoria entre corridas ---
    estado_path = RAIZ / "data" / "estado_anterior.json"
    prev = {}
    if estado_path.exists():
        try:
            prev = json.loads(estado_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    cambios = []
    for f in filas:
        pc = prev.get(f["ticker"])
        if pc and pc != f["categoria"]:
            f["cambio"] = {"desde": pc, "hacia": f["categoria"]}
            cambios.append({"ticker": f["ticker"], "desde": pc, "hacia": f["categoria"]})
    # guardar estado actual para la proxima corrida
    estado_path.write_text(json.dumps({f["ticker"]: f["categoria"] for f in filas},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    # historial acumulado
    if cambios:
        hist = RAIZ / "docs" / "historial_cambios.md"
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        linea = "\n".join(f"- **{c['ticker']}**: {c['desde']} -> {c['hacia']}" for c in cambios)
        with open(hist, "a", encoding="utf-8") as h:
            h.write(f"\n## {fecha}\n{linea}\n")

    salida = {
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "corte_fundamental": cfg["clasificacion"]["corte_fundamental"],
        "corte_tecnico": cfg["clasificacion"]["corte_tecnico"],
        "corte_emergente": cfg["clasificacion"].get("corte_emergente", 60),
        "empresas": filas,
        "cambios": cambios,
    }
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    # data.js: permite abrir el tablero con doble clic (sin servidor / sin CORS)
    (SALIDA.parent / "data.js").write_text(
        "window.SCORING_DATA = " + json.dumps(salida, ensure_ascii=False) + ";",
        encoding="utf-8")

    resumen = {}
    for f in filas:
        resumen[f["categoria"]] = resumen.get(f["categoria"], 0) + 1
    print(f"\nOK -> {SALIDA}")
    print("Resumen por categoria:", resumen)


if __name__ == "__main__":
    main()
