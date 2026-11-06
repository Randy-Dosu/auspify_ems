import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Spinner from "../components/Spinner";
import { useNotification } from "../hooks/useNotification";
import { api } from "../api";
import { todayISO } from "../utils";

const EMPTY_FORM = {
  employee_code: "",
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  date_of_birth: "",
  gender: "",
  job_title: "",
  department_id: "",
  salary: "",
  hire_date: "",
  status: "active",
  address: "",
};

function employeeToForm(employee) {
  return {
    employee_code: employee.employee_code ?? "",
    first_name: employee.first_name ?? "",
    last_name: employee.last_name ?? "",
    email: employee.email ?? "",
    phone: employee.phone ?? "",
    date_of_birth: employee.date_of_birth ?? "",
    gender: employee.gender ?? "",
    job_title: employee.job_title ?? "",
    department_id: employee.department_id ? String(employee.department_id) : "",
    salary: employee.salary ?? "",
    hire_date: employee.hire_date ?? "",
    status: employee.status ?? "active",
    address: employee.address ?? "",
  };
}

function Field({
  label,
  htmlFor,
  error,
  help,
  required,
  children,
  className = "",
}) {
  return (
    <div className={`field ${className}`.trim()}>
      <label htmlFor={htmlFor}>
        {label}
        {required && <span className="required"> *</span>}
      </label>
      {children}
      {help && <span className="help-text">{help}</span>}
      {error && (
        <span className="field-error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export default function EmployeeForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const { notify } = useNotification();

  const [form, setForm] = useState(EMPTY_FORM);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const today = todayISO();

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setLoadError("");
      try {
        const [departmentResponse, employeeResponse] = await Promise.all([
          api.getDepartments(),
          isEdit ? api.getEmployee(id) : Promise.resolve(null),
        ]);
        if (cancelled) return;
        setDepartments(departmentResponse.data);
        if (employeeResponse) {
          setForm(employeeToForm(employeeResponse.data));
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(err.message || "Could not load the employee form.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [id, isEdit]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
    setServerError("");
  };

  const validate = () => {
    const errors = {};
    if (!form.first_name.trim()) errors.first_name = "First name is required.";
    if (!form.last_name.trim()) errors.last_name = "Last name is required.";
    if (!form.email.trim()) {
      errors.email = "Email is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      errors.email = "Enter a valid email address.";
    }
    if (!form.job_title.trim()) errors.job_title = "Job title is required.";
    if (!form.department_id) errors.department_id = "Select a department.";
    if (!form.hire_date) {
      errors.hire_date = "Hire date is required.";
    } else if (form.hire_date > today) {
      errors.hire_date = "Hire date cannot be in the future.";
    }
    if (form.date_of_birth && form.date_of_birth > today) {
      errors.date_of_birth = "Date of birth cannot be in the future.";
    }
    if (form.salary === "" || Number.isNaN(Number(form.salary))) {
      errors.salary = "Enter a valid salary.";
    } else if (Number(form.salary) < 0) {
      errors.salary = "Salary cannot be negative.";
    }
    if (
      form.employee_code.trim() &&
      !/^[A-Za-z0-9_-]{3,20}$/.test(form.employee_code.trim())
    ) {
      errors.employee_code = "Use 3–20 letters, numbers, hyphens, or underscores.";
    }
    return errors;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length) {
      notify("Please fix the highlighted fields.", "error");
      return;
    }

    const payload = {
      employee_code: form.employee_code.trim() || undefined,
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || null,
      date_of_birth: form.date_of_birth || null,
      gender: form.gender || null,
      job_title: form.job_title.trim(),
      department_id: Number(form.department_id),
      salary: form.salary === "" ? 0 : Number(form.salary),
      hire_date: form.hire_date,
      status: form.status,
      address: form.address.trim() || null,
    };

    setSubmitting(true);
    setServerError("");
    try {
      const response = isEdit
        ? await api.updateEmployee(id, payload)
        : await api.createEmployee(payload);
      notify(
        isEdit ? "Employee updated successfully." : "Employee registered successfully.",
        "success",
      );
      navigate(`/employees/${response.data.id}`);
    } catch (err) {
      setServerError(err.message || "The employee could not be saved.");
      if (err.fields) setFieldErrors(err.fields);
      notify(err.message || "The employee could not be saved.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-loader">
        <Spinner label="Loading form" />
        <p>Loading form…</p>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="page-stack">
        <div className="alert alert-error" role="alert">
          <p>{loadError}</p>
          <Link to="/employees" className="btn btn-sm btn-secondary">
            Back to employees
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <Link to={isEdit ? `/employees/${id}` : "/employees"} className="back-link">
            ← Back
          </Link>
          <h1>{isEdit ? "Edit employee" : "Add employee"}</h1>
          <p className="page-subtitle">
            {isEdit
              ? "Update the employee record. Changes are saved immediately."
              : "Register a new employee. Fields marked * are required."}
          </p>
        </div>
      </div>

      {serverError && (
        <div className="alert alert-error" role="alert">
          <p>{serverError}</p>
        </div>
      )}

      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Personal details</h2>
              <p>Basic information about the employee.</p>
            </div>
          </div>
          <div className="form-grid">
            <Field
              label="First name"
              htmlFor="first_name"
              required
              error={fieldErrors.first_name}
            >
              <input
                id="first_name"
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
                className={fieldErrors.first_name ? "is-invalid" : ""}
                autoComplete="given-name"
              />
            </Field>
            <Field
              label="Last name"
              htmlFor="last_name"
              required
              error={fieldErrors.last_name}
            >
              <input
                id="last_name"
                name="last_name"
                value={form.last_name}
                onChange={handleChange}
                className={fieldErrors.last_name ? "is-invalid" : ""}
                autoComplete="family-name"
              />
            </Field>
            <Field
              label="Email"
              htmlFor="email"
              required
              error={fieldErrors.email}
            >
              <input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                className={fieldErrors.email ? "is-invalid" : ""}
                autoComplete="email"
              />
            </Field>
            <Field label="Phone" htmlFor="phone" error={fieldErrors.phone}>
              <input
                id="phone"
                name="phone"
                value={form.phone}
                onChange={handleChange}
                autoComplete="tel"
              />
            </Field>
            <Field
              label="Date of birth"
              htmlFor="date_of_birth"
              error={fieldErrors.date_of_birth}
            >
              <input
                id="date_of_birth"
                name="date_of_birth"
                type="date"
                max={today}
                value={form.date_of_birth}
                onChange={handleChange}
              />
            </Field>
            <Field label="Gender" htmlFor="gender" error={fieldErrors.gender}>
              <select
                id="gender"
                name="gender"
                value={form.gender}
                onChange={handleChange}
              >
                <option value="">Not specified</option>
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Other">Other</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            </Field>
            <Field
              label="Address"
              htmlFor="address"
              error={fieldErrors.address}
              className="field-full"
            >
              <textarea
                id="address"
                name="address"
                rows={3}
                value={form.address}
                onChange={handleChange}
              />
            </Field>
          </div>
        </section>

        <section className="card">
          <div className="card-heading">
            <div>
              <h2>Employment details</h2>
              <p>Role, department, compensation, and status.</p>
            </div>
          </div>
          <div className="form-grid">
            <Field
              label="Employee code"
              htmlFor="employee_code"
              help="Leave blank to auto-generate, e.g. EMP-0026."
              error={fieldErrors.employee_code}
            >
              <input
                id="employee_code"
                name="employee_code"
                value={form.employee_code}
                onChange={handleChange}
                placeholder="Auto-generated"
                className={fieldErrors.employee_code ? "is-invalid" : ""}
              />
            </Field>
            <Field
              label="Job title"
              htmlFor="job_title"
              required
              error={fieldErrors.job_title}
            >
              <input
                id="job_title"
                name="job_title"
                value={form.job_title}
                onChange={handleChange}
                className={fieldErrors.job_title ? "is-invalid" : ""}
              />
            </Field>
            <Field
              label="Department"
              htmlFor="department_id"
              required
              error={fieldErrors.department_id}
            >
              <select
                id="department_id"
                name="department_id"
                value={form.department_id}
                onChange={handleChange}
                className={fieldErrors.department_id ? "is-invalid" : ""}
              >
                <option value="">Select a department</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Salary (GHS)" htmlFor="salary" required error={fieldErrors.salary}>
              <input
                id="salary"
                name="salary"
                type="number"
                min="0"
                step="0.01"
                value={form.salary}
                onChange={handleChange}
                className={fieldErrors.salary ? "is-invalid" : ""}
              />
            </Field>
            <Field
              label="Hire date"
              htmlFor="hire_date"
              required
              error={fieldErrors.hire_date}
            >
              <input
                id="hire_date"
                name="hire_date"
                type="date"
                max={today}
                value={form.hire_date}
                onChange={handleChange}
                className={fieldErrors.hire_date ? "is-invalid" : ""}
              />
            </Field>
            <Field label="Status" htmlFor="status" error={fieldErrors.status}>
              <select
                id="status"
                name="status"
                value={form.status}
                onChange={handleChange}
              >
                <option value="active">Active</option>
                <option value="on_leave">On leave</option>
                <option value="terminated">Terminated</option>
              </select>
            </Field>
          </div>
        </section>

        <div className="form-actions">
          <Link
            to={isEdit ? `/employees/${id}` : "/employees"}
            className="btn btn-secondary"
          >
            Cancel
          </Link>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Saving…" : isEdit ? "Save changes" : "Register employee"}
          </button>
        </div>
      </form>
    </div>
  );
}
