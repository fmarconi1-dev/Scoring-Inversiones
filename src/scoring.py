"""Convierte metricas fundamentales y tecnicas en scores 0-100 y clasifica.
Toda regla lee umbrales del config: nada hardcodeado."""
from __future__ import annotations


# ----------------------------- Fundamental -----------------------------

def _puntaje_metrica(valor, umbral: dict) -> float | None:
    """Mapea un valor a 0..1 segun umbrales excelente/aceptable y direccion.
    Interpolacion lineal simple; devuelve None si el dato falta."""
    if valor is None:
        return None
    exc, acp = umbral["excelente"], umbral["aceptable"]
    if umbral["direccion"] == "menor_mejor":
        # 1.0 en "excelente"; 0.5 en "aceptable"; sigue bajando a 0 mas alla,
        # con la misma pendiente. Monotono y continuo (sin salto en el umbral).
        span = (acp - exc) or 1
        if valor <= exc:
            return 1.0
        if valor <= acp:
            return 1.0 - 0.5 * (valor - exc) / span      # exc..acp -> 1.0..0.5
        return max(0.0, 0.5 - 0.5 * (valor - acp) / span)  # > acp   -> 0.5..0.0
    else:  # mayor_mejor
        if valor >= exc:
            return 1.0
        if valor <= acp * 0.5:
            return 0.0
        if valor >= acp:
            return 0.5 + (valor - acp) / (exc - acp) * 0.5  # acp..exc -> 0.5..1
        return (valor - acp * 0.5) / (acp * 0.5) * 0.5      # acp/2..acp -> 0..0.5


def score_fundamental(fund: dict, cfg: dict, sector: str | None = None) -> dict:
    uf = cfg["umbrales_fundamentales"]
    pesos = uf["pesos"]
    campos = ["pe", "pb", "roe", "deuda_equity", "margen_neto"]
    # Sectores donde Deuda/Equity de la fuente no es significativo (bancos/financieras):
    # se excluye la metrica y se reponderan las demas (ver metodologia).
    sectores_de_na = set(uf.get("sectores_deuda_equity_na", []))
    excluir_de = sector in sectores_de_na if sector else False

    detalle, acum, peso_valido = {}, 0.0, 0.0
    presentes = 0
    for clave in campos:
        if clave == "deuda_equity" and excluir_de:
            detalle[clave] = {"valor": fund.get(clave), "puntaje": None,
                              "na_sector": True}  # marcada N/A por sector, no penaliza
            continue
        val = fund.get(clave)
        p = _puntaje_metrica(val, uf[clave])
        detalle[clave] = {"valor": val, "puntaje": p}
        if p is not None:
            acum += p * pesos[clave]
            peso_valido += pesos[clave]
            presentes += 1
    # En financieras, el peso del D/E (excluido) va a ROA, que si es significativo en bancos
    if excluir_de:
        roa_val = fund.get("roa")
        proa = _puntaje_metrica(roa_val, uf.get("roa", {"excelente": 0.015, "aceptable": 0.007, "direccion": "mayor_mejor"}))
        detalle["roa"] = {"valor": roa_val, "puntaje": proa}
        if proa is not None:
            acum += proa * pesos["deuda_equity"]
            peso_valido += pesos["deuda_equity"]
            presentes += 1

    score = round(acum / peso_valido * 100, 1) if peso_valido > 0 else None
    return {"score": score, "metricas_presentes": presentes,
            "detalle": detalle, "de_excluida_sector": excluir_de}


# ------------------------------- Tecnico -------------------------------

