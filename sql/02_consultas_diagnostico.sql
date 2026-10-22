-- Consultas de perfilado rápido sobre el dataset v0 (SQL Server)
USE IntegradorVIII_URP;
GO
-- Nulos por columna
SELECT
  SUM(CASE WHEN modalidad IS NULL THEN 1 ELSE 0 END)               AS nulos_modalidad,
  SUM(CASE WHEN promedio_periodo IS NULL THEN 1 ELSE 0 END)        AS nulos_promedio,
  SUM(CASE WHEN asistencia_pct IS NULL THEN 1 ELSE 0 END)          AS nulos_asistencia,
  SUM(CASE WHEN no_continua_siguiente_periodo IS NULL THEN 1 ELSE 0 END) AS nulos_resultado
FROM stg_PermanenciaEstudiantil;

-- Duplicados exactos por id
SELECT id_estudiante_periodo, COUNT(*) AS veces
FROM stg_PermanenciaEstudiantil GROUP BY id_estudiante_periodo HAVING COUNT(*) > 1;

-- Fuera de rango (rangos del diccionario)
SELECT COUNT(*) AS fuera_rango FROM stg_PermanenciaEstudiantil
WHERE promedio_periodo NOT BETWEEN 48 AND 96 OR asistencia_pct NOT BETWEEN 35 AND 100
   OR accesos_campus_virtual NOT BETWEEN 0 AND 180 OR asignaturas_reprobadas NOT BETWEEN 0 AND 5;

-- Etiquetas no normalizadas
SELECT modalidad, COUNT(*) n FROM stg_PermanenciaEstudiantil GROUP BY modalidad ORDER BY 1;
SELECT asignatura_critica, COUNT(*) n FROM stg_PermanenciaEstudiantil GROUP BY asignatura_critica ORDER BY 1;

-- Cargas tardías (> 7 días)
SELECT COUNT(*) AS cargas_tardias FROM stg_PermanenciaEstudiantil
WHERE DATEDIFF(DAY, fecha_inicio_periodo, fecha_carga) > 7;
