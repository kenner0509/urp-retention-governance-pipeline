# -*- coding: utf-8 -*-
"""
Módulo de Gobernanza de Datos y Validación de Políticas de Gobierno (URP)
Autor: Kenner Alexander Ruiz Hernández (#22909546)
"""

import os
import hashlib
import pandas as pd
from .config import CATALOGOS, RANGOS, CAMPOS_CRITICOS, SLA_DIAS_CARGA


def validar_politicas_dataset(df: pd.DataFrame) -> dict:
    """
    Ejecuta el perfilado y verificación de cumplimiento normativo (POL-CAL, POL-OPO, POL-SEG)
    sobre el dataset analítico procesado.
    """
    resultados = {}
    
    # 1. Validación de Rangos Numéricos (POL-CAL-02)
    for col, (min_v, max_v) in RANGOS.items():
        if col in df.columns:
            fuera_rango = df[(df[col].notna()) & ((df[col] < min_v) | (df[col] > max_v))].shape[0]
            resultados[f"rango_{col}"] = {
                "fallos": int(fuera_rango), 
                "estado": "FAIL" if fuera_rango > 0 else "OK"
            }

    # 2. Validación de Dominios y Catálogos Oficiales (POL-USO-01)
    for col, valores_validos in CATALOGOS.items():
        if col in df.columns:
            # Evalúa cuántos valores no nulos no están en el catálogo oficial
            invalidos = df[(df[col].notna()) & (~df[col].isin(valores_validos))].shape[0]
            resultados[f"catalogo_{col}"] = {
                "fallos": int(invalidos), 
                "estado": "FAIL" if invalidos > 0 else "OK"
            }

    # 3. Nivel de Seudonimización y Privacidad (POL-SEG-03 / SHA-256)
    if "id_estudiante" in df.columns:
        # Verifica cuántos IDs tienen el formato de huella hash SHA-256 (64 caracteres hexadecimales)
        hasheados = df["id_estudiante"].astype(str).str.match(r"^[a-fA-F0-9]{64}$").sum()
        total_regs = len(df)
        pct_seudonimizacion = (hasheados / total_regs) * 100 if total_regs > 0 else 0.0
        
        resultados["nivel_seudonimizacion"] = {
            "valor_pct": float(pct_seudonimizacion),
            "estado": "OK" if pct_seudonimizacion == 100.0 else "REVISAR"
        }
    else:
        resultados["nivel_seudonimizacion"] = {
            "valor_pct": 0.0,
            "estado": "N/A (Columna id_estudiante ausente)"
        }

    return resultados