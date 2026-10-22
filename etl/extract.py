"""EXTRACT: lee el dataset v0 (SIN modificar) desde SQL Server o desde el CSV."""
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from .config import CSV_V0, TABLA_STAGING

load_dotenv()


def crear_engine():
    """Construye el engine de SQL Server (Windows Auth o usuario/clave) o usa DB_URL."""
    url_directa = os.getenv("DB_URL")
    if url_directa:
        return create_engine(url_directa)
    servidor = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
    base = os.getenv("DB_NAME", "IntegradorVIII_URP")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    consulta = {"driver": driver, "TrustServerCertificate": "yes"}
    if os.getenv("DB_AUTH", "windows").lower() == "windows":
        consulta["trusted_connection"] = "yes"
        url = URL.create("mssql+pyodbc", host=servidor, database=base, query=consulta)
    else:
        url = URL.create("mssql+pyodbc", username=os.getenv("DB_USER"),
                         password=os.getenv("DB_PASSWORD"), host=servidor,
                         database=base, query=consulta)
    return create_engine(url, fast_executemany=True)


def leer_v0() -> pd.DataFrame:
    modo = os.getenv("SOURCE_MODE", "sql").lower()
    if modo == "sql":
        try:
            df = pd.read_sql(f"SELECT * FROM {TABLA_STAGING}", crear_engine())
            print(f"[EXTRACT] SQL Server -> {len(df):,} filas desde {TABLA_STAGING}")
            return df
        except Exception as e:
            print(f"[EXTRACT] ⚠ No se pudo leer SQL Server ({type(e).__name__}). Uso el CSV local.")
    df = pd.read_csv(CSV_V0, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8")
    print(f"[EXTRACT] CSV -> {len(df):,} filas desde {CSV_V0.name}")
    return df
