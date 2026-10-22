"""
Genera Dataset_V0_C01_Permanencia.csv (10,000 registros sintéticos) con la MISMA
estructura del diccionario del Caso 1 (URP) y con ruido de calidad intencional:
nulos, duplicados, etiquetas no normalizadas, fuera de rango y cargas tardías.

USO:  python data/generar_dataset_v0.py
NOTA: Es un SUSTITUTO. Si tienes el CSV real de 10,000 filas, colócalo en data/
      con el mismo nombre y no ejecutes este script.
"""
import numpy as np, pandas as pd
from pathlib import Path

rng = np.random.default_rng(2026)
N = 10_000

programas = ["Sistemas", "Computación", "Telecomunicaciones", "Industrial", "Civil"]
modalidades = ["Presencial", "Por encuentros", "Virtual"]
ingresos = ["Nuevo ingreso", "Continuidad", "Reingreso", "Traslado"]
asigs = ["Matemática I", "Programación I", "Física I", "Estadística", "Bases de datos"]
becas = ["Beca completa", "Beca parcial", "Sin beca", "Tutoría académica"]
sistemas = ["SIGA", "Moodle", "Bienestar", "Archivo CSV"]

df = pd.DataFrame({
    "programa_academico": rng.choice(programas, N, p=[.23, .17, .21, .21, .18]),
    "modalidad": rng.choice(modalidades, N, p=[.33, .30, .37]),
    "condicion_ingreso": rng.choice(ingresos, N, p=[.30, .50, .12, .08]),
    "asignatura_critica": rng.choice(asigs, N),
    "beca_o_apoyo": rng.choice(becas, N, p=[.12, .20, .50, .18]),
    "sistema_origen": rng.choice(sistemas, N, p=[.40, .30, .10, .20]),
})

meses = pd.date_range("2025-01-01", "2026-06-01", freq="MS")
df["fecha_inicio_periodo"] = [m + pd.Timedelta(days=int(d)) for m, d in
                              zip(rng.choice(meses, N), rng.integers(0, 28, N))]

base = rng.normal(0, 1, N)                       # "capacidad" latente
virtual = (df.modalidad == "Virtual").astype(int)
nuevo = (df.condicion_ingreso == "Nuevo ingreso").astype(int)
df["promedio_periodo"] = np.clip(72 + 9 * base + rng.normal(0, 5, N) - 2 * virtual, 48, 96).round(1)
df["asistencia_pct"] = np.clip(78 + 8 * base + rng.normal(0, 9, N) - 4 * virtual, 35, 100).round(1)
df["accesos_campus_virtual"] = np.clip(70 + 25 * base + rng.normal(0, 20, N) + 15 * virtual, 0, 180).round().astype(int)
df["asignaturas_reprobadas"] = np.clip(rng.poisson(np.clip(1.3 - 0.9 * base, 0.05, 4)), 0, 5)

z = (-1.05
     - 0.060 * (df.promedio_periodo - 72)
     - 0.030 * (df.asistencia_pct - 78)
     - 0.008 * (df.accesos_campus_virtual - 70)
     + 0.45 * df.asignaturas_reprobadas
     + 0.30 * virtual + 0.35 * nuevo
     + 0.25 * (df.condicion_ingreso == "Reingreso")
     - 0.90 * (df.beca_o_apoyo == "Beca completa")
     - 0.45 * (df.beca_o_apoyo == "Beca parcial")
     - 0.30 * (df.beca_o_apoyo == "Tutoría académica")
     + 0.30 * (df.programa_academico == "Computación")
     + 0.25 * (df.asignatura_critica == "Matemática I")
     + rng.normal(0, 0.6, N))
df["no_continua_siguiente_periodo"] = (rng.random(N) < 1 / (1 + np.exp(-z))).astype(float)

df["autorizacion_uso_analitico"] = rng.choice(["Sí", "No"], N, p=[.96, .04])
retraso = np.where(rng.random(N) < .90, rng.integers(0, 6, N), rng.integers(8, 45, N))
df["fecha_carga"] = df["fecha_inicio_periodo"] + pd.to_timedelta(retraso, unit="D")
df.insert(0, "id_estudiante_periodo", [f"EP-{i:06d}" for i in range(1, N + 1)])

# ---------------- RUIDO INTENCIONAL DE CALIDAD (dataset v0) ----------------
def nulos(col, frac):
    df.loc[rng.choice(N, int(N * frac), replace=False), col] = np.nan
for c, f in [("modalidad", .025), ("promedio_periodo", .03), ("asistencia_pct", .03),
             ("accesos_campus_virtual", .02), ("asignaturas_reprobadas", .015),
             ("beca_o_apoyo", .02), ("condicion_ingreso", .01),
             ("no_continua_siguiente_periodo", .018)]:
    nulos(c, f)

for col, val in [("asignatura_critica", "Física I"), ("asignatura_critica", "Matemática I"),
                 ("programa_academico", "Civil"), ("modalidad", "Virtual")]:
    idx = df.index[df[col] == val]
    pick = rng.choice(idx, max(1, int(len(idx) * .012)), replace=False)
    df.loc[pick, col] = [rng.choice([val.upper(), val.lower(), f" {val} "]) for _ in pick]

def fuera(col, vals, frac):
    idx = rng.choice(N, int(N * frac), replace=False)
    df.loc[idx, col] = rng.choice(vals, len(idx))
fuera("promedio_periodo", [0, 100, 105.5, 120, -1, 15], .012)
fuera("asistencia_pct", [0, 110, 150, 5, -3], .010)
fuera("accesos_campus_virtual", [-5, 240, 400, 999], .008)
fuera("asignaturas_reprobadas", [7, 8, 12, -1], .006)

df.loc[rng.choice(N, 150, replace=False), "autorizacion_uso_analitico"] = "SI"
df.loc[rng.choice(N, 60, replace=False), "autorizacion_uso_analitico"] = np.nan

dup = df.sample(int(N * .02), random_state=7)                 # duplicados exactos
df = pd.concat([df.iloc[: N - len(dup)], dup], ignore_index=True)
df = df.sample(frac=1, random_state=11).reset_index(drop=True)

# ---------------- EXPORTACIÓN (mismo formato que usa el BULK INSERT) ----------------
COLS = ["id_estudiante_periodo","fecha_inicio_periodo","programa_academico","modalidad",
        "condicion_ingreso","asignatura_critica","promedio_periodo","asistencia_pct",
        "accesos_campus_virtual","asignaturas_reprobadas","beca_o_apoyo","sistema_origen",
        "no_continua_siguiente_periodo","autorizacion_uso_analitico","fecha_carga"]
out = df[COLS].copy()   # el BULK INSERT es posicional: el orden debe coincidir con la tabla
for c in ["accesos_campus_virtual", "asignaturas_reprobadas"]:
    out[c] = pd.to_numeric(out[c]).round().astype("Int64")
out["no_continua_siguiente_periodo"] = out["no_continua_siguiente_periodo"].map(
    lambda v: "" if pd.isna(v) else f"{v:.1f}")      # '1.0' / '0.0' / vacío
out["fecha_inicio_periodo"] = pd.to_datetime(out["fecha_inicio_periodo"]).dt.strftime("%Y-%m-%d")
out["fecha_carga"] = pd.to_datetime(out["fecha_carga"]).dt.strftime("%Y-%m-%d")

ruta = Path(__file__).parent / "Dataset_V0_C01_Permanencia.csv"
out.to_csv(ruta, index=False, encoding="utf-8", lineterminator="\n")
print(f"OK -> {ruta}  filas={len(out)}")
