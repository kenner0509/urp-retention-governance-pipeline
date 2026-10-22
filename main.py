"""Orquesta el pipeline: Extract -> Diagnóstico -> Transform -> Features -> KPIs -> Load."""
import os
from etl.extract import leer_v0
from etl.transform import diagnosticar_calidad, aplicar_gobierno
from etl.features import construir_features
from etl.kpis import calcular_kpis
from etl.load import cargar


def ejecutar():
    print("=" * 60, "\n PIPELINE MINERÍA DE DATOS – URP (Caso 1: Permanencia)\n", "=" * 60, sep="")
    v0 = leer_v0()
    diag = diagnosticar_calidad(v0)
    limpio, rechazos, pendientes = aplicar_gobierno(v0)
    v1 = construir_features(limpio)
    pend = construir_features(pendientes)
    kpis = calcular_kpis(v0, diag, v1)
    print("\n", kpis[["KPI", "Nombre", "Valor", "Meta", "Estado"]].to_string(index=False), "\n")
    cargar({"dw_permanencia_predictivo": v1,
            "dw_permanencia_pendientes": pend,
            "stg_rechazos_calidad": rechazos,
            "dw_diagnostico_calidad": diag,
            "dw_kpi_resumen": kpis},
           a_sql=os.getenv("LOAD_TO_SQL", "1") == "1")
    print("🎉 Listo. Siguiente paso: jupyter lab -> modelos_permanencia.ipynb")


if __name__ == "__main__":
    ejecutar()
