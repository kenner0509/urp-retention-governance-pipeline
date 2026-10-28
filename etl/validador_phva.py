"""Validación, bitácora y auditoría (ciclo PHVA) — reporte legible para consola o notebook.

Antes era un script que se ejecutaba al abrirlo y SOBRESCRIBÍA outputs/dw_permanencia_predictivo.csv
(dejándolo sin las columnas que necesita el cuaderno). Ahora solo calcula y muestra; guardar lo hace main.py.

USO desde la consola:   python -m etl.validador_phva
"""
from .policies import (generar_bitacora, indicadores_phva, ejecutar_pruebas_control, generar_evidencia)


def mostrar(df, titulo=None):
    """display() en Jupyter; print() en consola."""
    if titulo:
        print(f"\n=== {titulo} ===")
    try:
        from IPython import get_ipython
        if get_ipython().__class__.__name__ == "ZMQInteractiveShell":      # dentro de un notebook
            from IPython.display import display
            display(df)
            return
    except Exception:
        pass
    print(df.to_string(index=False, max_colwidth=70))


def ejecutar_validacion(v0, diag, v1_real, v1_seud, n_pendientes, verbose=True):
    bitacora = generar_bitacora(v0, diag, n_pendientes, len(v1_seud))
    phva = indicadores_phva(v0, diag, v1_real, v1_seud)
    pruebas = ejecutar_pruebas_control()
    evidencia = generar_evidencia(v0, diag, v1_real, v1_seud)
    if verbose:
        print("=" * 62, "\n  VALIDACIÓN, BITÁCORA Y AUDITORÍA URP (CICLO PHVA)\n", "=" * 62, sep="")
        mostrar(phva[["indicador", "antes", "despues", "meta", "estado"]], "INDICADORES ANTES → DESPUÉS")
        mostrar(bitacora[["politica", "causa", "responsable", "registros_afectados"]], "BITÁCORA DE INCIDENCIAS")
        mostrar(pruebas[["prueba", "datos", "resultado_control", "aprobada"]], "PRUEBAS VÁLIDA E INVÁLIDA DEL CONTROL")
    return {"bitacora": bitacora, "phva": phva, "pruebas": pruebas, "evidencia": evidencia}


if __name__ == "__main__":
    from .extract import leer_v0
    from .transform import diagnosticar_calidad, aplicar_gobierno
    from .features import construir_features
    from .policies import aplicar_seudonimizacion
    v0 = leer_v0()
    diag = diagnosticar_calidad(v0)
    limpio, rechazos, pend = aplicar_gobierno(v0)
    v1 = construir_features(limpio)
    ejecutar_validacion(v0, diag, v1, aplicar_seudonimizacion(v1), len(pend))