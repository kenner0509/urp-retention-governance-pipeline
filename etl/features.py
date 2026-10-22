"""FEATURES: indicadores de riesgo derivados de los KPIs (feature engineering)."""
import numpy as np
import pandas as pd
from .config import UMBRAL_INACTIVIDAD, NOTA_MINIMA_APROBACION, ASISTENCIA_MINIMA


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    print("[FEATURES] Construyendo variables derivadas...")
    f = df.copy()
    f["f_bajo_promedio"] = (f["promedio_periodo"] < NOTA_MINIMA_APROBACION).astype(int)
    f["f_baja_asistencia"] = (f["asistencia_pct"] < ASISTENCIA_MINIMA).astype(int)
    f["f_inactivo_campus"] = (f["accesos_campus_virtual"] <= UMBRAL_INACTIVIDAD).astype(int)   # KPI-08
    f["f_reprobacion_multiple"] = (f["asignaturas_reprobadas"] >= 2).astype(int)
    f["f_es_virtual"] = (f["modalidad"] == "Virtual").astype(int)
    f["f_nuevo_ingreso"] = (f["condicion_ingreso"] == "Nuevo ingreso").astype(int)
    f["f_acompanado"] = (f["beca_o_apoyo"] == "Tutoría académica").astype(int)                 # KPI-07/10
    f["f_tiene_beca"] = f["beca_o_apoyo"].isin(["Beca completa", "Beca parcial"]).astype(int)
    f["indice_alertas"] = f[["f_bajo_promedio", "f_baja_asistencia", "f_inactivo_campus",
                             "f_reprobacion_multiple"]].sum(axis=1)
    f["f_riesgo_regla"] = (f["indice_alertas"] >= 2).astype(int)   # regla simple de referencia
    f["mes_periodo"] = f["fecha_inicio_periodo"].dt.to_period("M").astype(str)
    f["semestre"] = f["fecha_inicio_periodo"].dt.year.astype(str) + "-S" + \
        np.where(f["fecha_inicio_periodo"].dt.month <= 6, "1", "2")
    return f
