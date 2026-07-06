"""DataProvider: unica puerta a los datos de mercado.
- Fuente: yfinance (gratis, sin API key). US + ADRs en USD.
- Cache local por dia en /cache (evita golpear la API y da fallback si cae).
- Manejo de errores: reintentos con backoff; ante fallo, usa cache aunque este vieja.
La logica de scoring NUNCA llama a yfinance directo: siempre pasa por aca."""
from __future__ import annotations
import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

_CACHE = Path(__file__).parent / "cache"
_CACHE.mkdir(exist_ok=True)


def _ruta_hist(ticker: str) -> Path:
    return _CACHE / f"{ticker}_hist5y.csv"


def _ruta_info(ticker: str) -> Path:
    return _CACHE / f"{ticker}_info.json"


def _fresco(path: Path) -> bool:
    """True si el archivo se genero hoy (cache EOD valida por el dia)."""
    if not path.exists():
        return False
    mtime = date.fromtimestamp(path.stat().st_mtime)
    return mtime == date.today()


def _con_reintentos(fn, intentos: int = 3, base: float = 1.5):
    ultimo = None
    for i in range(intentos):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - queremos capturar todo error de red
            ultimo = e
            time.sleep(base ** i)
    raise ultimo


def obtener_historia(ticker: str, periodo: str = "5y") -> pd.DataFrame:
    """Precios diarios. Cache -> API -> cache vieja como fallback."""
    ph = _ruta_hist(ticker)
    if _fresco(ph):
        try:
            return pd.read_csv(ph, index_col=0, parse_dates=True)
        except Exception:
            pass
    try:
        def _fetch():
            tkr = yf.Ticker(ticker)
            df = tkr.history(period=periodo, auto_adjust=True)
            if df is None or df.empty:
                raise ValueError("historia vacia")
            # first trade date (para el radar de nacientes)
            try:
                ft = (getattr(tkr, "history_metadata", {}) or {}).get("firstTradeDate")
                if ft:
                    (_CACHE / f"{ticker}_meta.json").write_text(json.dumps({"first_trade": int(ft)}), encoding="utf-8")
            except Exception:
                pass
            return df
        df = _con_reintentos(_fetch)
        df.to_csv(ph)
        return df
    except Exception as e:
        if ph.exists():  # fallback: cache aunque sea de ayer
            print(f"  [WARN] {ticker}: uso cache vieja de historia ({e})")
            return pd.read_csv(ph, index_col=0, parse_dates=True)
        print(f"  [ERROR] {ticker}: sin historia y sin cache ({e})")
        return pd.DataFrame()


def anios_cotizando(ticker: str):
    """Anios desde la primera cotizacion (para el radar de nacientes). None si no hay dato."""
    import datetime as _dt
    mp = _CACHE / f"{ticker}_meta.json"
    if not mp.exists():
        return None
    try:
        ft = json.loads(mp.read_text(encoding="utf-8")).get("first_trade")
        if not ft:
            return None
        return round((_dt.datetime.utcnow() - _dt.datetime.utcfromtimestamp(ft)).days / 365.25, 1)
    except Exception:
        return None


def obtener_fundamentals(ticker: str) -> dict:
    """Metricas fundamentales normalizadas. Faltantes quedan en None."""
    pi = _ruta_info(ticker)
    info = None
    if _fresco(pi):
        try:
            info = json.loads(pi.read_text(encoding="utf-8"))
        except Exception:
            info = None
    if info is None:
        try:
            info = _con_reintentos(lambda: yf.Ticker(ticker).info)
            pi.write_text(json.dumps(info, default=str), encoding="utf-8")
        except Exception as e:
            if pi.exists():
                print(f"  [WARN] {ticker}: uso cache vieja de fundamentals ({e})")
                info = json.loads(pi.read_text(encoding="utf-8"))
            else:
                print(f"  [ERROR] {ticker}: sin fundamentals ({e})")
                info = {}

    de = info.get("debtToEquity")

    def _pos(x):
        # descarta valores no positivos o absurdos de la fuente (p.ej. BRK-B P/B=0.001, gross=0 en bancos)
        return x if isinstance(x, (int, float)) and x > 0 else None

    return {
        "pe": _pos(info.get("trailingPE")),
        "pb": (lambda x: x if isinstance(x,(int,float)) and x > 0.05 else None)(info.get("priceToBook")),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        # yfinance da debtToEquity en % (150 = 1.5x); normalizamos a ratio
        "deuda_equity": (de / 100.0) if isinstance(de, (int, float)) else None,
        "margen_neto": info.get("profitMargins"),
        "nombre_yf": info.get("shortName") or info.get("longName"),
        "sector": info.get("sector"),
        "market_cap": info.get("marketCap"),
        # --- campos para el track Emergente ---
        "crecimiento": info.get("revenueGrowth"),
        "margen_bruto": _pos(info.get("grossMargins")),
        "fcf": info.get("freeCashflow"),
        "ingresos": info.get("totalRevenue"),
        "caja": info.get("totalCash"),
        "deuda_total": info.get("totalDebt"),
        "insiders": info.get("heldPercentInsiders"),
        "peg": _pos(info.get("trailingPegRatio") or info.get("pegRatio")),
        "ps": _pos(info.get("priceToSalesTrailing12Months")),
        # --- target price (consenso de analistas) ---
        "target_mean": info.get("targetMeanPrice"),
        "target_high": info.get("targetHighPrice"),
        "target_low": info.get("targetLowPrice"),
        "precio_actual": info.get("currentPrice"),
        "n_analistas": info.get("numberOfAnalystOpinions"),
    }
