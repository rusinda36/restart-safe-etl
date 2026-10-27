# Restart-Safe ETL with Python and SQL Server

A reproducible data engineering experiment demonstrating idempotent batch loading, transaction rollback, checkpoint-based recovery, and data reconciliation using Python and Microsoft SQL Server.

## Project Overview

ETL pipelines can fail after partially processing a source file. Without appropriate recovery mechanisms, restarting a pipeline may introduce duplicate records, lose data, or repeat already completed work.

This project implements a restart-safe loading process and tests its behavior under controlled failure conditions.

The experiment uses the real-world **UCI Online Retail II** dataset, containing 1,067,371 transaction records across two Excel worksheets.

## Technology Stack

- Python 3.13
- Microsoft SQL Server Express
- pyodbc and ODBC Driver 18
- openpyxl and pandas
- SQL Server Management Studio (SSMS)
- Git and GitHub

## Architecture

The pipeline consists of three main SQL Server tables:

| Table | Responsibility |
|---|---|
| `etl.SourceFile` | Registers source files using SHA-256 hashes |
| `etl.LoadBatch` | Tracks completed loading batches and their source row ranges |
| `stg.RetailTransaction` | Stores source transactions with unique source-row identifiers |

Each transaction is identified by the combination of `SourceFileID`, `SourceSheet`, and `SourceRowNumber`.

The pipeline processes Excel data in batches of 1,000 rows.

A completed batch is recorded in `etl.LoadBatch` within the same database transaction as the corresponding data insertion.

On restart, previously completed batches are skipped.

## Repository Structure

```text
restart-safe-etl/
├── data/
│   └── raw/
├── src/
│   ├── analyze_invoices.py
│   ├── load_transactions.py
│   ├── profile_full.py
│   ├── profile_source.py
│   ├── register_source.py
│   └── test_connection.py
├── sql/
│   ├── 00_create_database.sql
│   ├── 01_create_tables.sql
│   └── 02_validate_load.sql
├── evidence/
├── tests/
├── .gitignore
├── requirements.txt
└── README.md
```

## Dataset

Source: UCI Machine Learning Repository — Online Retail II.

https://archive.ics.uci.edu/dataset/502/online+retail+ii

The dataset is not included in this repository.

Download and extract the Excel workbook into:

`data/raw/online_retail_II.xlsx`

The workbook used in the experiment had the following characteristics:

- File size: 45,622,278 bytes
- SHA-256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`
- Year 2009–2010: 525,461 records
- Year 2010–2011: 541,910 records

The SHA-256 hash identifies the exact workbook used for the documented experiment.

## Setup

### 1. Create a Python virtual environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Install SQL Server

Install Microsoft SQL Server Express and Microsoft ODBC Driver 18 for SQL Server.

The current scripts assume:

- SQL Server instance: `.\SQLEXPRESS`
- Database: `RestartSafeETL`
- Authentication: Windows Authentication

Adjust the connection settings in the Python scripts if your environment differs.

### 3. Create the database

Execute these scripts in SQL Server Management Studio, in order:

1. `sql/00_create_database.sql`
2. `sql/01_create_tables.sql`

The database and table creation scripts were also tested using a separate clean database.

### 4. Register the source file

```powershell
python .\src\register_source.py
```

The registration process calculates a SHA-256 hash and checks whether the source file has already been registered.

### 5. Run the ETL

```powershell
python .\src\load_transactions.py
```

By default, controlled failure simulation is disabled:

```python
FAIL_BEFORE_COMMIT_AT_BATCH = None
```

To simulate an exception before a particular batch commits, set this value to the desired batch number.

Use a fresh test database when reproducing failure scenarios.

### 6. Validate the results

Run:

`sql/02_validate_load.sql`

The validation script checks source registration, loaded row counts, completed batches, duplicate source keys, reconciliation differences, and incomplete batches.

## Experiment Results

The original experiment produced the following verified results:

| Metric | Result |
|---|---:|
| Source records | 1,067,371 |
| Staging records | 1,067,371 |
| Completed batches | 1,068 |
| Duplicate source keys | 0 |
| Incomplete batches | 0 |
| Staging-to-batch reconciliation difference | 0 |

### Experiment 1 — Restart After Partial Completion

The pipeline was stopped after several committed batches and subsequently restarted.

Previously completed batches were recognized and skipped.

### Experiment 2 — Failure Before COMMIT

A controlled exception was raised after inserting a batch and its completion record, but before committing the transaction.

SQL Server verification confirmed:

- Previously committed records remained intact.
- No records from the interrupted batch remained.
- No completion record for the interrupted batch remained.

This demonstrated transaction rollback for the controlled exception scenario.

### Experiment 3 — Complete Recovery

The pipeline was restarted with failure simulation disabled.

It successfully completed loading both Excel worksheets.

### Experiment 4 — Idempotent Rerun

The fully completed pipeline was executed again.

All 1,068 batches were skipped, and SQL Server validation confirmed that the staging and batch-log counts remained unchanged.

## Transactional Guarantees

The implementation provides the following behavior in the tested single-process scenarios:

- Completed batches are identified using persistent SQL Server records.
- Data insertion and batch completion are committed together.
- Exceptions before commit trigger transaction rollback.
- Source-row uniqueness prevents duplicate staging keys.
- Repeated execution skips previously completed batches.

These guarantees were verified using controlled exceptions and SQL validation.

## Known Limitations

### Insertion performance

The current implementation uses `pyodbc.executemany()` with an individual `INSERT ... WHERE NOT EXISTS` operation for each source record.

This approach demonstrated poor performance when loading more than one million rows.

Potential improvements include set-based loading, temporary staging tables, bulk insert operations, and `fast_executemany`.

These optimizations have not yet been benchmarked in this project.

### Recovery model

The implementation was tested using a single loading process and controlled Python exceptions.

Concurrent ETL workers, abrupt process termination, SQL Server crashes, and network interruptions were not separately validated.

### Checkpoint granularity

Completed batches are skipped on restart, but the current loader still reads the Excel worksheets sequentially.

Therefore, checkpoint recovery reduces repeated database writes but does not eliminate repeated source-file reading.

### Data validation

The reconciliation process compares source-row counts, unique identifiers, and batch-log totals.

It does not independently verify every field value against the original workbook.

## Project Status

The original ETL experiment is complete and validated.

Future engineering work may include automated integration tests, performance benchmarking, bulk loading optimization, and stronger recovery testing.
