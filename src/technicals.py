"""Indicadores tecnicos calculados sobre una serie de precios de cierre.
Sin dependencias mas alla de pandas. Cada funcion es pura y testeable."""
from __future__ import annotations
import pandas as pd


def sma(serie: pd.Series, ventana: int) -> pd.Series:
    return serie.rolling(window=ventana, min_periods=ventana).mean()


def rsi(serie: pd.Series, periodo: int = 14) -> pd.Series:
    delta = serie.diff()
    ganancia = delta.clip(lower=0.0)
    perdida = -delta.clip(upper=0.0)
    avg_g = ganancia.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
    avg_p = perdida.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
    rs = avg_g / avg_p.replace(0.0, pd.NA)
    return 100 - (100 / (1 + rs))


def macd(serie: pd.Series, rapida: int = 12, lenta: int = 26, senal: int = 9):
    ema_r = serie.ewm(span=rapida, adjust=False).mean()
    ema_l = serie.ewm(span=lenta, adjust=False).mean()
    linea = ema_r - ema_l
    linea_senal = linea.ewm(span=senal, adjust=False).mean()
    histograma = linea - linea_senal
    return linea, linea_senal, histograma


def obv(cierre: pd.Series, volumen: pd.Series) -> pd.Series:
    direccion = cierre.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direccion * volumen).fillna(0).cumsum()


def _divergencia_bajista(cierre: pd.Series, rsi_s: pd.Series, ventana: int = 70, sep: int = 5) -> bool:
    """Precio hace un maximo mas alto pero el RSI hace un maximo mas bajo = divergencia bajista."""
    c = cierre.dropna()
    r = rsi_s.reindex(c.index)
    if len(c) < ventana:
        return False
    c = c.tail(ventana); r = r.tail(ventana)
    vals = c.values
    picos = []
    for i in range(sep, len(vals) - sep):
        if vals[i] == max(vals[i - sep:i + sep + 1]):
            if not picos or i - picos[-1] > sep:  # evita picos pegados
                picos.append(i)
    if len(picos) < 2:
        return False
    p1, p2 = picos[-2], picos[-1]  # anterior, reciente
    precio_hh = vals[p2] > vals[p1]
    rsi_lh = r.iloc[p2] is not None and r.iloc[p1] is not None and r.iloc[p2] < r.iloc[p1]
    return bool(precio_hh and rsi_lh)


def calcular_indicadores(hist: pd.DataFrame, cfg_tec: dict) -> dict:
    """Recibe un DataFrame con columnas Close y Volume. Devuelve el snapshot
    tecnico mas reciente. Si no hay historia suficiente, marca los faltantes en None."""
    if hist is None or hist.empty or "Close" not in hist:
        return {"error": "sin_historia"}

    cierre = hist["Close"].dropna()
    volumen = hist.get("Volume", pd.Series(dtype=float)).reindex(cierre.index).fillna(0)
    if len(cierre) < 30:
        return {"error": "historia_insuficiente", "barras": int(len(cierre))}

    mm_c = cfg_tec["mm_corta"]
    mm_l = cfg_tec["mm_larga"]
    mm50 = sma(cierre, mm_c)
    mm200 = sma(cierre, mm_l)
    rsi_s = rsi(cierre, cfg_tec["rsi"]["periodo"])
    linea, senal, hist_macd = macd(cierre, cfg_tec["macd"]["rapida"],
                                   cfg_tec["macd"]["lenta"], cfg_tec["macd"]["senal"])
    obv_s = obv(cierre, volumen)
    obv_win = cfg_tec["obv_ventana"]

    def ult(s):
        v = s.dropna()
        return float(v.iloc[-1]) if len(v) else None

    divergencia_bajista = _divergencia_bajista(cierre, rsi_s)

    obv_pendiente = None
    obv_valida = obv_s.dropna()
    if len(obv_valida) > obv_win:
        obv_pendiente = float(obv_valida.iloc[-1] - obv_valida.iloc[-obv_win - 1])

    # --- Techo: cercania a maximos y ruptura confirmada por volumen ---
    precio_ult = float(cierre.iloc[-1])
    max_precio = float(cierre.max())               # maximo del periodo (~5 anios), usado para el techo/ATH
    dist_ath = precio_ult / max_precio if max_precio else None
    # Confirmacion por volumen: volumen del dia >= factor x promedio de N ruedas
    fac = cfg_tec.get("ruptura_vol_factor", 1.5)
    vent = cfg_tec.get("ruptura_vol_ventana", 50)
    vol_ratio = None
    if len(volumen) >= vent:
        vmed = float(volumen.tail(vent).mean())
        if vmed > 0:
            vol_ratio = round(float(volumen.iloc[-1]) / vmed, 2)
    volumen_confirma = vol_ratio is not None and vol_ratio >= fac
    techo_prox = cfg_tec.get("techo_proximidad", 0.97)
    en_techo = dist_ath is not None and dist_ath >= techo_prox
    nuevo_max = dist_ath is not None and dist_ath >= 0.999
    ruptura_confirmada = bool(nuevo_max and volumen_confirma)

    # Antiguedad del cruce MM50/MM200 (en ruedas)
    dias_cruce, cruce_tipo = None, None
    dif = (mm50 - mm200).dropna()
    if len(dif) > 1:
        signo = dif.apply(lambda x: 1 if x >= 0 else -1)
        cambios = signo[signo != signo.shift(1)]
        if len(cambios) > 1:  # el primero es el arranque de la serie, no un cruce real
            loc = signo.index.get_loc(cambios.index[-1])
            dias_cruce = int(len(signo) - 1 - loc)
        cruce_tipo = "golden" if signo.iloc[-1] > 0 else "death"

    return {
        "precio": ult(cierre),
        "mm50": ult(mm50),
        "mm200": ult(mm200),
        "dias_cruce": dias_cruce,
        "cruce_tipo": cruce_tipo,
        "rsi": ult(rsi_s),
        "macd": ult(linea),
        "macd_senal": ult(senal),
        "macd_hist": ult(hist_macd),
        "obv_pendiente": obv_pendiente,
        "divergencia_bajista": divergencia_bajista,
        "max_precio": max_precio,
        "dist_ath": dist_ath,
        "en_techo": en_techo,
        "ruptura_confirmada": ruptura_confirmada,
        "vol_ratio": vol_ratio,
        "barras": int(len(cierre)),
    }
