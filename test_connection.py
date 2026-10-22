"""Prueba la conexión a SQL Server usando el .env"""
from sqlalchemy import text
from etl.extract import crear_engine
try:
    with crear_engine().connect() as c:
        print("✅ Conectado:", c.execute(text("SELECT @@VERSION")).scalar()[:80])
        n = c.execute(text("SELECT COUNT(*) FROM stg_PermanenciaEstudiantil")).scalar()
        print(f"✅ stg_PermanenciaEstudiantil tiene {n:,} filas")
except Exception as e:
    print("❌ Falló la conexión:\n", e)
    print("\nRevisa: 1) servicio SQL Server activo  2) DB_SERVER/DB_NAME en .env  3) ODBC Driver instalado  4) que ejecutaste el script SQL")