def score_tecnico(tec: dict, cfg: dict, target_mean=None, precio=None) -> dict:
    if tec.get("error"):
        return {"score": None, "error": tec["error"], "detalle": {}}
    ct = cfg["umbrales_tecnicos"]
    pesos = ct["pesos"]
    p, det, total = 0.0, {}, 0.0

    precio, mm200, mm50 = tec.get("precio"), tec.get("mm200"), tec.get("mm50")
    # 1. Precio vs MM200 (tendencia primaria)
    if precio is not None and mm200 is not None:
        ok = precio > mm200
        p += pesos["precio_vs_mm200"] if ok else 0
        total += pesos["precio_vs_mm200"]
        det["precio_vs_mm200"] = {"ok": ok, "detalle": f"precio {'>' if ok else '<='} MM200"}
    # 2. Cruce MM50/MM200
    if mm50 is not None and mm200 is not None:
        ok = mm50 > mm200
        p += pesos["cruce_mm50_200"] if ok else 0
        total += pesos["cruce_mm50_200"]
        det["cruce_mm50_200"] = {"ok": ok, "detalle": "golden" if ok else "death"}
    # 3. RSI
    rsi_v = tec.get("rsi")
    if rsi_v is not None:
        r = ct["rsi"]
        if r["sano_min"] <= rsi_v <= r["sano_max"]:
            frac, txt = 1.0, "sano"
        elif rsi_v < r["sobreventa"]:
            frac, txt = 0.7, "sobreventa (oportunidad si calidad)"
        elif rsi_v > r["sobrecompra"]:
            frac, txt = 0.2, "sobrecompra"
        else:
            frac, txt = 0.6, "neutral"
        p += pesos["rsi"] * frac
        total += pesos["rsi"]
        det["rsi"] = {"ok": frac >= 0.6, "detalle": f"RSI {rsi_v:.0f} ({txt})"}
    # 4. MACD
    macd_v, macd_s = tec.get("macd"), tec.get("macd_senal")
    if macd_v is not None and macd_s is not None:
        ok = macd_v > macd_s
        p += pesos["macd"] if ok else 0
        total += pesos["macd"]
        det["macd"] = {"ok": ok, "detalle": "momentum+" if ok else "momentum-"}
    # 5. OBV
    obv_p = tec.get("obv_pendiente")
    if obv_p is not None:
        ok = obv_p > 0
        p += pesos["obv"] if ok else 0
        total += pesos["obv"]
        det["obv"] = {"ok": ok, "detalle": "volumen acumula" if ok else "volumen distribuye"}

    score = round(p / total * 100, 1) if total > 0 else None

    # --- Penalizaciones por techo (agotamiento) y falta de recorrido ---
    if score is not None:
        # 1) Cercania a maximos SIN ruptura confirmada por volumen
        if tec.get("en_techo"):
            if tec.get("ruptura_confirmada"):
                vr = tec.get("vol_ratio")
                det["techo"] = {"ok": True, "detalle": f"ruptura de maximos con volumen ({vr}x prom.)" if vr else "ruptura de maximos con volumen (sano)"}
            else:
                score -= ct.get("penal_techo", 15)
                vr = tec.get("vol_ratio")
                fac = ct.get("ruptura_vol_factor", 1.5)
                txt = (f"en maximos, volumen {vr}x (<{fac}x): sin confirmacion (riesgo de techo/doble techo)"
                       if vr is not None else "en maximos sin confirmacion de volumen (riesgo de techo/doble techo)")
                det["techo"] = {"ok": False, "detalle": txt}
        else:
            det["techo"] = {"ok": True, "detalle": "con recorrido por debajo de maximos"}
        # 2) Recorrido hasta el objetivo de analistas
        if target_mean and precio:
            up = target_mean / precio - 1
            if up <= 0:
                score -= ct.get("penal_sin_recorrido", 10)
                det["recorrido"] = {"ok": False, "detalle": f"precio en/sobre el objetivo ({up*100:.0f}%)"}
            elif up < ct.get("recorrido_min", 0.05):
                score -= ct.get("penal_poco_recorrido", 5)
                det["recorrido"] = {"ok": False, "detalle": f"poco recorrido al objetivo (+{up*100:.0f}%)"}
            else:
                det["recorrido"] = {"ok": True, "detalle": f"recorrido al objetivo +{up*100:.0f}%"}
        # 3) Divergencia bajista de RSI (momentum se debilita mientras el precio sube)
        if tec.get("divergencia_bajista"):
            score -= ct.get("penal_divergencia", 8)
            det["divergencia"] = {"ok": False, "detalle": "divergencia bajista de RSI (precio sube, momentum baja)"}
        else:
            det["divergencia"] = {"ok": True, "detalle": "sin divergencia bajista de RSI"}
        score = max(0.0, round(score, 1))

    return {"score": score, "detalle": det}


# ------------------------------ Emergente ------------------------------

def _supervivencia(fund: dict, runway_min: float) -> tuple:
    """Devuelve (score 0..1, riesgo_liquidez, runway_anios).
    FCF>0 -> autofinanciada; caja>deuda -> solida; si no, mira el runway."""
    fcf = fund.get("fcf")
    caja = fund.get("caja")
    deuda = fund.get("deuda_total")
    if fcf is not None and fcf > 0:
        return 1.0, False, None
    caja_neta = None
    if caja is not None and deuda is not None:
        caja_neta = caja - deuda
        if caja_neta > 0:
            return 0.85, False, None
    # quema caja: runway = caja / quema anual
    if caja is not None and fcf is not None and fcf < 0:
        runway = caja / abs(fcf)
        riesgo = (runway < runway_min) and (caja_neta is None or caja_neta <= 0)
        # score: 0 en runway 0, ~1 en runway 3+ anios
        sc = max(0.0, min(1.0, (runway - runway_min) / (3.0 - runway_min))) if runway >= runway_min else 0.15
        return sc, riesgo, round(runway, 2)
    return None, False, None  # sin datos suficientes


