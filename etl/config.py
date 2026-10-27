"""Parámetros centrales del proyecto (reglas de negocio, catálogos y supuestos)."""
from pathlib import Path
from sqlalchemy import create_engine

RAIZ = Path(__file__).resolve().parent.parent
DIR_DATA = RAIZ / "data"
DIR_OUT = RAIZ / "outputs"
DIR_OUT.mkdir(exist_ok=True)

CSV_V0 = DIR_DATA / "Dataset_V0_C01_Permanencia.csv"
TABLA_STAGING = "stg_PermanenciaEstudiantil"

# ---------------- Configuración de Conexión a SQL Server ----------------
SERVER = 'DESKTOP-G3NSGKO\\SQLEXPRESS'
DATABASE = 'IntegradorVIII_URP'
DRIVER = 'ODBC Driver 18 for SQL Server' # O Driver 17 según tengas instalado

def obtener_conexion_engine():
    """Crea y retorna el engine de SQLAlchemy para conectar con SQL Server."""
    connection_string = (
        f"mssql+pyodbc://@{SERVER}/{DATABASE}?"
        f"driver={DRIVER}&trusted_connection=yes&encrypt=no"
    )
    return create_engine(connection_string)

# ---------------- Catálogos oficiales (diccionario del expediente) ----------------
CATALOGOS = {
    "programa_academico": ["Sistemas", "Computación", "Telecomunicaciones", "Industrial", "Civil"],
    "modalidad": ["Presencial", "Por encuentros", "Virtual"],
    "condicion_ingreso": ["Nuevo ingreso", "Continuidad", "Reingreso", "Traslado"],
    "asignatura_critica": ["Matemática I", "Programación I", "Física I", "Estadística", "Bases de datos"],
    "beca_o_apoyo": ["Beca completa", "Beca parcial", "Sin beca", "Tutoría académica"],
    "sistema_origen": ["SIGA", "Moodle", "Bienestar", "Archivo CSV"],
}

# ---------------- Rangos esperados (diccionario) ----------------
RANGOS = {
    "promedio_periodo": (48, 96),
    "asistencia_pct": (35, 100),
    "accesos_campus_virtual": (0, 180),
    "asignaturas_reprobadas": (0, 5),
}

# Campos críticos para completitud (KPI-06)
CAMPOS_CRITICOS = ["modalidad", "condicion_ingreso", "beca_o_apoyo", "promedio_periodo",
                   "asistencia_pct", "accesos_campus_virtual", "asignaturas_reprobadas",
                   "autorizacion_uso_analitico"]

# ---------------- PARÁMETROS DE GOBIERNO Y POLÍTICAS (POL-SEG / POL-CAL) ----------------
ALGORITMO_SEUDONIMIZACION = "SHA-256"
UMBRAL_MINIMO_SEUDONIMIZACION_PCT = 100.0

# ---------------- SUPUESTOS (documentar y validar con la URP) ----------------
SLA_DIAS_CARGA = 7          # KPI-05: carga oportuna si fecha_carga - fecha_inicio <= 7 días
UMBRAL_INACTIVIDAD = 25     # KPI-08: accesos por periodo <= 25 => "inactivo" (proxy; la ficha pide 7 días sin login)
NOTA_MINIMA_APROBACION = 60 # riesgo académico: promedio < 60
ASISTENCIA_MINIMA = 70      # riesgo académico: asistencia < 70 %
TASA_REF_NO_CONTINUIDAD = 0.18   # referencia anual de programas comparables (expediente)
META_COMPLETITUD_INSTITUCIONAL = 0.97

SEMILLA = 42