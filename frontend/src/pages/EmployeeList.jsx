import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import EmployeeTable from "../components/EmployeeTable";
import SearchBar from "../components/SearchBar";
import Spinner from "../components/Spinner";
import { useDebounce } from "../hooks/useDebounce";
import { useNotification } from "../hooks/useNotification";
import { api } from "../api";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "on_leave", label: "On leave" },
  { value: "terminated", label: "Terminated" },
];

const SORT_OPTIONS = [
  { value: "last_name", label: "Last name" },
  { value: "first_name", label: "First name" },
  { value: "hire_date", label: "Hire date" },
  { value: "salary", label: "Salary" },
  { value: "department", label: "Department" },
];

export default function EmployeeList() {
  const { notify } = useNotification();

  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebounce(searchInput, 300);
  const [department, setDepartment] = useState("");
  const [status, setStatus] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [hiredFrom, setHiredFrom] = useState("");
  const [hiredTo, setHiredTo] = useState("");
  const [sort, setSort] = useState("last_name");
  const [order, setOrder] = useState("asc");
  const [includeTerminated, setIncludeTerminated] = useState(false);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);

  const [employees, setEmployees] = useState([]);
  const [meta, setMeta] = useState({
    total: 0,
    page: 1,
    per_page: 10,
    total_pages: 0,
  });
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState({ open: false, mode: "soft", employee: null });
  const [deleting, setDeleting] = useState(false);

  const loadEmployees = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await api.getEmployees({
        search: debouncedSearch,
        department,
        status,
        job_title: jobTitle,
        hired_from: hiredFrom,
        hired_to: hiredTo,
        sort,
        order,
        include_terminated: includeTerminated,
        page,
        per_page: perPage,
      });
      setEmployees(payload.data);
      setMeta(payload.meta);
      // If deleting the last row on a page, move back to the previous page.
      if (payload.meta.total_pages > 0 && page > payload.meta.total_pages) {
        setPage(payload.meta.total_pages);
      }
    } catch (err) {
      setError(err.message || "Could not load employees.");
    } finally {
      setLoading(false);
    }
  }, [
    debouncedSearch,
    department,
    status,
    jobTitle,
    hiredFrom,
    hiredTo,
    sort,
    order,
    includeTerminated,
    page,
    perPage,
  ]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadEmployees();
  }, [loadEmployees]);

  useEffect(() => {
    let cancelled = false;
    api
      .getDepartments()
      .then((payload) => {
        if (!cancelled) setDepartments(payload.data);
      })
      .catch(() => {
        // The department dropdown is optional; the page still works without it.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const hasFilters = Boolean(
    debouncedSearch || department || status || jobTitle || hiredFrom || hiredTo || includeTerminated,
  );

  // Changing a filter should jump back to the first page. Setting the page
  // in the same event as the filter avoids an extra fetch with the old page.
  const changeFilter = (setter) => (value) => {
    setter(value);
    setPage(1);
  };

  const clearFilters = () => {
    setSearchInput("");
    setDepartment("");
    setStatus("");
    setJobTitle("");
    setHiredFrom("");
    setHiredTo("");
    setIncludeTerminated(false);
    setSort("last_name");
    setOrder("asc");
    setPage(1);
  };

  const requestSoftDelete = useCallback((employee) => {
    setDialog({ open: true, mode: "soft", employee });
  }, []);

  const requestHardDelete = useCallback((employee) => {
    setDialog({ open: true, mode: "hard", employee });
  }, []);

  const closeDialog = useCallback(() => {
    setDialog((current) => ({ ...current, open: false }));
  }, []);

  const confirmDelete = async () => {
    if (!dialog.employee) return;
    setDeleting(true);
    try {
      await api.deleteEmployee(dialog.employee.id, dialog.mode === "hard");
      notify(
        dialog.mode === "hard"
          ? `${dialog.employee.first_name} ${dialog.employee.last_name} was permanently deleted.`
          : `${dialog.employee.first_name} ${dialog.employee.last_name} was marked as terminated.`,
        "success",
      );
      setDialog({ open: false, mode: "soft", employee: null });
      await loadEmployees();
    } catch (err) {
      notify(err.message || "The employee could not be deleted.", "error");
    } finally {
      setDeleting(false);
    }
  };

  const start = meta.total === 0 ? 0 : (meta.page - 1) * meta.per_page + 1;
  const end = Math.min(meta.page * meta.per_page, meta.total);

  const dialogCopy = useMemo(() => {
    if (!dialog.employee) return { title: "", message: "" };
    const name = `${dialog.employee.first_name} ${dialog.employee.last_name}`;
    if (dialog.mode === "hard") {
      return {
        title: "Delete employee permanently?",
        message: `This will permanently remove ${name} from the database. This action cannot be undone.`,
      };
    }
    return {
      title: "Terminate employee?",
      message: `Mark ${name} as terminated? They will be hidden from the default list. You can still show terminated employees with the toggle.`,
    };
  }, [dialog]);

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">People</p>
          <h1>Employees</h1>
          <p className="page-subtitle">
            Search, filter, and manage every employee record.
          </p>
        </div>
        <div className="page-actions">
          <Link to="/employees/new" className="btn btn-primary">
            Add employee
          </Link>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          <p>{error}</p>
          <button type="button" className="btn btn-sm btn-secondary" onClick={loadEmployees}>
            Try again
          </button>
        </div>
      )}

      <section className="card filters-card" aria-label="Employee filters">
        <div className="filter-top">
          <SearchBar
            value={searchInput}
            onChange={(value) => {
              setSearchInput(value);
              setPage(1);
            }}
          />
          <div className="filter-top-actions">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={includeTerminated}
                onChange={(event) => {
                  setIncludeTerminated(event.target.checked);
                  setPage(1);
                }}
              />
              Show terminated
            </label>
            {hasFilters && (
              <button type="button" className="btn btn-sm btn-ghost" onClick={clearFilters}>
                Clear filters
              </button>
            )}
          </div>
        </div>

        <div className="filter-grid">
          <label className="field">
            <span>Department</span>
            <select value={department} onChange={(event) => changeFilter(setDepartment)(event.target.value)}>
              <option value="">All departments</option>
              {departments.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Status</span>
            <select value={status} onChange={(event) => changeFilter(setStatus)(event.target.value)}>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Job title contains</span>
            <input
              type="text"
              value={jobTitle}
              onChange={(event) => changeFilter(setJobTitle)(event.target.value)}
              placeholder="e.g. Manager"
            />
          </label>

          <label className="field">
            <span>Hired from</span>
            <input
              type="date"
              value={hiredFrom}
              onChange={(event) => changeFilter(setHiredFrom)(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Hired to</span>
            <input
              type="date"
              value={hiredTo}
              onChange={(event) => changeFilter(setHiredTo)(event.target.value)}
            />
          </label>

          <label className="field">
            <span>Sort by</span>
            <select value={sort} onChange={(event) => changeFilter(setSort)(event.target.value)}>
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Order</span>
            <select value={order} onChange={(event) => changeFilter(setOrder)(event.target.value)}>
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </label>

          <label className="field">
            <span>Per page</span>
            <select
              value={perPage}
              onChange={(event) => changeFilter(setPerPage)(Number(event.target.value))}
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </label>
        </div>
      </section>

      <section className="card table-card">
        <div className="table-summary">
          <p>
            {loading ? (
              <span className="inline-loading">
                <Spinner label="Loading employees" /> Loading employees…
              </span>
            ) : (
              <>
                Showing <strong>{start}</strong>–<strong>{end}</strong> of{" "}
                <strong>{meta.total}</strong> employees
              </>
            )}
          </p>
          <div className="pagination">
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={loading || meta.page <= 1}
            >
              Previous
            </button>
            <span className="page-indicator">
              Page {meta.page} of {Math.max(meta.total_pages, 1)}
            </span>
            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() =>
                setPage((current) => Math.min(meta.total_pages || 1, current + 1))
              }
              disabled={loading || meta.page >= meta.total_pages}
            >
              Next
            </button>
          </div>
        </div>

        <EmployeeTable
          employees={employees}
          loading={loading}
          onSoftDelete={requestSoftDelete}
          onHardDelete={requestHardDelete}
          emptyMessage={
            hasFilters
              ? "No employees match these filters. Try clearing them."
              : "No employees have been added yet."
          }
        />
      </section>

      <ConfirmDialog
        open={dialog.open}
        title={dialogCopy.title}
        message={dialogCopy.message}
        confirmLabel={dialog.mode === "hard" ? "Delete permanently" : "Terminate employee"}
        danger={dialog.mode === "hard"}
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={closeDialog}
      />
    </div>
  );
}
