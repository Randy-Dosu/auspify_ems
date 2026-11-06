# Auspify EMS — Folder structure

```text
auspify_ems/
├── backend/
│   ├── app.py                  # Flask app factory, health endpoint, error handlers
│   ├── database.py             # SQLite connection, schema, indexes, WAL
│   ├── validation.py           # Employee and department validation rules
│   ├── performance.py          # Short-lived report cache + invalidation
│   ├── seed_large.py           # Optional 10,000+ employee benchmark generator
│   ├── benchmark.py            # Before/after timings + EXPLAIN QUERY PLAN
│   ├── requirements.txt        # Flask, flask-cors
│   ├── requirements-dev.txt    # pytest
│   ├── pytest.ini              # Test configuration
│   ├── ems.db                  # Development database (git-ignored)
│   ├── routes/
│   │   ├── employees.py        # List/search/filter, detail, create, update, delete
│   │   ├── departments.py      # List, create, update, delete
│   │   └── reports.py          # Report endpoints + CSV exports
│   └── tests/
│       ├── conftest.py         # Empty temporary DB + test-only fixtures
│       ├── test_health.py      # Health, empty database, foreign keys, WAL
│       ├── test_employees.py   # Validation, CRUD, soft delete, filters, pagination
│       ├── test_departments.py # Department CRUD and deletion rules
│       └── test_reports.py     # Report calculations, CSV, cache, empty database
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js          # /api proxy -> http://127.0.0.1:5000
│   └── src/
│       ├── main.jsx            # React root
│       ├── App.jsx             # Router, lazy routes, layout, footer
│       ├── api.js              # fetch wrapper + ApiError
│       ├── index.css           # Design system and all component styles
│       ├── utils.js            # Currency/date/status formatting helpers
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── EmployeeTable.jsx
│       │   ├── SearchBar.jsx
│       │   ├── ConfirmDialog.jsx
│       │   ├── Notification.jsx
│       │   ├── StatusBadge.jsx
│       │   ├── Spinner.jsx
│       │   └── PageLoader.jsx
│       ├── context/
│       │   ├── NotificationContext.jsx
│       │   └── notification-context.js
│       ├── hooks/
│       │   ├── useDebounce.js
│       │   └── useNotification.js
│       └── pages/
│           ├── Dashboard.jsx
│           ├── EmployeeList.jsx
│           ├── EmployeeForm.jsx
│           ├── EmployeeDetails.jsx
│           ├── Departments.jsx
│           ├── Reports.jsx
│           └── NotFound.jsx
├── docs/
│   ├── REQUIREMENTS.md         # Functional + non-functional requirements
│   ├── WIREFRAMES.md           # Text wireframes for every screen
│   ├── FOLDER_STRUCTURE.md     # This file
│   ├── PERFORMANCE.md          # Generated before/after benchmark report
│   └── TESTING.md              # Test results, manual checklist, edge cases
├── .venv/                      # Local Python virtual environment (git-ignored)
├── .gitignore
└── README.md
```

## Conventions

- **Backend:** one topic per module; routes return JSON; errors use
  `{"error": "message"}` with a meaningful HTTP status.
- **Frontend:** functional components and hooks only; plain CSS; no UI
  library; route pages are lazy-loaded.
- **Data flow:** React calls relative `/api/...` URLs; Vite proxies them to
  Flask in development, so there is no hard-coded backend host in the client.
- **Database:** SQLite with foreign keys enabled and WAL mode. The schema is
  created automatically on first run. The application starts empty; tests
  create their own temporary data.
