# Guía de instalación y ejecución – Minería de Datos URP (Caso 1)

> Tu `INSTALCION.MD` original era una plantilla de otro proyecto (SkyTravel + PostgreSQL).
> Tu script `Import_URP_Data.sql` es **SQL Server**, así que esta guía usa **SQL Server + Python**.

## 0. Qué vas a tener al final
```
urp_permanencia/
├─ data/            Dataset_V0_C01_Permanencia.csv (+ generador sintético)
├─ sql/             01_importar_v0_CORREGIDO.sql, 02_consultas_diagnostico.sql
├─ etl/             extract · transform · features · kpis · load · config
├─ main.py          ejecuta todo el pipeline
├─ modelos_permanencia.ipynb   análisis de minería (CRISP-DM)
└─ outputs/         tablas, figuras, scoring e informe HTML
```

## 1. Instalar Python (Windows)
1. Descarga **Python 3.11** de https://www.python.org/downloads/
2. En el instalador marca ✅ **Add Python to PATH**.
3. Verifica en CMD: `python --version` (3.10 o superior) y `pip --version`.

## 2. Instalar SQL Server y herramientas
1. **SQL Server Express** (gratis) y **SSMS** (SQL Server Management Studio).
2. **ODBC Driver 17 (o 18) for SQL Server** (necesario para que Python se conecte).
3. En SSMS conéctate a `localhost\SQLEXPRESS` con *Windows Authentication* (si funciona, ya está bien).

## 3. Preparar el proyecto
```bat
cd C:\Proyectos\urp_permanencia
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python verify_installation.py
```
Debes ver ✅ en todas las librerías. (Si `pyodbc` falla, instala antes *Microsoft C++ Build Tools* o usa Python 3.11.)

## 4. Datos del Caso 1
* **Si tienes el CSV real** (10,000 filas): cópialo a `data\Dataset_V0_C01_Permanencia.csv`.
* **Si no lo tienes**: `python data\generar_dataset_v0.py` (crea un sustituto sintético de 10,000 filas con la misma estructura y ruido de calidad).

El orden de columnas del CSV debe ser el de la tabla (el BULK INSERT es posicional):
`id_estudiante_periodo, fecha_inicio_periodo, programa_academico, modalidad, condicion_ingreso, asignatura_critica, promedio_periodo, asistencia_pct, accesos_campus_virtual, asignaturas_reprobadas, beca_o_apoyo, sistema_origen, no_continua_siguiente_periodo, autorizacion_uso_analitico, fecha_carga`

## 5. Cargar el dataset v0 a SQL Server
1. Copia el CSV a una carpeta **simple y accesible**, p. ej. `C:\Datos\Dataset_V0_C01_Permanencia.csv`
   (evita `C:\Users\...`: el servicio de SQL Server suele no tener permiso → *error 5, Access denied*).
2. Abre `sql\01_importar_v0_CORREGIDO.sql` en SSMS.
3. Cambia la línea `DECLARE @ruta ... = N'C:\Users\Luis\...'` por tu ruta.
4. Ejecuta todo (F5). Debe mostrar **TotalRegistros = 10000**.

**Errores corregidos respecto a tu script original:** columna objetivo como `VARCHAR(10)` desde el inicio (el CSV trae `1.0/0.0`), y se eliminó el `TRUNCATE` final que vaciaba la tabla.

## 6. Configurar la conexión
```bat
copy .env.example .env
notepad .env
```
Ajusta `DB_SERVER` (ej. `localhost\SQLEXPRESS` o `NOMBREPC\SQLEXPRESS`), `DB_NAME=IntegradorVIII_URP` y `DB_DRIVER` (17 o 18).
Para trabajar **sin SQL Server** pon `SOURCE_MODE=csv` y `LOAD_TO_SQL=0`.
```bat
python test_connection.py
```

## 7. Ejecutar el pipeline
```bat
python main.py
```
Hace: extracción → diagnóstico de calidad → gobierno (v0→v1) → variables derivadas → **KPI-01…10** → carga a SQL Server (`dw_*`) y CSV en `outputs\`.

## 8. Análisis de minería de datos
```bat
jupyter lab
```
Abre `modelos_permanencia.ipynb` → menú **Run ▸ Run All Cells**. Incluye calidad, KPIs, EDA, 9 modelos, validación fuera de tiempo, importancia, K-Means, Apriori y scoring (`outputs\scoring_pendientes.csv`).

## 9. Problemas frecuentes
| Síntoma | Solución |
|---|---|
| `Data source name not found` / `driver` | Instala ODBC Driver y pon el nombre exacto en `DB_DRIVER` |
| `Login failed` | Usa `DB_AUTH=windows` o `DB_AUTH=sql` con `DB_USER/DB_PASSWORD` |
| `Cannot bulk load ... error 5` | Mueve el CSV a `C:\Datos\` y revisa la ruta |
| `Bulk load data conversion error` | El CSV no coincide con el orden/tipos de columnas (ver sección 4) |
| `ModuleNotFoundError` | Activa el entorno: `venv\Scripts\activate` e instala `requirements.txt` |
| El notebook no encuentra `outputs\...csv` | Ejecuta antes `python main.py` y abre Jupyter desde la carpeta del proyecto |
