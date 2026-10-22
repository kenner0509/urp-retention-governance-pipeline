-- =====================================================================
-- Carga del Dataset v0 – Caso 1 URP (SQL Server)  |  VERSIÓN CORREGIDA
-- Cambios vs. tu script original:
--  1) La columna no_continua_siguiente_periodo es VARCHAR(10) desde el inicio
--     (el CSV trae '1.0' / '0.0' / vacío; con INT el BULK INSERT falla).
--  2) Se eliminó el TRUNCATE final que dejaba la tabla VACÍA.
--  3) Orden lógico: crear BD -> DROP/CREATE -> BULK INSERT -> verificar.
-- ANTES DE EJECUTAR: cambia @ruta por la ruta real del CSV en el equipo donde corre SQL Server.
-- =====================================================================
IF DB_ID('IntegradorVIII_URP') IS NULL CREATE DATABASE IntegradorVIII_URP;
GO
USE IntegradorVIII_URP;
GO

DROP TABLE IF EXISTS stg_PermanenciaEstudiantil;
GO
CREATE TABLE stg_PermanenciaEstudiantil (
    id_estudiante_periodo          VARCHAR(50),
    fecha_inicio_periodo           DATE,
    programa_academico             VARCHAR(100),
    modalidad                      VARCHAR(50),
    condicion_ingreso              VARCHAR(50),
    asignatura_critica             VARCHAR(100),
    promedio_periodo               DECIMAL(6,2),   -- amplio a propósito: admite valores fuera de rango (105.5, -1...)
    asistencia_pct                 DECIMAL(6,2),
    accesos_campus_virtual         INT,
    asignaturas_reprobadas         INT,
    beca_o_apoyo                   VARCHAR(100),
    sistema_origen                 VARCHAR(50),
    no_continua_siguiente_periodo  VARCHAR(10) NULL,   -- '1.0', '0.0' o NULL
    autorizacion_uso_analitico     VARCHAR(50),
    fecha_carga                    DATE
);
GO

-- >>> CAMBIA ESTA RUTA <<<
DECLARE @ruta NVARCHAR(400) = N'C:\Users\Luis\Dataset_V0_C01_Permanencia.csv';
DECLARE @sql  NVARCHAR(MAX) = N'
BULK INSERT stg_PermanenciaEstudiantil
FROM ''' + @ruta + N'''
WITH (
    FORMAT = ''CSV'',
    FIRSTROW = 2,
    FIELDTERMINATOR = '','',
    ROWTERMINATOR = ''0x0a'',
    CODEPAGE = ''65001'',
    TABLOCK,
    KEEPNULLS
);';
EXEC sp_executesql @sql;
GO

-- Verificación
SELECT COUNT(*) AS TotalRegistros FROM stg_PermanenciaEstudiantil;          -- esperado: 10000
SELECT no_continua_siguiente_periodo, COUNT(*) AS n
FROM stg_PermanenciaEstudiantil GROUP BY no_continua_siguiente_periodo;
SELECT TOP 10 * FROM stg_PermanenciaEstudiantil;
GO
