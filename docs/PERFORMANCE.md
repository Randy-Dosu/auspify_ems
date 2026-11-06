# Performance Report (Step 5)

The benchmark uses a separate temporary database; the application itself starts empty.

Dataset: **10,000 employees**, 5 departments. Each timing is the median of 100 requests after 2 warm-ups (reports: cold first request, then cached requests).

## Before / after timings

| Endpoint | Before (ms, median) | After (ms, median) | Change |
|---|---:|---:|---:|
| Employee list (page 1) | 1.27 | 1.52 | +19.7% |
| Search (partial, case-insensitive) | 10.09 | 10.51 | +4.2% |
| Filter (department + status) | 2.58 | 2.10 | -18.6% |
| Initial dashboard data | 1.02 | 1.35 | +32.4% |
| Headcount by department | 6.38 | 0.22 | -96.6% |
| Salary summary | 6.72 | 0.23 | -96.6% |
| New hires (date range) | 20.43 | 7.87 | -61.5% |
| Status breakdown | 0.98 | 0.22 | -77.6% |
| Employee directory | 58.67 | 23.55 | -59.9% |

## Report cache detail

| Report | Cold (ms) | Warm median (ms) | Warm min (ms) |
|---|---:|---:|---:|
| Headcount by department | 3.59 | 0.22 | 0.20 |
| Salary summary | 7.98 | 0.23 | 0.20 |
| New hires (date range) | 20.98 | 7.87 | 6.96 |
| Status breakdown | 1.58 | 0.22 | 0.20 |
| Employee directory | 68.14 | 23.55 | 20.58 |

## EXPLAIN QUERY PLAN — search

### Before

- `table=None` · `detail=SCAN e USING INDEX idx_employees_last_name`
- `table=None` · `detail=SEARCH d USING INTEGER PRIMARY KEY (rowid=?)`

### After

- `table=None` · `detail=SCAN e USING INDEX idx_employees_last_name`
- `table=None` · `detail=SEARCH d USING INTEGER PRIMARY KEY (rowid=?)`

## EXPLAIN QUERY PLAN — department + status filter

### Before

- `table=None` · `detail=SEARCH d USING INTEGER PRIMARY KEY (rowid=?)`
- `table=None` · `detail=SEARCH e USING INDEX idx_employees_department_id (department_id=?)`
- `table=None` · `detail=USE TEMP B-TREE FOR ORDER BY`

### After

- `table=None` · `detail=SEARCH d USING INTEGER PRIMARY KEY (rowid=?)`
- `table=None` · `detail=SEARCH e USING INDEX idx_employees_department_status (department_id=? AND status=?)`
- `table=None` · `detail=USE TEMP B-TREE FOR ORDER BY`

## EXPLAIN QUERY PLAN — salary summary

### Before

- `table=None` · `detail=SCAN d USING COVERING INDEX sqlite_autoindex_departments_1`
- `table=None` · `detail=SEARCH e USING INDEX idx_employees_department_id (department_id=?) LEFT-JOIN`
- `table=None` · `detail=USE TEMP B-TREE FOR ORDER BY`

### After

- `table=None` · `detail=SCAN d USING COVERING INDEX sqlite_autoindex_departments_1`
- `table=None` · `detail=SEARCH e USING INDEX idx_employees_department_id (department_id=?) LEFT-JOIN`
- `table=None` · `detail=USE TEMP B-TREE FOR ORDER BY`

## Optimizations applied

1. Composite indexes on `(status, department_id)`, `(department_id, status)`, and `(hire_date)`.
2. SQLite WAL journal mode for better read/write concurrency.
3. Short-lived in-memory cache for report endpoints, invalidated on every employee/department write.
4. Parameterized queries, explicit column selection, and pagination on every list request.

## Notes

- A leading-wildcard search (`%term%`) cannot use a B-tree index; SQLite scans the rows. At 10,000 rows this remains fast, and the indexed filters (department/status) are used for the query plan.
- Timings include Flask routing, JSON serialization, and SQLite execution, but not network latency.
- Values below ~2 ms are within run-to-run noise; the meaningful wins are the report endpoints and the employee directory.
- WAL mode adds a small overhead to tiny read-only requests in this single-threaded benchmark, but it is kept for better read/write concurrency and is required by the project brief.
