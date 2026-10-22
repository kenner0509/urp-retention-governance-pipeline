"""LOAD: guarda resultados en CSV (siempre) y en SQL Server (si hay conexión)."""
from .config import DIR_OUT
from .extract import crear_engine


def cargar(tablas: dict, a_sql=True):
    for nombre, df in tablas.items():
        df.to_csv(DIR_OUT / f"{nombre}.csv", index=False, encoding="utf-8")
    print(f"[LOAD] CSV guardados en {DIR_OUT}")
    if not a_sql:
        return
    try:
        eng = crear_engine()
        for nombre, df in tablas.items():
            df.to_sql(nombre, eng, if_exists="replace", index=False)
        print("[LOAD] ✅ Tablas cargadas en SQL Server:", ", ".join(tablas))
    except Exception as e:
        print(f"[LOAD] ⚠ No se cargó a SQL Server ({type(e).__name__}: {str(e)[:120]}). Quedan los CSV.")
