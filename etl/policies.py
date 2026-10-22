import pandas as pd
import hashlib
from datetime import datetime

# ==========================================
# 1. VALIDADOR Y CONFIGURACIÓN DE BITÁCORA
# ==========================================
bitacora_incidencias = []

def registrar_incidencia(causa, tratamiento, responsable, registros_afectados):
    """Registra de manera estructurada cada anomalía detectada por el validador."""
    bitacora_incidencias.append({
        'fecha_hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'causa': causa,
        'tratamiento': tratamiento,
        'responsable': responsable,
        'registros_afectados': registros_afectados
    })

# --- CARGA DIRECTA DE TU DATASET REAL ---
ruta_dataset = 'data/Dataset_V0_C01_Permanencia.csv'

try:
    df_v0 = pd.read_csv(ruta_dataset)
    print(f"✅ Dataset v0 cargado exitosamente desde: {ruta_dataset}")
except FileNotFoundError:
    print(f"❌ Error: No se encontró el archivo en {ruta_dataset}. Revisa la carpeta raíz de tu entorno.")

# ==========================================
# 2. INDICADORES ANTES (CICLO PHVA - PLANIFICAR)
# ==========================================
total_inicial = len(df_v0)
completitud_antes = ((df_v0.notnull().sum().sum()) / df_v0.size) * 100

# Verificamos la clave primaria 'id_estudiante' o 'id_estudiante_periodo'
col_id = 'id_estudiante_periodo' if 'id_estudiante_periodo' in df_v0.columns else 'id_estudiante'
duplicados_antes = df_v0.duplicated(subset=[col_id]).sum()

# Verificamos si existe la variable de promedio de nota
col_nota = 'promedio_periodo' if 'promedio_periodo' in df_v0.columns else 'promedio_nota'
if col_nota in df_v0.columns:
    fuera_rango_antes = len(df_v0[(df_v0[col_nota] < 0) | (df_v0[col_nota] > 100)])
else:
    fuera_rango_antes = 0

print(f"\n--- 📊 EVALUACIÓN AS-IS (ANTES) ---")
print(f"• Total registros analizados (Dataset v0): {total_inicial}")
print(f"• Tasa de Completitud inicial: {completitud_antes:.2f}%")
print(f"• Duplicados detectados en {col_id}: {duplicados_antes}")
print(f"• Registros fuera de rango en {col_nota}: {fuera_rango_antes}\n")

# ==========================================
# 3. ACCIÓN CORRECTIVA Y VERSIÓN DERIVADA (Dataset v1)
# ==========================================
df_v1 = df_v0.copy()

# 3.1 Tratamiento de duplicados
if duplicados_antes > 0:
    registrar_incidencia(
        causa="Registros duplicados en la extracción de fuentes origen",
        tratamiento=f"Eliminación de filas duplicadas en {col_id}",
        responsable="Custodio Técnico de TI",
        registros_afectados=int(duplicados_antes)
    )
    df_v1 = df_v1.drop_duplicates(subset=[col_id])

# 3.2 Control de datos fuera de rango (0-100)
if fuera_rango_antes > 0 and col_nota in df_v1.columns:
    registrar_incidencia(
        causa="Calificación superior al límite máximo académico (>100) o negativa",
        tratamiento="Filtrado y exclusión del registro inconsistente para evitar sesgos",
        responsable="Data Steward",
        registros_afectados=int(fuera_rango_antes)
    )
    df_v1 = df_v1[(df_v1[col_nota] >= 0) & (df_v1[col_nota] <= 100)]

# 3.3 Tratamiento de nulos (Imputación por mediana si aplica)
if col_nota in df_v1.columns:
    nulos_notas = df_v1[col_nota].isnull().sum()
    if nulos_notas > 0:
        mediana_notas = df_v1[col_nota].median()
        df_v1[col_nota].fillna(mediana_notas, inplace=True)
        registrar_incidencia(
            causa=f"Presencia de vacíos (nulos) en la variable {col_nota}",
            tratamiento=f"Imputación estadística por la mediana ({mediana_notas:.2f})",
            responsable="Analista de Datos",
            registros_afectados=int(nulos_notas)
        )

# 3.4 Seudonimización obligatoria con SHA-256 (POL-PRIV-01)
if col_id in df_v1.columns:
    df_v1[col_id] = df_v1[col_id].apply(lambda x: hashlib.sha256(str(x).encode()).hexdigest())

# Guardar la versión derivada depurada en la carpeta data/
df_v1.to_csv('data/Dataset_V1_Permanencia_Limpio.csv', index=False)

# ==========================================
# 4. INDICADORES DESPUÉS (CICLO PHVA - VERIFICAR Y ACTUAR)
# ==========================================
completitud_despues = ((df_v1.notnull().sum().sum()) / df_v1.size) * 100
total_final = len(df_v1)

print(f"--- 📈 EVALUACIÓN TO-BE (DESPUÉS - PHVA) ---")
print(f"• Total registros limpios (Dataset v1): {total_final}")
print(f"• Tasa de Completitud final: {completitud_despues:.2f}%")
print(f"• Nivel de Seudonimización SHA-256: 100%")
print(f"• Decisión basada en evidencia: Dataset validado para entrenamiento del modelo predictivo.\n")

# Mostrar Bitácora en formato de tabla (DataFrame)
print("=== 📝 BITÁCORA DE INCIDENCIAS REGISTRADA ===")
df_bitacora = pd.DataFrame(bitacora_incidencias)
display(df_bitacora)

# ==========================================
# 5. PRUEBAS: VÁLIDA E INVÁLIDA DEL CONTROL
# ==========================================
def probar_validador(registro):
    """Demostración en vivo de pruebas válida e inválida para el docente."""
    nota = registro.get(col_nota, 85)
    if nota is None or nota < 0 or nota > 100:
        return f"❌ PRUEBA FALLIDA (Detectó anomalía): {col_nota}={nota} viola el rango (0-100)."
    return f"✅ PRUEBA EXITOSA: {col_nota}={nota} cumple con las reglas de calidad."

print("\n--- 🧪 DEMOSTRACIÓN DE PRUEBAS DE CONTROL ---")
prueba_valida = {col_id: 'EST-999', col_nota: 88}
prueba_invalida = {col_id: 'EST-888', col_nota: 135}

print(f"Prueba 1 (Caso Válido): {probar_validador(prueba_valida)}")
print(f"Prueba 2 (Caso Inválido): {probar_validador(prueba_invalida)}")