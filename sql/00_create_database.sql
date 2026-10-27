
USE master;
GO

IF DB_ID(N'RestartSafeETL') IS NULL
BEGIN
    CREATE DATABASE RestartSafeETL;
END;
GO

USE RestartSafeETL;
GO

IF SCHEMA_ID(N'etl') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA etl');
END;
GO

IF SCHEMA_ID(N'stg') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA stg');
END;
GO

PRINT 'Database and schemas are ready.';
GO
