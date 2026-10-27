# Restart-Safe ETL — Experiment Results

## Test Environment

- Python 3.13
- SQL Server Express
- ODBC Driver 18
- Source: UCI Online Retail II
- Batch size: 1,000 rows
- Source records: 1,067,371

## Test 1 — Source File Registration

**Procedure:** Register the same Excel workbook twice.

**Observed results:**

First execution:
```text
File registered. SourceFileID: 1
```

Second execution:
```text
File already registered. SourceFileID: 1
```

**Result:** PASS — duplicate file registration prevented.

## Test 2 — Restart After Partial Loading

**Procedure:**

1. Load 3,000 records.
2. Stop the loader after committed batches.
3. Restart and process five batches.

**Observed results:**

| Metric | Value |
|---|---:|
| Staging rows before restart | 3,000 |
| Staging rows after restart | 5,000 |
| Unique source rows | 5,000 |

**Result:** PASS — no duplicate source rows.

## Test 3 — Transaction Rollback

**Procedure:** Raise a controlled exception before committing batch 6.

**Observed results:**

| Metric | Value |
|---|---:|
| Previously committed rows | 5,000 |
| Rows from interrupted batch | 0 |
| Batch 6 completion records | 0 |

**Result:** PASS — both data insertion and batch-log insertion rolled back.

## Test 4 — Recovery and Complete Loading

**Procedure:** Disable failure simulation and restart the pipeline.

**Observed results:**

| Worksheet | Rows | Completed batches |
|---|---:|---:|
| Year 2009–2010 | 525,461 | 526 |
| Year 2010–2011 | 541,910 | 542 |
| **Total** | **1,067,371** | **1,068** |

**Result:** PASS — both worksheets loaded successfully.

## Test 5 — Idempotent Full Rerun

**Procedure:** Execute the completed ETL again without clearing the database.

**Observed results:**

- Completed batches were skipped.
- Total staging records: 1,067,371.
- Completed batch records: 1,068.
- Incomplete batches: 0.
- Logged rows: 1,067,371.
- Duplicate source keys: 0.
- Reconciliation difference: 0.

**Result:** PASS — no additional source rows or batch-log records.

## Performance Observation

The initial implementation used row-by-row conditional SQL insertion through `pyodbc.executemany()`.

Loading the complete dataset was significantly slower than expected.

No controlled performance benchmark was performed, so exact throughput comparisons are not reported.

## Scope of Validation

The experiment verifies controlled exception handling, transactional rollback, restart behavior, source-key uniqueness, and row-count reconciliation.

It does not establish guarantees for concurrent loaders, network failures, abrupt process termination, or SQL Server crashes.

## Overall Result

**PASS — all five documented experiments completed successfully within the tested scope.**
