"""TRANSFORM: diagnóstico de calidad (perfilado) + reglas de gobierno de datos.

Principios: el v0 nunca se modifica; todo cambio queda en una versión derivada (v1)
con banderas de trazabilidad. La imputación se hace dentro del modelo (sin fuga)."""
import re, unicodedata
import numpy as np
import pandas as pd
from .config import CATALOGOS, RANGOS, CAMPOS_CRITICOS, SLA_DIAS_CARGA

NUM = list(RANGOS)


def _clave(s):
    if pd.isna(s):
        return None
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().casefold()


def tipificar(df_v0: pd.DataFrame) -> pd.DataFrame:
    """Convierte tipos sin corregir valores (valores no convertibles -> NaN)."""
    df = df_v0.copy()
    for c in NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["no_continua_siguiente_periodo"] = pd.to_numeric(df["no_continua_siguiente_periodo"], errors="coerce")
    for c in ["fecha_inicio_periodo", "fecha_carga"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def diagnosticar_calidad(df_v0: pd.DataFrame) -> pd.DataFrame:
    """Marca por registro cada violación de calidad (insumo de KPI-01/04/05/06)."""
    d = tipificar(df_v0)
    diag = pd.DataFrame(index=d.index)
    diag["id_estudiante_periodo"] = d["id_estudiante_periodo"]
    diag["e_duplicado"] = d.duplicated(keep="first")
    diag["e_id_repetido"] = d["id_estudiante_periodo"].duplicated(keep="first")
    for c, (lo, hi) in RANGOS.items():
        diag[f"e_rango_{c}"] = d[c].notna() & ((d[c] < lo) | (d[c] > hi))
    for c, cat in CATALOGOS.items():
        v = df_v0[c]
        diag[f"e_catalogo_{c}"] = v.notna() & ~v.isin(cat)        # incluye mayúsculas/espacios
    diag["e_fecha_incoherente"] = d["fecha_carga"] < d["fecha_inicio_periodo"]
    diag["e_carga_tardia"] = (d["fecha_carga"] - d["fecha_inicio_periodo"]).dt.days > SLA_DIAS_CARGA
    diag["e_nulo_critico"] = d[CAMPOS_CRITICOS].isna().any(axis=1)
    diag["e_sin_resultado"] = d["no_continua_siguiente_periodo"].isna()
    diag["e_sin_autorizacion"] = ~df_v0["autorizacion_uso_analitico"].map(_clave).isin(["si"])
    # Validación primaria (KPI-01): errores de esquema/validación al ingresar
    primaria = ["e_duplicado"] + [c for c in diag if c.startswith(("e_rango_", "e_catalogo_"))] + ["e_fecha_incoherente"]
    diag["falla_validacion_primaria"] = diag[primaria].any(axis=1)
    # Error de calidad (KPI-04): precisión + consistencia + completitud
    calidad = primaria + ["e_nulo_critico"]
    diag["tiene_error_calidad"] = diag[calidad].any(axis=1)
    return diag


def aplicar_gobierno(df_v0: pd.DataFrame):
    """Devuelve (df_limpio_v1, df_rechazos, df_pendientes_scoring)."""
    print("[TRANSFORM] Aplicando políticas de gobierno de datos...")
    d = tipificar(df_v0)
    rech = []

    def rechazar(mask, motivo):
        if mask.any():
            r = d[mask].copy(); r["motivo_rechazo"] = motivo; rech.append(r)
        return d[~mask]

    # POL-CAL-01 duplicados exactos / id repetido (se conserva la primera ocurrencia)
    d = rechazar(d.duplicated(keep="first"), "POL-CAL-01 registro duplicado")
    d = rechazar(d["id_estudiante_periodo"].duplicated(keep="first"), "POL-CAL-01 id repetido")
    # POL-SEG-01 / ética: solo registros con autorización de uso analítico
    ok_aut = d["autorizacion_uso_analitico"].map(_clave).isin(["si"])
    d = rechazar(~ok_aut, "POL-SEG-01 sin autorización de uso analítico")
    d = d.copy()

    # POL-USO-01 normalización de catálogos (case/espacios/acentos) + categoría inválida
    for c, cat in CATALOGOS.items():
        mapa = {_clave(x): x for x in cat}
        original = d[c]
        d[c] = original.map(_clave).map(mapa)
        d[f"flag_normalizado_{c}"] = original.notna() & d[c].notna() & (original != d[c])
    # POL-CAL-02 fuera de rango -> NaN (+ bandera). La imputación va dentro del modelo.
    for c, (lo, hi) in RANGOS.items():
        fuera = d[c].notna() & ((d[c] < lo) | (d[c] > hi))
        d[f"flag_fuera_rango_{c}"] = fuera
        d.loc[fuera, c] = np.nan
    # POL-CAL-03 coherencia temporal
    d["dias_carga"] = (d["fecha_carga"] - d["fecha_inicio_periodo"]).dt.days
    d.loc[d["dias_carga"] < 0, "dias_carga"] = np.nan
    d["flag_carga_tardia"] = d["dias_carga"] > SLA_DIAS_CARGA
    for c in ["modalidad", "condicion_ingreso", "beca_o_apoyo"]:
        d[c] = d[c].fillna("Sin dato")           # categoría explícita (POL-TRA-01)

    # Variable de resultado no consolidada -> no entrena; se usa para scoring
    pend = d[d["no_continua_siguiente_periodo"].isna()].copy()
    limpio = d[d["no_continua_siguiente_periodo"].notna()].copy()
    limpio["no_continua_siguiente_periodo"] = limpio["no_continua_siguiente_periodo"].astype(int)
    rechazos = pd.concat(rech, ignore_index=True) if rech else pd.DataFrame()
    print(f"[TRANSFORM] v0={len(df_v0):,} | limpio={len(limpio):,} | "
          f"rechazos={len(rechazos):,} | pendientes (sin resultado)={len(pend):,}")
    return limpio.reset_index(drop=True), rechazos, pend.reset_index(drop=True)
