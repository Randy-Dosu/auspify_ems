# Auspify EMS — Requirements

A small full-stack application for managing employee records and
organisational data. Built with **Python + Flask**, **React + Vite**, and
**SQLite**.

## 1. Purpose

Auspify EMS lets an organisation store employee records, organise staff into
departments, search the staff directory, and generate headcount, salary, and
hiring reports.

## 2. Functional requirements

| ID | Requirement | Status |
|----|-------------|--------|
| FR-1 | The backend exposes a health endpoint that verifies the database connection. | Implemented |
| FR-2 | The React frontend loads and calls the backend through the Vite proxy. | Implemented |
| FR-3 | Departments are stored with a unique name, description, manager, and timestamps. | Implemented |
| FR-4 | Employees are stored with code, names, email, phone, date of birth, gender, job title, department, salary, hire date, status, address, and timestamps. | Implemented |
| FR-5 | The database schema is created automatically on first run. The application starts empty; tests create their own temporary data. | Implemented |
| FR-6 | Dashboard, employee list, employee form, employee details, departments, and reports screens are available. | Implemented |
| FR-7 | A new employee can be registered with server-side validation and a department dropdown. | Implemented |
| FR-8 | Departments can be created with unique names and assigned managers. | Implemented |
| FR-9 | Employees can be updated, soft-deleted (terminated), and hard-deleted with confirmation. | Implemented |
| FR-10 | Departments can be updated and deleted; deletion is blocked while employees remain. | Implemented |
| FR-11 | Employees can be searched by name/email/code and filtered by department, status, job title, and hire date range. | Implemented |
| FR-12 | Results can be sorted and paginated. | Implemented |
| FR-13 | Headcount, salary, new-hire, status, and directory reports are available. | Implemented |
| FR-14 | At least two reports can be exported as CSV. | Implemented (headcount, salary, directory) |
| FR-15 | The system performs acceptably with 10,000+ employees. | Implemented and profiled |

## 3. Non-functional requirements

| ID | Requirement | Status |
|----|-------------|--------|
| NFR-1 | Responsive layout that works on desktop and mobile. | Implemented |
| NFR-2 | Predictable HTTP status codes and JSON error messages. | Implemented |
| NFR-3 | Data integrity: required fields, unique email/code, valid dates, non-negative salary, valid department references. | Implemented |
| NFR-4 | Parameterized SQL only; no secrets in source; CORS enabled for development. | Implemented |
| NFR-5 | Pagination on every list request; 10,000+ employee dataset profiled. | Implemented |
| NFR-6 | Small, commented modules and a clear folder structure. | Implemented |
| NFR-7 | Runs on Python 3.11+ with SQLite; no external database server. | Implemented |
| NFR-8 | Automated tests use a temporary database and never touch development data. | Implemented |

## 4. Business rules

1. **Employee code** is auto-generated as `EMP-0001`, `EMP-0002`, … when not
   supplied. Codes and emails are unique (case-insensitive).
2. **Hire date** cannot be in the future. **Salary** must be zero or greater.
3. **Department** must exist. A department name is unique (case-insensitive).
4. **Soft delete** sets `status = 'terminated'`. Terminated employees are
   hidden from the default employee list and can be shown with a toggle or an
   explicit status filter.
5. **Hard delete** is permanent and requires confirmation in the UI.
6. **Department deletion** is blocked while any employee is assigned to it.
7. **Salary summary** excludes terminated employees. Headcount includes all
   statuses and shows the breakdown.
8. **Report cache** is invalidated after every employee or department write.

## 5. Out of scope / future work

Authentication and roles, leave management, payroll processing, profile
photos, audit logging, Docker, and full-text search are not part of this
project. See the README for suggested improvements.
