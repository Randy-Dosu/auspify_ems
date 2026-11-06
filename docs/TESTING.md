# Testing and verification

## 1. Automated backend tests

The pytest suite uses a **temporary, empty SQLite database for every test**, so
it never touches the development database. Tests that need records create
them through the API.

```bash
cd backend
../.venv/bin/python -m pytest
```

Latest result:

```text
59 passed
```

### Coverage

| Area | Tests | What is verified |
|------|-------|------------------|
| Health and empty database | `test_health.py` | Health status, empty start, test fixture creates 5 departments/25 employees, manager names, foreign keys, WAL mode, invalid department rejected by the database |
| Search and filters | `test_employees.py` | Partial case-insensitive search, code/email search, wildcard escaping, department id/name, status, job title, hire-date range, combined filters, invalid filter values |
| Pagination and sorting | `test_employees.py` | Correct total/page counts, last page, empty page, per-page cap, salary and last-name sorting |
| Validation | `test_employees.py` | Missing fields, bad email, future hire date, negative salary, invalid department, invalid status |
| Create and update | `test_employees.py` | Auto-generated code, supplied code, duplicate email/code (409), update persists, duplicate email on update, missing ID (404) |
| Soft and hard delete | `test_employees.py` | Terminated status, hidden by default, shown with toggle/status filter, permanent delete, missing ID (404) |
| Departments | `test_departments.py` | Create, duplicate name (409), missing name, invalid manager, update, duplicate update, delete empty, delete with employees (409), missing ID (404) |
| Reports | `test_reports.py` | Headcount totals, salary min/max/avg/total against direct SQL, new-hire date range, status breakdown, directory, CSV headers/content |
| Cache | `test_reports.py` | MISS then HIT, invalidation after create/delete, bypass when disabled |
| Empty database | `test_reports.py` | All reports return zeros and no errors |

## 2. Frontend verification

```bash
cd frontend
npm run lint
npm run build
```

Latest result: **0 lint warnings/errors**, production build succeeds with
separate lazy-loaded chunks for each route.

A runtime smoke test was also executed against the live Vite proxy and Flask
API using jsdom (no real browser is available in the sandbox). It verified:

- Dashboard renders with 25 employees, 5 departments, payroll totals, and charts.
- Employee list renders filters, table rows, pagination, and actions.
- Departments renders all five cards with managers and counts.
- Reports renders summary cards, charts, salary table, and new-hire table.
- Navigating between all four pages works.
- Creating an employee through the form works and navigates to the detail page.
- Terminate and hard-delete confirmation dialogs open and cancel correctly.
- Creating a department through the modal works.
- No fatal console errors.

The only console warnings in jsdom were Recharts `width(0)`/`height(0)`
warnings caused by jsdom's lack of layout; a real browser gives the chart
container a real size.

## 3. Manual end-to-end checklist

Perform these actions in the browser at `http://127.0.0.1:5173`.

| # | Action | Expected result | Pass/Fail |
|---|--------|-----------------|-----------|
| 1 | Departments → **Add department** → enter `Operations` → **Create department** | Card appears, toast “Department created successfully.” | ☐ Pass / ☐ Fail |
| 2 | Employees → **Add employee** → fill required fields → **Register employee** | Navigates to the new employee's details, toast “Employee registered successfully.” | ☐ Pass / ☐ Fail |
| 3 | Employees → search `Mensah` | Kwame Mensah appears after the 300 ms debounce | ☐ Pass / ☐ Fail |
| 4 | Employees → search `zzzz-no-match` | Empty state with a helpful message | ☐ Pass / ☐ Fail |
| 5 | Open an employee → **Edit** → change job title and salary → **Save changes** | Details update, toast “Employee updated successfully.” | ☐ Pass / ☐ Fail |
| 6 | Open an employee → **Terminate** → confirm | Status becomes Terminated; employee disappears from the default list | ☐ Pass / ☐ Fail |
| 7 | Employees → check **Show terminated** | Terminated employee reappears | ☐ Pass / ☐ Fail |
| 8 | Open a terminated employee → **Delete permanently** → confirm | Record is removed; it no longer appears in the list or search results | ☐ Pass / ☐ Fail |
| 9 | Departments → try to delete **Engineering** | Error message explains that the department has employees; it is not deleted | ☐ Pass / ☐ Fail |
| 10 | Reports → apply a hire-date range | New-hire count and table update to the selected range | ☐ Pass / ☐ Fail |
| 11 | Reports → **Export headcount CSV** | A CSV file downloads and opens in a spreadsheet | ☐ Pass / ☐ Fail |
| 12 | Reports → **Export directory CSV** | A CSV with the employee directory downloads | ☐ Pass / ☐ Fail |
| 13 | Stop the Flask server, reload the frontend | Friendly error banner; no unhandled crash | ☐ Pass / ☐ Fail |
| 14 | Restart Flask and reload | Data is still present (SQLite persistence) | ☐ Pass / ☐ Fail |
| 15 | Resize the browser to 375px | Hamburger menu, stacked cards, horizontally scrollable tables | ☐ Pass / ☐ Fail |
| 16 | Open the browser console and navigate every page | No errors (Recharts may warn only in jsdom) | ☐ Pass / ☐ Fail |

## 4. Edge cases handled

- **Empty database:** reports return zeros; list shows an empty state.
- **Duplicate email:** 409 with a field error.
- **Duplicate employee code:** 409 with a field error.
- **Duplicate department name:** 409 (case-insensitive).
- **Department with employees:** deletion returns 409 and a clear message.
- **Terminated employees:** hidden by default; visible via toggle or status filter.
- **Future hire date:** 400 with a field error.
- **Negative salary:** 400 with a field error.
- **Invalid email:** 400 with a field error.
- **Invalid department:** 400 with a field error.
- **Missing ID:** 404 for employee and department endpoints.
- **Invalid filters:** 400 for unknown status, invalid dates, invalid sort/order, or non-positive pagination.
- **Pagination past the last page:** empty data array with correct `total_pages`.
- **Very large datasets:** 10,000 employees generated in a separate benchmark database and profiled; list/search/reports remain responsive.
- **Server offline:** the React pages show an error banner with a retry button.
- **Cache staleness:** any employee/department write invalidates report caches.
- **Manager deletion:** soft delete keeps the record; hard delete sets `departments.manager_id` to `NULL` via `ON DELETE SET NULL`.
- **Search wildcards:** `%` and `_` are treated literally.
- **CSV formula injection:** values are written with the `csv` module; spreadsheet apps may still interpret `=`, `+`, `-`, `@` as formulas. For untrusted data, prefix such values with an apostrophe in a production system.

## 5. Known limitations

- Leading-wildcard search (`%term%`) cannot use a B-tree index; SQLite scans
  the index. At 10,000 rows this is still fast (~10 ms including Flask).
- WAL mode adds a small overhead to tiny read-only requests in a
  single-threaded benchmark; it is kept for write concurrency.
- No authentication or role-based access control.
- The department manager dropdown loads up to 100 employees; the API supports
  pagination for larger datasets.
- CSV exports intentionally include all matching rows rather than one page.
- There is no automated browser test suite; the UI was verified with a jsdom
  runtime smoke test and the manual checklist above.
