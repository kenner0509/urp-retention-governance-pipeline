"""KPI-09 · Tasa de No Continuidad Académica por Corte (única KPI de foco).

Ficha técnica:  Tasa (%) = (E_t − E_t→t+1) / E_t × 100
  Meta   : reducción del 15 % vs. línea base      Alerta: +10 % de variación negativa sobre la meta
  Sentido: ↓ menor es mejor                        Frecuencia: por periodo académico
Aquí  E_t = estudiantes del corte;  no_continua_siguiente_periodo = 1  ⇔  no reinscrito en t+1.
Limitación: el v0 no trae marca de egresado, por lo que no se puede excluir a graduados (regla de negocio de la ficha).
"""
import pandas as pd

META_REDUCCION = 0.15      # -15 % vs línea base
MARGEN_ALERTA = 0.10       # +10 % sobre la meta


def _estado(valor, meta):
    if valor <= meta:
        return "🟢 Cumple"
    return "🟡 Vigilar" if valor <= meta * (1 + MARGEN_ALERTA) else "🔴 Alerta"


def tasa_por_corte(v1: pd.DataFrame, corte="semestre") -> pd.DataFrame:
    g = v1.groupby(corte)["no_continua_siguiente_periodo"].agg(estudiantes="size", no_continuan="sum")
    g["tasa_pct"] = (100 * g["no_continuan"] / g["estudiantes"]).round(2)
    return g.reset_index()


def calcular_kpi09(v1: pd.DataFrame) -> pd.DataFrame:
    """Una fila con el valor actual, línea base, meta y estado."""
    s = tasa_por_corte(v1)
    base, actual = float(s["tasa_pct"].iloc[0]), float(s["tasa_pct"].iloc[-1])
    meta = round(base * (1 - META_REDUCCION), 2)
    return pd.DataFrame([{
        "KPI": "KPI-09", "Nombre": "Tasa de No Continuidad Académica por Corte",
        "Corte_base": s["semestre"].iloc[0], "Linea_base_pct": base,
        "Corte_actual": s["semestre"].iloc[-1], "Valor_actual_pct": actual,
        "Meta_pct": meta, "Umbral_alerta_pct": round(meta * (1 + MARGEN_ALERTA), 2),
        "Variacion_vs_base_pct": round(100 * (actual - base) / base, 2),
        "Estudiantes_evaluados": int(len(v1)), "Estado": _estado(actual, meta),
        "Nota": "Sin marca de egresado en v0: no se excluyen graduados (regla de negocio de la ficha).",
    }])


def detalle_kpi09(v1: pd.DataFrame) -> pd.DataFrame:
    """KPI-09 desagregado por semestre, modalidad, programa y condición de ingreso."""
    partes = []
    for dim in ["semestre", "modalidad", "programa_academico", "condicion_ingreso"]:
        t = tasa_por_corte(v1, dim).rename(columns={dim: "segmento"}); t.insert(0, "dimension", dim)
        partes.append(t)
    return pd.concat(partes, ignore_index=True)