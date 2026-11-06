import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import { useNotification } from "../hooks/useNotification";
import { api } from "../api";
import {
  formatCurrency,
  formatDate,
  formatDateTime,
  initials,
} from "../utils";

export default function EmployeeDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { notify } = useNotification();

  const [employee, setEmployee] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState({ open: false, mode: "soft" });
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.getEmployee(id);
      setEmployee(response.data);
    } catch (err) {
      setError(err.message || "Could not load this employee.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const requestSoftDelete = () => setDialog({ open: true, mode: "soft" });
  const requestHardDelete = () => setDialog({ open: true, mode: "hard" });
  const closeDialog = () => setDialog({ open: false, mode: "soft" });

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      await api.deleteEmployee(employee.id, dialog.mode === "hard");
      notify(
        dialog.mode === "hard"
          ? `${employee.first_name} ${employee.last_name} was permanently deleted.`
          : `${employee.first_name} ${employee.last_name} was marked as terminated.`,
        "success",
      );
      navigate("/employees");
    } catch (err) {
      notify(err.message || "The employee could not be deleted.", "error");
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-loader">
        <Spinner label="Loading employee" />
        <p>Loading employee…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-stack">
        <div className="alert alert-error" role="alert">
          <p>{error}</p>
          <Link to="/employees" className="btn btn-sm btn-secondary">
            Back to employees
          </Link>
        </div>
      </div>
    );
  }

  const fullName = `${employee.first_name} ${employee.last_name}`;
  const dialogCopy =
    dialog.mode === "hard"
      ? {
          title: "Delete employee permanently?",
          message: `This will permanently remove ${fullName} from the database. This action cannot be undone.`,
        }
      : {
          title: "Terminate employee?",
          message: `Mark ${fullName} as terminated? They will be hidden from the default employee list.`,
        };

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <Link to="/employees" className="back-link">
            ← Back to employees
          </Link>
          <div className="detail-title-row">
            <span className="avatar avatar-large" aria-hidden="true">
              {initials(employee.first_name, employee.last_name)}
            </span>
            <div>
              <h1>{fullName}</h1>
              <p className="page-subtitle">
                {employee.job_title} · {employee.department_name}
              </p>
            </div>
            <StatusBadge status={employee.status} />
          </div>
        </div>
        <div className="page-actions">
          <Link to={`/employees/${employee.id}/edit`} className="btn btn-secondary">
            Edit
          </Link>
          {employee.status !== "terminated" && (
            <button type="button" className="btn btn-warning" onClick={requestSoftDelete}>
              Terminate
            </button>
          )}
          <button type="button" className="btn btn-danger" onClick={requestHardDelete}>
            Delete permanently
          </button>
        </div>
      </div>

      {employee.status === "terminated" && (
        <div className="alert alert-warning" role="status">
          <p>
            This employee is terminated. The record is retained for reporting but
            hidden from the default employee list.
          </p>
        </div>
      )}

      <section className="card">
        <div className="card-heading">
          <div>
            <h2>Employee record</h2>
            <p>Complete details for {fullName}.</p>
          </div>
          <span className="record-code">{employee.employee_code}</span>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Email</dt>
            <dd>{employee.email}</dd>
          </div>
          <div>
            <dt>Phone</dt>
            <dd>{employee.phone || "—"}</dd>
          </div>
          <div>
            <dt>Department</dt>
            <dd>{employee.department_name}</dd>
          </div>
          <div>
            <dt>Job title</dt>
            <dd>{employee.job_title}</dd>
          </div>
          <div>
            <dt>Salary</dt>
            <dd>{formatCurrency(employee.salary)}</dd>
          </div>
          <div>
            <dt>Hire date</dt>
            <dd>{formatDate(employee.hire_date)}</dd>
          </div>
          <div>
            <dt>Date of birth</dt>
            <dd>{formatDate(employee.date_of_birth)}</dd>
          </div>
          <div>
            <dt>Gender</dt>
            <dd>{employee.gender || "—"}</dd>
          </div>
          <div className="detail-full">
            <dt>Address</dt>
            <dd>{employee.address || "—"}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{formatDateTime(employee.created_at)}</dd>
          </div>
          <div>
            <dt>Last updated</dt>
            <dd>{formatDateTime(employee.updated_at)}</dd>
          </div>
        </dl>
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
