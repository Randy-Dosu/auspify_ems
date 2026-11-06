import { memo } from "react";
import { Link } from "react-router-dom";
import StatusBadge from "./StatusBadge";
import { formatCurrency, formatDate, initials } from "../utils";

/**
 * Shared employee table. Memoized so a parent re-render (for example a
 * notification) does not re-render every row unnecessarily.
 */
function EmployeeTable({
  employees = [],
  loading = false,
  onSoftDelete,
  onHardDelete,
  emptyMessage = "No employees found.",
  compact = false,
}) {
  if (loading) {
    return (
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Employee</th>
              {!compact && <th>Job title</th>}
              <th>Department</th>
              <th>Status</th>
              {!compact && <th>Salary</th>}
              <th>Hire date</th>
              {(onSoftDelete || onHardDelete) && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, index) => (
              <tr key={`skeleton-${index}`} className="skeleton-row">
                <td>
                  <div className="skeleton skeleton-avatar" />
                  <div className="skeleton skeleton-line" />
                </td>
                {!compact && <td><div className="skeleton skeleton-line" /></td>}
                <td><div className="skeleton skeleton-line" /></td>
                <td><div className="skeleton skeleton-pill" /></td>
                {!compact && <td><div className="skeleton skeleton-line" /></td>}
                <td><div className="skeleton skeleton-line" /></td>
                {(onSoftDelete || onHardDelete) && (
                  <td><div className="skeleton skeleton-line" /></td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (!employees.length) {
    return (
      <div className="empty-state">
        <p className="empty-title">No employees found</p>
        <p className="empty-text">{emptyMessage}</p>
      </div>
    );
  }

  const hasActions = Boolean(onSoftDelete || onHardDelete);

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>Employee</th>
            {!compact && <th>Job title</th>}
            <th>Department</th>
            <th>Status</th>
            {!compact && <th>Salary</th>}
            <th>Hire date</th>
            {hasActions && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee.id}>
              <td>
                <div className="employee-cell">
                  <span className="avatar" aria-hidden="true">
                    {initials(employee.first_name, employee.last_name)}
                  </span>
                  <span className="employee-cell-text">
                    <Link
                      to={`/employees/${employee.id}`}
                      className="employee-name"
                    >
                      {employee.first_name} {employee.last_name}
                    </Link>
                    <span className="employee-meta">
                      {employee.employee_code} · {employee.email}
                    </span>
                  </span>
                </div>
              </td>
              {!compact && <td>{employee.job_title}</td>}
              <td>{employee.department_name}</td>
              <td>
                <StatusBadge status={employee.status} />
              </td>
              {!compact && <td>{formatCurrency(employee.salary)}</td>}
              <td>{formatDate(employee.hire_date)}</td>
              {hasActions && (
                <td>
                  <div className="row-actions">
                    <Link
                      to={`/employees/${employee.id}`}
                      className="btn btn-sm btn-ghost"
                    >
                      View
                    </Link>
                    <Link
                      to={`/employees/${employee.id}/edit`}
                      className="btn btn-sm btn-ghost"
                    >
                      Edit
                    </Link>
                    {onSoftDelete && employee.status !== "terminated" && (
                      <button
                        type="button"
                        className="btn btn-sm btn-warning-ghost"
                        onClick={() => onSoftDelete(employee)}
                      >
                        Terminate
                      </button>
                    )}
                    {onHardDelete && (
                      <button
                        type="button"
                        className="btn btn-sm btn-danger-ghost"
                        onClick={() => onHardDelete(employee)}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default memo(EmployeeTable);
