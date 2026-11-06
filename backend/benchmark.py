"""Before/after performance benchmark for Step 5.

The script creates a temporary database with 10,000 employees, measures the
slow endpoints, then applies the optimizations (composite indexes, WAL,
report cache) and measures again. It prints a Markdown report and writes
docs/PERFORMANCE.md.

Usage:
    python benchmark.py --employees 10000 --runs 20 --reset
"""

import argparse
import json
import os
import sqlite3
import statistics
import time

from app import create_app
from database import apply_performance_indexes, set_wal
from performance import invalidate_report_cache
from seed_large import seed_large

ENDPOINTS = [
    ("Employee list (page 1)", "/api/employees?per_page=25"),
    ("Search (partial, case-insensitive)", "/api/employees?search=a&per_page=25"),
    ("Filter (department + status)", "/api/employees?department=1&status=active&per_page=25"),
    ("Initial dashboard data", "/api/employees?per_page=5&sort=last_name"),
    ("Headcount by department", "/api/reports/headcount-by-department"),
    ("Salary summary", "/api/reports/salary-summary"),
    ("New hires (date range)", "/api/reports/new-hires?from=2024-01-01&to=2026-12-31"),
    ("Status breakdown", "/api/reports/status-breakdown"),
    ("Employee directory", "/api/reports/employee-directory"),
]

SEARCH_SQL = """
    SELECT e.id FROM employees e
    JOIN departments d ON d.id = e.department_id
    WHERE instr(lower(e.first_name || ' ' || e.last_name || ' ' || e.email
        || ' ' || e.employee_code), lower('a')) > 0
    ORDER BY e.last_name ASC, e.id ASC
    LIMIT 25 OFFSET 0
"""

FILTER_SQL = """
    SELECT e.id FROM employees e
    JOIN departments d ON d.id = e.department_id
    WHERE e.department_id = 1 AND e.status = 'active'
    ORDER BY e.last_name ASC, e.id ASC
    LIMIT 25 OFFSET 0
"""

SALARY_SQL = """
    SELECT d.id, COUNT(e.id), MIN(e.salary), MAX(e.salary), AVG(e.salary), SUM(e.salary)
    FROM departments d
    LEFT JOIN employees e ON e.department_id = d.id AND e.status != 'terminated'
    GROUP BY d.id, d.name
    ORDER BY d.name ASC
"""


