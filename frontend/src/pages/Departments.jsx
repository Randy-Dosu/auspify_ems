import { useCallback, useEffect, useState } from "react";
import ConfirmDialog from "../components/ConfirmDialog";
import Spinner from "../components/Spinner";
import { useNotification } from "../hooks/useNotification";
import { api } from "../api";
import { formatNumber } from "../utils";

const EMPTY_FORM = { name: "", description: "", manager_id: "" };

export default function Departments() {
  const { notify } = useNotification();

  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formErrors, setFormErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [departmentResponse, employeeResponse] = await Promise.all([
        api.getDepartments(),
        api.getEmployees({ per_page: 100, include_terminated: true }),
      ]);
      setDepartments(departmentResponse.data);
      setEmployees(employeeResponse.data);
    } catch (err) {
      setError(err.message || "Could not load departments.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormErrors({});
    setServerError("");
    setModalOpen(true);
  };

  const openEdit = (department) => {
    setEditingId(department.id);
    setForm({
      name: department.name,
      description: department.description ?? "",
      manager_id: department.manager_id ? String(department.manager_id) : "",
    });
    setFormErrors({});
    setServerError("");
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
    setFormErrors({});
    setServerError("");
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFormErrors((current) => ({ ...current, [name]: undefined }));
    setServerError("");
  };

  const validate = () => {
    const errors = {};
    if (!form.name.trim()) {
      errors.name = "Department name is required.";
    } else if (form.name.trim().length < 2) {
      errors.name = "Use at least 2 characters.";
    } else if (form.name.trim().length > 100) {
      errors.name = "Use at most 100 characters.";
    }
    if (form.description.length > 500) {
      errors.description = "Use at most 500 characters.";
    }
    return errors;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const errors = validate();
    setFormErrors(errors);
    if (Object.keys(errors).length) return;

    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      manager_id: form.manager_id ? Number(form.manager_id) : null,
    };

    setSubmitting(true);
    setServerError("");
    try {
      if (editingId) {
        await api.updateDepartment(editingId, payload);
        notify("Department updated successfully.", "success");
      } else {
        await api.createDepartment(payload);
        notify("Department created successfully.", "success");
      }
      closeModal();
      await load();
    } catch (err) {
      setServerError(err.message || "The department could not be saved.");
      if (err.fields) setFormErrors(err.fields);
      notify(err.message || "The department could not be saved.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.deleteDepartment(deleteTarget.id);
      notify(`${deleteTarget.name} was deleted.`, "success");
      setDeleteTarget(null);
      await load();
    } catch (err) {
      notify(err.message || "The department could not be deleted.", "error");
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  const sortedEmployees = [...employees].sort((a, b) =>
    `${a.first_name} ${a.last_name}`.localeCompare(`${b.first_name} ${b.last_name}`),
  );

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">Organisation</p>
          <h1>Departments</h1>
          <p className="page-subtitle">
            Organise employees into departments and assign managers.
          </p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            Add department
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          <p>{error}</p>
          <button type="button" className="btn btn-sm btn-secondary" onClick={load}>
            Try again
          </button>
        </div>
      )}

      {loading ? (
        <div className="page-loader">
          <Spinner label="Loading departments" />
          <p>Loading departments…</p>
        </div>
      ) : departments.length === 0 ? (
        <div className="card empty-state">
          <p className="empty-title">No departments yet</p>
          <p className="empty-text">Create your first department to get started.</p>
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            Add department
          </button>
        </div>
      ) : (
        <section className="department-grid" aria-label="Departments">
          {departments.map((department) => (
            <article key={department.id} className="card department-card">
              <div className="department-card-head">
                <div>
                  <h2>{department.name}</h2>
                  <p className="department-manager">
                    Manager: {department.manager_name || "Unassigned"}
                  </p>
                </div>
                <span className="count-pill">
                  {formatNumber(department.employee_count)} employees
                </span>
              </div>
              <p className="department-description">
                {department.description || "No description provided."}
              </p>
              <div className="department-meta">
                <span>{department.active_employee_count} active</span>
                <span>
                  {department.employee_count - department.active_employee_count} inactive
                </span>
              </div>
              <div className="department-actions">
                <button
                  type="button"
                  className="btn btn-sm btn-secondary"
                  onClick={() => openEdit(department)}
                >
                  Edit
                </button>
                <button
                  type="button"
                  className="btn btn-sm btn-danger-ghost"
                  onClick={() => setDeleteTarget(department)}
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </section>
      )}

      {modalOpen && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !submitting) closeModal();
          }}
        >
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="department-modal-title"
          >
            <div className="modal-header">
              <h2 id="department-modal-title">
                {editingId ? "Edit department" : "Add department"}
              </h2>
              <button
                type="button"
                className="modal-close"
                onClick={closeModal}
                aria-label="Close dialog"
                disabled={submitting}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} noValidate>
              <div className="modal-body">
                {serverError && (
                  <div className="alert alert-error" role="alert">
                    <p>{serverError}</p>
                  </div>
                )}
                <div className="form-grid">
                  <label className="field field-full">
                    <span>
                      Name <span className="required">*</span>
                    </span>
                    <input
                      name="name"
                      value={form.name}
                      onChange={handleChange}
                      className={formErrors.name ? "is-invalid" : ""}
                      placeholder="e.g. Operations"
                      autoFocus
                    />
                    {formErrors.name && (
                      <span className="field-error" role="alert">
                        {formErrors.name}
                      </span>
                    )}
                  </label>
                  <label className="field field-full">
                    <span>Description</span>
                    <textarea
                      name="description"
                      rows={3}
                      value={form.description}
                      onChange={handleChange}
                      placeholder="What does this department do?"
                    />
                    {formErrors.description && (
                      <span className="field-error" role="alert">
                        {formErrors.description}
                      </span>
                    )}
                  </label>
                  <label className="field field-full">
                    <span>Manager</span>
                    <select
                      value={form.manager_id}
                      onChange={handleChange}
                      name="manager_id"
                    >
                      <option value="">Unassigned</option>
                      {sortedEmployees.map((employee) => (
                        <option key={employee.id} value={employee.id}>
                          {employee.first_name} {employee.last_name} · {employee.job_title}
                        </option>
                      ))}
                    </select>
                    {formErrors.manager_id && (
                      <span className="field-error" role="alert">
                        {formErrors.manager_id}
                      </span>
                    )}
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={closeModal}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Saving…" : editingId ? "Save changes" : "Create department"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete department?"
        message={
          deleteTarget
            ? `Delete ${deleteTarget.name}? A department with employees cannot be deleted; reassign or remove its employees first.`
            : ""
        }
        confirmLabel="Delete department"
        danger
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
