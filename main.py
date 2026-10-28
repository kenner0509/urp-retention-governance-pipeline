"""Pipeline: Extract → Diagnóstico → Gobierno (políticas) → Features → KPI-09 → Load (SQL Server + CSV)."""
import os
from etl.extract import leer_v0
from etl.transform import diagnosticar_calidad, aplicar_gobierno
from etl.features import construir_features
from etl.kpi09 import calcular_kpi09, detalle_kpi09
from etl.policies import CATALOGO, aplicar_seudonimizacion
from etl.validador_phva import ejecutar_validacion
from etl.load import cargar


def ejecutar():
    print("=" * 62, "\n PIPELINE MINERÍA DE DATOS – URP · Caso 1 · KPI-09\n", "=" * 62, sep="")
    v0 = leer_v0()
    diag = diagnosticar_calidad(v0)
    limpio, rechazos, pendientes = aplicar_gobierno(v0)          # POL-CAL-01, POL-SEG-01, POL-USO-01
    v1_real = construir_features(limpio)
    v1 = aplicar_seudonimizacion(v1_real)                          # POL-PRIV-01
    pend = aplicar_seudonimizacion(construir_features(pendientes))
    rechazos_s = aplicar_seudonimizacion(rechazos)
    diag_s = aplicar_seudonimizacion(diag)

    rep = ejecutar_validacion(v0, diag, v1_real, v1, len(pendientes))    # bitácora + PHVA + pruebas + evidencia
    kpi9, det9 = calcular_kpi09(v1), detalle_kpi09(v1)
    print("\n── KPI-09 ──\n", kpi9.drop(columns=["Nota"]).T.to_string(header=False))
    print("\n── Evidencia de políticas programadas ──\n",
          rep["evidencia"][["codigo", "evaluados", "detectados", "incumplen_despues", "estado"]].to_string(index=False), "\n")

    cargar({"dw_permanencia_predictivo": v1, "dw_permanencia_pendientes": pend,
            "stg_rechazos_calidad": rechazos_s, "dw_diagnostico_calidad": diag_s,
            "dw_kpi_resumen": kpi9, "dw_kpi09_detalle": det9,
            "dw_politicas_catalogo": CATALOGO, "dw_politicas_evidencia": rep["evidencia"],
            "dw_bitacora_incidencias": rep["bitacora"], "dw_phva_indicadores": rep["phva"],
            "dw_pruebas_control": rep["pruebas"]},
           a_sql=os.getenv("LOAD_TO_SQL", "1") == "1")
    print("🎉 Listo. Siguiente: ejecuta sql/03_politicas_acceso.sql en SSMS y abre modelos_permanencia.ipynb")


if __name__ == "__main__":
    ejecutar()