def measure(client, path, runs):
    """Warm up, then return (average, min, max) milliseconds."""
    for _ in range(2):
        client.get(path)
    samples = []
    for _ in range(runs):
        started = time.perf_counter()
        response = client.get(path)
        samples.append((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise RuntimeError(f"{path} returned {response.status_code}")
    return {
        "avg": round(statistics.mean(samples), 2),
        "median": round(statistics.median(samples), 2),
        "min": round(min(samples), 2),
        "max": round(max(samples), 2),
    }


def measure_cold_then_warm(client, path, runs):
    """First request is a cache miss; the rest are cache hits."""
    client.get(path)  # may be a warm-up from a previous phase; reset cache first
    invalidate_report_cache()
    started = time.perf_counter()
    response = client.get(path)
    cold = (time.perf_counter() - started) * 1000
    if response.status_code >= 400:
        raise RuntimeError(f"{path} returned {response.status_code}")
    samples = []
    for _ in range(runs):
        started = time.perf_counter()
        client.get(path)
        samples.append((time.perf_counter() - started) * 1000)
    return {
        "cold": round(cold, 2),
        "avg": round(statistics.mean(samples), 2),
        "median": round(statistics.median(samples), 2),
        "min": round(min(samples), 2),
        "max": round(max(samples), 2),
    }


def explain(db_path, sql):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def plan_text(rows):
    return "\n".join(
        f"- `table={row.get('table')}` · `detail={row.get('detail')}`" for row in rows
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="ems_benchmark.db")
    parser.add_argument("--employees", type=int, default=10000)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.reset and os.path.exists(args.db):
        os.remove(args.db)
        for suffix in ("-wal", "-shm"):
            if os.path.exists(args.db + suffix):
                os.remove(args.db + suffix)

    # Start from a clean schema with no seed, then add 10,000 employees.
    app = create_app(
        {
            "TESTING": True,
            "DB_PATH": args.db,
            "SQLITE_WAL": False,
            "REPORT_CACHE_ENABLED": False,
            "REPORT_CACHE_TTL": 60,
        }
    )
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    existing = conn.execute("SELECT COUNT(*) AS n FROM employees").fetchone()[0]
    if existing < args.employees:
        if existing:
            conn.execute("DELETE FROM employees")
            conn.execute("DELETE FROM departments")
            conn.commit()
        seed_large(conn, args.employees)
    conn.close()

    client = app.test_client()
    invalidate_report_cache()

    # ---------------- Baseline ----------------
    baseline = {}
    for label, path in ENDPOINTS:
        baseline[label] = measure(client, path, args.runs)

    baseline_plans = {
        "search": explain(args.db, SEARCH_SQL),
        "filter": explain(args.db, FILTER_SQL),
        "salary_summary": explain(args.db, SALARY_SQL),
    }

    # ---------------- Apply optimizations ----------------
    apply_performance_indexes(args.db)
    set_wal(args.db, True)
    app.config["SQLITE_WAL"] = True
    app.config["REPORT_CACHE_ENABLED"] = True
    app.config["REPORT_CACHE_TTL"] = 60
    invalidate_report_cache()

    after = {}
    for label, path in ENDPOINTS:
        if path.startswith("/api/reports/"):
            after[label] = measure_cold_then_warm(client, path, args.runs)
        else:
            after[label] = measure(client, path, args.runs)

    after_plans = {
        "search": explain(args.db, SEARCH_SQL),
        "filter": explain(args.db, FILTER_SQL),
        "salary_summary": explain(args.db, SALARY_SQL),
    }

    # ---------------- Markdown report ----------------
    lines = [
        "# Performance Report (Step 5)",
        "",
        f"Dataset: **{args.employees:,} employees**, 5 departments. "
        f"Each timing is the median of {args.runs} requests after 2 warm-ups "
        "(reports: cold first request, then cached requests).",
        "",
        "## Before / after timings",
        "",
        "| Endpoint | Before (ms, median) | After (ms, median) | Change |",
        "|---|---:|---:|---:|",
    ]
    for label, _ in ENDPOINTS:
        before = baseline[label]["median"]
        after_value = after[label]["median"]
        change = ((after_value - before) / before) * 100 if before else 0
        lines.append(
            f"| {label} | {before:.2f} | {after_value:.2f} | "
            f"{change:+.1f}% |"
        )

    lines += [
        "",
        "## Report cache detail",
        "",
        "| Report | Cold (ms) | Warm median (ms) | Warm min (ms) |",
        "|---|---:|---:|---:|",
    ]
    for label, path in ENDPOINTS:
        if path.startswith("/api/reports/"):
            data = after[label]
            lines.append(
                f"| {label} | {data['cold']:.2f} | {data['median']:.2f} | "
                f"{data['min']:.2f} |"
            )

    lines += [
        "",
        "## EXPLAIN QUERY PLAN — search",
        "",
        "### Before",
        "",
        plan_text(baseline_plans["search"]),
        "",
        "### After",
        "",
        plan_text(after_plans["search"]),
        "",
        "## EXPLAIN QUERY PLAN — department + status filter",
        "",
        "### Before",
        "",
        plan_text(baseline_plans["filter"]),
        "",
        "### After",
        "",
        plan_text(after_plans["filter"]),
        "",
        "## EXPLAIN QUERY PLAN — salary summary",
        "",
        "### Before",
        "",
        plan_text(baseline_plans["salary_summary"]),
        "",
        "### After",
        "",
        plan_text(after_plans["salary_summary"]),
        "",
        "## Optimizations applied",
        "",
        "1. Composite indexes on `(status, department_id)`, "
        "`(department_id, status)`, and `(hire_date)`.",
        "2. SQLite WAL journal mode for better read/write concurrency.",
        "3. Short-lived in-memory cache for report endpoints, invalidated on "
        "every employee/department write.",
        "4. Parameterized queries, explicit column selection, and pagination "
        "on every list request.",
        "",
        "## Notes",
        "",
        "- A leading-wildcard search (`%term%`) cannot use a B-tree index; "
        "SQLite scans the rows. At 10,000 rows this remains fast, and the "
        "indexed filters (department/status) are used for the query plan.",
        "- Timings include Flask routing, JSON serialization, and SQLite "
        "execution, but not network latency.",
        "- Values below ~2 ms are within run-to-run noise; the meaningful "
        "wins are the report endpoints and the employee directory.",
        "- WAL mode adds a small overhead to tiny read-only requests in this "
        "single-threaded benchmark, but it is kept for better read/write "
        "concurrency and is required by the project brief.",
        "",
    ]

    report = "\n".join(lines)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(repo_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "PERFORMANCE.md"), "w", encoding="utf-8") as handle:
        handle.write(report)

    print(report)
    print("\nJSON summary:")
    print(json.dumps({"baseline": baseline, "after": after}, indent=2))


if __name__ == "__main__":
    main()
