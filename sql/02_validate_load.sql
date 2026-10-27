
USE RestartSafeETL;
GO

SET NOCOUNT ON;

-- 1. Source file registration
SELECT
    SourceFileID,
    FileName,
    FileHash,
    FileSizeBytes,
    RegisteredAt
FROM etl.SourceFile
ORDER BY SourceFileID;


-- 2. Loaded rows per worksheet
SELECT
    SourceFileID,
    SourceSheet,
    COUNT_BIG(*) AS TotalRows,
    COUNT_BIG(DISTINCT SourceRowNumber) AS UniqueSourceRows,
    MIN(SourceRowNumber) AS FirstRow,
    MAX(SourceRowNumber) AS LastRow
FROM stg.RetailTransaction
GROUP BY SourceFileID, SourceSheet
ORDER BY SourceFileID, SourceSheet;


-- 3. Batch completion status
SELECT
    SourceFileID,
    SourceSheet,
    Status,
    COUNT_BIG(*) AS BatchCount,
    SUM(CAST(RowsLoaded AS BIGINT)) AS LoggedRows
FROM etl.LoadBatch
GROUP BY SourceFileID, SourceSheet, Status
ORDER BY SourceFileID, SourceSheet, Status;


-- 4. Duplicate source key detection
SELECT
    SourceFileID,
    SourceSheet,
    SourceRowNumber,
    COUNT_BIG(*) AS DuplicateCount
FROM stg.RetailTransaction
GROUP BY
    SourceFileID,
    SourceSheet,
    SourceRowNumber
HAVING COUNT_BIG(*) > 1;


-- 5. Staging vs. batch log reconciliation
WITH Staging AS (
    SELECT
        SourceFileID,
        SourceSheet,
        COUNT_BIG(*) AS StagingRows
    FROM stg.RetailTransaction
    GROUP BY SourceFileID, SourceSheet
),
BatchLog AS (
    SELECT
        SourceFileID,
        SourceSheet,
        SUM(CAST(RowsLoaded AS BIGINT)) AS LoggedRows
    FROM etl.LoadBatch
    WHERE Status = 'Completed'
    GROUP BY SourceFileID, SourceSheet
)
SELECT
    COALESCE(s.SourceFileID, b.SourceFileID) AS SourceFileID,
    COALESCE(s.SourceSheet, b.SourceSheet) AS SourceSheet,
    COALESCE(s.StagingRows, 0) AS StagingRows,
    COALESCE(b.LoggedRows, 0) AS LoggedRows,
    COALESCE(s.StagingRows, 0)
      - COALESCE(b.LoggedRows, 0) AS Difference
FROM Staging AS s
FULL OUTER JOIN BatchLog AS b
    ON s.SourceFileID = b.SourceFileID
   AND s.SourceSheet = b.SourceSheet
ORDER BY SourceFileID, SourceSheet;


-- 6. Incomplete batches
SELECT
    LoadBatchID,
    SourceFileID,
    SourceSheet,
    StartRowNumber,
    EndRowNumber,
    Status,
    RowsLoaded
FROM etl.LoadBatch
WHERE Status <> 'Completed';