def _valuacion(fund: dict, uval: dict) -> dict:
    """PEG si hay ganancias; si no, PSG = P/S / crecimiento%. Menor es mejor."""
    peg = fund.get("peg")
    if peg is not None and peg > 0:
        u = {"excelente": uval["peg_excelente"], "aceptable": uval["peg_aceptable"], "direccion": "menor_mejor"}
        return {"valor": peg, "puntaje": _puntaje_metrica(peg, u), "base": "PEG"}
    ps, crec = fund.get("ps"), fund.get("crecimiento")
    if ps is not None and crec is not None and crec > 0:
        psg = ps / (crec * 100)  # P/S sobre crecimiento en %
        u = {"excelente": uval["psg_excelente"], "aceptable": uval["psg_aceptable"], "direccion": "menor_mejor"}
        return {"valor": psg, "puntaje": _puntaje_metrica(psg, u), "base": "P/S÷crec"}
    return {"valor": None, "puntaje": None, "base": None}


def score_emergente(fund: dict, cfg: dict, tec: dict | None = None) -> dict:
    ue = cfg.get("umbrales_emergente")
    if not ue:
        return {"score": None, "detalle": {}, "riesgo_liquidez": False}
    pesos = ue["pesos"]
    detalle, acum, peso_valido, presentes = {}, 0.0, 0.0, 0

    # Regla del 40 = crecimiento% + margen FCF%
    r40 = None
    if fund.get("crecimiento") is not None and fund.get("fcf") is not None and fund.get("ingresos"):
        r40 = fund["crecimiento"] * 100 + (fund["fcf"] / fund["ingresos"]) * 100

    # Margen bruto no es significativo en bancos/financieras -> se excluye (como el D/E)
    sec_mb_na = set(ue.get("sectores_margen_bruto_na", []))
    excluir_mb = fund.get("sector") in sec_mb_na

    metricas = {
        "crecimiento": fund.get("crecimiento"),
        "margen_bruto": fund.get("margen_bruto"),
        "regla_40": r40,
        "insiders": fund.get("insiders"),
    }
    for clave, val in metricas.items():
        if clave == "margen_bruto" and excluir_mb:
            detalle[clave] = {"valor": val, "puntaje": None, "na_sector": True}
            continue
        pj = _puntaje_metrica(val, ue[clave])
        detalle[clave] = {"valor": val, "puntaje": pj}
        if pj is not None:
            acum += pj * pesos[clave]; peso_valido += pesos[clave]; presentes += 1

    # Valuacion (PEG o P/S/crec) como metrica propia
    val_d = _valuacion(fund, ue["valuacion"])
    detalle["valuacion"] = val_d
    if val_d["puntaje"] is not None:
        acum += val_d["puntaje"] * pesos["valuacion"]; peso_valido += pesos["valuacion"]; presentes += 1

    # Supervivencia (runway)
    sup_sc, riesgo, runway = _supervivencia(fund, ue.get("runway_min_anios", 1.0))
    detalle["supervivencia"] = {"valor": runway, "puntaje": sup_sc, "riesgo_liquidez": riesgo}
    if sup_sc is not None:
        acum += sup_sc * pesos["supervivencia"]; peso_valido += pesos["supervivencia"]; presentes += 1

    score = round(acum / peso_valido * 100, 1) if peso_valido > 0 else None
    return {"score": score, "metricas_presentes": presentes, "detalle": detalle,
            "riesgo_liquidez": riesgo, "runway": runway, "market_cap": fund.get("market_cap")}


# ---------------------------- Clasificacion ----------------------------

def clasificar(sf: dict, st: dict, cfg: dict, se: dict | None = None) -> dict:
    cl = cfg["clasificacion"]
    f, t = sf.get("score"), st.get("score")
    fund_ok = (f is not None and f >= cl["corte_fundamental"]
               and sf.get("metricas_presentes", 0) >= cl["min_metricas_fundamentales"])
    tec_ok = t is not None and t >= cl["corte_tecnico"]
    triple = fund_ok and tec_ok

    # Sub-veredicto clasico (para la pestana "Otros")
    if triple:      sub = "triple_corona"
    elif fund_ok:   sub = "fundamental"
    elif tec_ok:    sub = "tecnico"
    else:           sub = "ninguna"

    # Track emergente
    se = se or {}
    e = se.get("score")
    mc = se.get("market_cap")
    techo = cl.get("market_cap_max_emergente")
    tamano_ok = (mc is not None) and (techo is None or mc < techo)  # naciente = no mega-cap
    emergente_ok = (e is not None and e >= cl.get("corte_emergente", 60)
                    and se.get("metricas_presentes", 0) >= cfg.get("umbrales_emergente", {}).get("min_metricas", 3)
                    and not se.get("riesgo_liquidez", False)
                    and tamano_ok)

    # Categoria de nivel superior (pestanas): madura tiene prioridad sobre emergente
    if triple:
        cat = "triple_corona_madura"
    elif emergente_ok:
        cat = "emergente_calidad"
    else:
        cat = "otros"

    return {"categoria": cat, "sub_veredicto": sub,
            "fundamental_ok": fund_ok, "tecnico_ok": tec_ok, "emergente_ok": emergente_ok,
            "score_fundamental": f, "score_tecnico": t, "score_emergente": e}
