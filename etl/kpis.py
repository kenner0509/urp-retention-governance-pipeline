"""KPIs de las Fichas Técnicas (KPI-01 a KPI-10) calculados sobre el dataset v0 / v1."""
import numpy as np
import pandas as pd
from .config import SLA_DIAS_CARGA, TASA_REF_NO_CONTINUIDAD


def _semaforo(valor, meta, alerta, mayor_mejor):
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "N/C"
    if mayor_mejor:
        return "🟢 Cumple" if valor >= meta else ("🔴 Alerta" if valor < alerta else "🟡 Vigilar")
    return "🟢 Cumple" if valor <= meta else ("🔴 Alerta" if valor > alerta else "🟡 Vigilar")


def calcular_kpis(df_v0, diag, v1) -> pd.DataFrame:
    filas = []

    def fila(cod, nombre, valor, meta_num, alerta_num, mayor_mejor, unidad, meta_txt, alerta_txt, nota):
        filas.append({"KPI": cod, "Nombre": nombre,
                      "Valor": None if valor is None else round(float(valor), 2),
                      "Unidad": unidad, "Meta": meta_txt, "Umbral alerta": alerta_txt,
                      "Estado": _semaforo(valor, meta_num, alerta_num, mayor_mejor), "Nota": nota})

    n = len(df_v0)
    fcr = 100 * (1 - diag["falla_validacion_primaria"].mean())
    fila("KPI-01", "FCR de Ingesta", fcr, 95, 90, True, "%", "≥ 95%", "< 90%",
         "Proxy: registros sin duplicado/rango/catálogo/fecha inválidos (no hay logs ETL en v0).")

    lag = (pd.to_datetime(df_v0["fecha_carga"], errors="coerce") -
           pd.to_datetime(df_v0["fecha_inicio_periodo"], errors="coerce")).dt.days
    lag = lag[lag >= 0]
    fila("KPI-02", "MTTR de Ingesta (proxy)", lag.mean(), 2, 4, False, "días", "≤ 2 días", "> 4 días",
         f"Proxy con fecha_carga − fecha_inicio_periodo (mediana={lag.median():.0f} d). Faltan timestamps de lote.")

    fila("KPI-03", "Multiprograma", None, 0, 0, True, "%", "Tendencia", "±20%",
         "NO CALCULABLE: v0 no trae ID persistente de estudiante ni segundo programa. Solicitar a Registro Académico.")

    fila("KPI-04", "Registros con errores de calidad", 100 * diag["tiene_error_calidad"].mean(), 3, 5, False,
         "%", "≤ 3%", "> 5%", "Precisión (rangos), consistencia (duplicados, catálogos, fechas) y completitud.")

    oportuno = 100 * (1 - diag["e_carga_tardia"].mean())
    fila("KPI-05", "Oportunidad de carga (Timeliness)", oportuno, 95, 90, True, "%", "≥ 95%", "< 90%",
         f"SLA supuesto = {SLA_DIAS_CARGA} días desde inicio de periodo (validar con TI).")

    fila("KPI-06", "Completitud de registro", 100 * (1 - diag["e_nulo_critico"].mean()), 98, 95, True,
         "%", "≥ 98%", "< 95%", "Campos críticos definidos en config.CAMPOS_CRITICOS.")

    riesgo = v1[v1["f_riesgo_regla"] == 1]
    cob = 100 * riesgo["f_acompanado"].mean() if len(riesgo) else None
    fila("KPI-07", "Cobertura de intervención (proxy)", cob, 90, 80, True, "%", "≥ 90%", "< 80%",
         "Riesgo = ≥2 alertas (promedio, asistencia, inactividad, reprobación). Atendido = beca_o_apoyo='Tutoría académica'.")

    virt = v1[v1["modalidad"] == "Virtual"]
    fila("KPI-08", "Inactividad en campus virtual", 100 * virt["f_inactivo_campus"].mean(), 10, 20, False,
         "%", "≤ 10%", "> 20%", "Solo modalidad Virtual (ficha). Umbral de inactividad supuesto en config.")

    s = v1.groupby("semestre")["no_continua_siguiente_periodo"].mean() * 100
    base, ultimo = s.iloc[0], s.iloc[-1]
    meta_k9 = base * 0.85
    fila("KPI-09", "No continuidad por corte", ultimo, meta_k9, meta_k9 * 1.10, False, "%",
         f"≤ {meta_k9:.1f}% (−15% vs base {base:.1f}%)", f"> {meta_k9*1.10:.1f}%",
         f"Último semestre vs línea base {s.index[0]}. Ref. anual comparable: {TASA_REF_NO_CONTINUIDAD:.0%} (no equivalente a tasa por periodo).")

    ac = v1[v1["f_acompanado"] == 1]
    fila("KPI-10", "Deserción de acompañados", 100 * ac["no_continua_siguiente_periodo"].mean(), 15, 25, False,
         "%", "≤ 15%", "> 25%", "Ojo: sesgo de selección (solo ingresan estudiantes ya en riesgo).")
    return pd.DataFrame(filas)
