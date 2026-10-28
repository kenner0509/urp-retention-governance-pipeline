"""POLÍTICAS PROGRAMADAS (policy-as-code) del Gobierno de Datos v2.

Este módulo NO se ejecuta solo al importarlo (antes los scripts corrían al abrirlos y pisaban outputs/).
Contiene funciones que el pipeline llama en cada carga:
  · seudonimizar_id / aplicar_seudonimizacion  → POL-PRIV-01
  · validar_registro / ejecutar_pruebas_control → pruebas válida e inválida del control (POL-CAL-01)
  · generar_bitacora                            → bitácora de incidencias (causa, tratamiento, responsable)
  · indicadores_phva                            → indicadores ANTES / DESPUÉS (ciclo PHVA)
  · generar_evidencia                           → evidencia por política con post-control
"""
import hashlib, hmac, os
from datetime import datetime
import numpy as np
import pandas as pd
from .config import (CATALOGOS, RANGOS, CAMPOS_CRITICOS, META_COMPLETITUD_INSTITUCIONAL,
                     ALGORITMO_SEUDONIMIZACION)
from .transform import tipificar

CLAVE = os.getenv("POLITICA_CLAVE", "URP-clave-demo-CAMBIAR-en-.env")
AHORA = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")

CATALOGO = pd.DataFrame([
    ("POL-ACC-01",  "Control de acceso por roles (RBAC)", "Mínimo privilegio: cada rol solo ve lo necesario", "APO14 / BAI09", "Custodio Técnico (TI)"),
    ("POL-PRIV-01", "Seudonimización", f"El ID del estudiante se reemplaza por {ALGORITMO_SEUDONIMIZACION} antes de analizar", "APO14", "Data Owner"),
    ("POL-CAL-01",  "Validación pre-ingreso", "Sin duplicados, valores en rango y fechas coherentes antes de entrar al pipeline", "APO14", "Data Steward"),
    ("POL-SEG-01",  "Uso con autorización", "Solo se analizan registros con autorización de uso analítico", "APO14", "Data Owner"),
    ("POL-USO-01",  "Catálogos normalizados", "Categorías únicas y oficiales (sin variantes de mayúsculas/espacios)", "APO14", "Data Steward"),
], columns=["codigo", "politica", "regla", "dominio_cobit", "responsable"])


# ------------------------------------------------------------------ POL-PRIV-01
def seudonimizar_id(valor) -> str:
    """HMAC-SHA256 con clave secreta: un SHA-256 simple se revierte probando IDs conocidos."""
    return hmac.new(CLAVE.encode(), str(valor).encode(), hashlib.sha256).hexdigest()


