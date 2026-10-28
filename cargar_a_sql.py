"""Carga data/Dataset_V0_C01_Permanencia.csv a SQL Server SIN usar BULK INSERT
(evita problemas de ruta y permisos). Crea la BD y la tabla staging si no existen.

USO:  python cargar_a_sql.py
"""
import os
import pandas as pd
from sqlalchemy import text
from etl.config import CSV_V0, TABLA_STAGING, DATABASE
from etl.extract import crear_engine

DDL = f"""
CREATE TABLE {TABLA_STAGING} (
    id_estudiante_periodo VARCHAR(50), fecha_inicio_periodo DATE, programa_academico VARCHAR(100),
    modalidad VARCHAR(50), condicion_ingreso VARCHAR(50), asignatura_critica VARCHAR(100),
    promedio_periodo DECIMAL(6,2), asistencia_pct DECIMAL(6,2), accesos_campus_virtual INT,
    asignaturas_reprobadas INT, beca_o_apoyo VARCHAR(100), sistema_origen VARCHAR(50),
    no_continua_siguiente_periodo VARCHAR(10) NULL, autorizacion_uso_analitico VARCHAR(50), fecha_carga DATE)
"""


def main():
    base = os.getenv("DB_NAME", DATABASE)
    if not os.getenv("DB_URL"):   # SQL Server: crear la BD si no existe (conexión a master, sin transacción)
        with crear_engine("master").connect().execution_options(isolation_level="AUTOCOMMIT") as c:
            c.execute(text(f"IF DB_ID('{base}') IS NULL CREATE DATABASE [{base}]"))
        print(f"✅ Base de datos {base} lista")
    df = pd.read_csv(CSV_V0, dtype=str, keep_default_na=False, na_values=[""])
    for c in ["promedio_periodo", "asistencia_pct"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["accesos_campus_virtual", "asignaturas_reprobadas"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").round().astype("Int64")
    for c in ["fecha_inicio_periodo", "fecha_carga"]:
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    eng = crear_engine()
    with eng.begin() as c:
        c.execute(text(f"DROP TABLE IF EXISTS {TABLA_STAGING}"))
        c.execute(text(DDL))
    df.to_sql(TABLA_STAGING, eng, if_exists="append", index=False, chunksize=1000)
    with eng.connect() as c:
        n = c.execute(text(f"SELECT COUNT(*) FROM {TABLA_STAGING}")).scalar()
    print(f"✅ {TABLA_STAGING}: {n:,} filas cargadas (esperado 10,000)")


if __name__ == "__main__":
    main()