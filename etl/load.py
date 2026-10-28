"""LOAD: guarda resultados en CSV (siempre) y en SQL Server (si hay conexión)."""
from .config import DIR_OUT
from .extract import crear_engine


def guardar_tabla(nombre, df, a_sql=True):
    """Guarda UNA tabla (CSV + SQL). Usado también por el cuaderno para el scoring."""
    df.to_csv(DIR_OUT / f"{nombre}.csv", index=False, encoding="utf-8")
    if not a_sql:
        return False
    try:
        df.to_sql(nombre, crear_engine(), if_exists="replace", index=False)
        return True
    except Exception as e:
        print(f"[LOAD] ⚠ {nombre}: no se cargó a SQL Server ({type(e).__name__}). Queda el CSV.")
        return False


def cargar(tablas: dict, a_sql=True):
    ok = [n for n, d in tablas.items() if guardar_tabla(n, d, a_sql)]
    print(f"[LOAD] CSV guardados en {DIR_OUT}")
    if ok:
        print("[LOAD] ✅ Tablas en SQL Server:", ", ".join(ok))