def aplicar_seudonimizacion(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    d = df.copy()
    d["id_estudiante_periodo"] = d["id_estudiante_periodo"].map(seudonimizar_id)
    return d


# ------------------------------------------------------------------ Pruebas del control
def validar_registro(registro: dict) -> list:
    """Devuelve la lista de violaciones de rango de UN registro (vacía = válido)."""
    fallas = []
    for col, (lo, hi) in RANGOS.items():
        v = registro.get(col)
        if v is not None and not (isinstance(v, float) and np.isnan(v)) and not (lo <= v <= hi):
            fallas.append(f"{col}={v} fuera del rango {lo}–{hi}")
    return fallas


def ejecutar_pruebas_control() -> pd.DataFrame:
    """Demostración de pruebas VÁLIDA e INVÁLIDA del control de calidad (para mostrar al docente)."""
    casos = [
        ("Prueba 1 · válida",   {"id": "EST-999", "promedio_periodo": 88,  "asistencia_pct": 92}, True),
        ("Prueba 2 · inválida", {"id": "EST-888", "promedio_periodo": 135, "asistencia_pct": 92}, False),
        ("Prueba 3 · inválida", {"id": "EST-777", "promedio_periodo": 80,  "asistencia_pct": 150}, False),
        ("Prueba 4 · válida",   {"id": "EST-666", "promedio_periodo": 55,  "asistencia_pct": 40}, True),
    ]
    filas = []
    for nombre, reg, esperado_valido in casos:
        fallas = validar_registro(reg)
        es_valido = not fallas
        filas.append({"prueba": nombre, "registro": reg["id"],
                      "datos": f"promedio={reg['promedio_periodo']}, asistencia={reg['asistencia_pct']}",
                      "resultado_control": "ACEPTADO" if es_valido else "RECHAZADO: " + "; ".join(fallas),
                      "esperado": "ACEPTADO" if esperado_valido else "RECHAZADO",
                      "aprobada": es_valido == esperado_valido})
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ Bitácora de incidencias
def generar_bitacora(v0, diag, n_pendientes, n_seudonimizados) -> pd.DataFrame:
    d = tipificar(v0)
    filas = []

    def reg(politica, causa, tratamiento, responsable, n):
        if int(n) > 0:
            filas.append({"fecha_hora": AHORA(), "politica": politica, "causa": causa,
                          "tratamiento": tratamiento, "responsable": responsable,
                          "registros_afectados": int(n)})

    reg("POL-CAL-01", "Registros duplicados en la extracción de fuentes origen",
        "Eliminación de filas duplicadas (se conserva la primera ocurrencia)", "Custodio Técnico (TI)",
        (diag["e_duplicado"] | diag["e_id_repetido"]).sum())
    for col, (lo, hi) in RANGOS.items():
        reg("POL-CAL-01", f"{col} fuera del rango esperado {lo}–{hi}",
            "Valor vaciado + bandera flag_fuera_rango_*; se imputa con la mediana DENTRO del modelo (no se borra el registro)",
            "Data Steward", diag[f"e_rango_{col}"].sum())
    reg("POL-CAL-01", "Fecha de carga anterior al inicio del periodo", "Fecha vaciada y marcada", "Data Steward",
        diag["e_fecha_incoherente"].sum())
    reg("POL-USO-01", "Etiquetas de catálogo con mayúsculas, espacios o variantes",
        "Normalización al catálogo oficial", "Data Steward",
        diag[[c for c in diag if c.startswith("e_catalogo_")]].any(axis=1).sum())
    reg("POL-SEG-01", "Registros sin autorización de uso analítico", "Exclusión del análisis (quedan en stg_rechazos_calidad)",
        "Data Owner", diag["e_sin_autorizacion"].sum())
    for col in RANGOS:
        reg("Calidad", f"Valores nulos en {col}", "Se marcan; imputación por mediana dentro del modelo (sin fuga de datos)",
            "Analista de Datos", d[col].isna().sum())
    reg("Calidad", "Resultado del siguiente periodo aún no consolidado",
        "No entran a entrenamiento; se puntúan como estudiantes pendientes", "Analista de Datos", n_pendientes)
    reg("POL-PRIV-01", "Identificadores directos del estudiante en el dato crudo",
        f"Seudonimización {ALGORITMO_SEUDONIMIZACION}", "Custodio Técnico (TI)", n_seudonimizados)
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ Indicadores ANTES / DESPUÉS (PHVA)
def _completitud(df):
    x = df[CAMPOS_CRITICOS].replace("Sin dato", np.nan)
    return 100 * (1 - x.isna().sum().sum() / (len(df) * len(CAMPOS_CRITICOS)))


def indicadores_phva(v0, diag, v1_real, v1_seud) -> pd.DataFrame:
    d0 = tipificar(v0)
    f = []

    def add(ind, antes, despues, meta, cumple, nota=""):
        f.append({"indicador": ind, "antes": round(float(antes), 2), "despues": round(float(despues), 2),
                  "meta": meta, "estado": "CUMPLE" if cumple else "INCUMPLE", "nota": nota})

    add("Registros totales", len(v0), len(v1_real), "—", True,
        "El dataset analítico excluye duplicados, sin autorización y sin resultado consolidado")
    c0, c1 = _completitud(d0), _completitud(v1_real)
    add("Completitud de celdas críticas (%)", c0, c1, f"≥ {META_COMPLETITUD_INSTITUCIONAL*100:.0f}%",
        c1 >= META_COMPLETITUD_INSTITUCIONAL * 100,
        "Baja levemente porque los valores inválidos pasan a vacío; el modelo los imputa (completitud utilizable 100%)")
    add("Registros duplicados", diag["e_duplicado"].sum(), v1_real.duplicated().sum(), "0", v1_real.duplicated().sum() == 0)
    r_cols = [c for c in diag if c.startswith("e_rango_")]
    fuera_despues = sum(((v1_real[c] < lo) | (v1_real[c] > hi)).sum() for c, (lo, hi) in RANGOS.items())
    add("Valores fuera de rango (registros)", diag[r_cols].any(axis=1).sum(), fuera_despues, "0", fuera_despues == 0)
    cat_despues = sum((~v1_real[c].isin(cat + ["Sin dato"]) & v1_real[c].notna()).sum() for c, cat in CATALOGOS.items())
    add("Etiquetas fuera de catálogo (registros)", diag[[c for c in diag if c.startswith("e_catalogo_")]].any(axis=1).sum(),
        cat_despues, "0", cat_despues == 0)
    sin_aut = (~v1_real["autorizacion_uso_analitico"].astype(str).str.strip().str.casefold().isin(["si", "sí"])).sum()
    add("Registros sin autorización de uso", diag["e_sin_autorizacion"].sum(), sin_aut, "0", sin_aut == 0)
    pct_sin_seud = 100 * (~v1_seud["id_estudiante_periodo"].str.fullmatch(r"[0-9a-f]{64}")).mean()
    add("IDs sin seudonimizar (%)", 100, pct_sin_seud, "0%", pct_sin_seud == 0)
    return pd.DataFrame(f)


# ------------------------------------------------------------------ Evidencia por política (post-control)
def _verificar_roles_sql():
    """POL-ACC-01 se programa en SQL Server (sql/03_politicas_acceso.sql). Aquí solo se verifica."""
    try:
        from sqlalchemy import text
        from .extract import crear_engine
        with crear_engine().connect() as c:
            roles = {r[0] for r in c.execute(text("SELECT name FROM sys.database_principals WHERE type='R'"))}
        faltan = {"rol_analista", "rol_bienestar", "rol_custodio_ti"} - roles
        return (0, "CUMPLE") if not faltan else (len(faltan), f"INCUMPLE: faltan roles {sorted(faltan)}")
    except Exception:
        return (None, "NO VERIFICADO (requiere SQL Server y sql/03_politicas_acceso.sql)")


def generar_evidencia(v0, diag, v1_real, v1_seud, lote=None) -> pd.DataFrame:
    lote = lote or datetime.now().strftime("%Y%m%d-%H%M%S")
    n, f = len(v0), []

    def add(cod, evaluados, detectados, tratamiento, post, estado=None):
        f.append({"lote": lote, "fecha_ejecucion": AHORA(), "codigo": cod, "evaluados": int(evaluados),
                  "detectados": None if detectados is None else int(detectados), "tratamiento": tratamiento,
                  "incumplen_despues": None if post is None else int(post),
                  "estado": estado or ("CUMPLE" if post == 0 else "INCUMPLE")})

    c_rango = [c for c in diag if c.startswith("e_rango_")]
    det = diag[["e_duplicado", "e_id_repetido", "e_fecha_incoherente"] + c_rango].any(axis=1).sum()
    post = v1_real["id_estudiante_periodo"].duplicated().sum()
    for col, (lo, hi) in RANGOS.items():
        post += ((v1_real[col] < lo) | (v1_real[col] > hi)).sum()
    add("POL-CAL-01", n, det, "Duplicados → rechazados; fuera de rango → vacío + bandera", post)

    post = (~v1_real["autorizacion_uso_analitico"].astype(str).str.strip().str.casefold().isin(["si", "sí"])).sum()
    add("POL-SEG-01", n, diag["e_sin_autorizacion"].sum(), "Sin autorización → excluidos del análisis", post)

    det = diag[[c for c in diag if c.startswith("e_catalogo_")]].any(axis=1).sum()
    post = sum((~v1_real[c].isin(cat + ["Sin dato"]) & v1_real[c].notna()).sum() for c, cat in CATALOGOS.items())
    add("POL-USO-01", n, det, "Etiquetas normalizadas al catálogo oficial", post)

    ids = v1_seud["id_estudiante_periodo"]
    post = (~ids.str.fullmatch(r"[0-9a-f]{64}")).sum() + ids.duplicated().sum()
    add("POL-PRIV-01", len(v1_seud), len(v1_seud), f"ID real reemplazado por {ALGORITMO_SEUDONIMIZACION} (64 hex)", post)

    post, estado = _verificar_roles_sql()
    add("POL-ACC-01", 3, None, "Roles y permisos creados en SQL Server (script 03)", post, estado)

    ev = pd.DataFrame(f).merge(CATALOGO, on="codigo", how="left")
    return ev[["lote", "fecha_ejecucion", "codigo", "politica", "regla", "responsable", "evaluados",
               "detectados", "tratamiento", "incumplen_despues", "estado"]]