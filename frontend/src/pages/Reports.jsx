import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import EmployeeTable from "../components/EmployeeTable";
import Spinner from "../components/Spinner";
import { useNotification } from "../hooks/useNotification";
import { api } from "../api";
import { formatCurrency, formatNumber } from "../utils";

const STATUS_COLORS = {
  active: "#0f766e",
  on_leave: "#d97706",
  terminated: "#b91c1c",
};

const STATUS_LABELS = {
  active: "Active",
  on_leave: "On leave",
  terminated: "Terminated",
};

export default function Reports() {
  const { notify } = useNotification();

  const [headcount, setHeadcount] = useState([]);
  const [salary, setSalary] = useState(null);
  const [status, setStatus] = useState([]);
  const [hires, setHires] = useState({ count: 0, data: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [appliedRange, setAppliedRange] = useState({ from: "", to: "" });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [headcountResponse, salaryResponse, statusResponse, hiresResponse] =
        await Promise.all([
          api.getReport("headcount-by-department"),
          api.getReport("salary-summary"),
          api.getReport("status-breakdown"),
          api.getReport("new-hires", appliedRange),
        ]);
      setHeadcount(headcountResponse.data);
      setSalary({ data: salaryResponse.data, meta: salaryResponse.meta });
      setStatus(statusResponse.data);
      setHires({ count: hiresResponse.count, data: hiresResponse.data });
    } catch (err) {
      setError(err.message || "Could not load reports.");
    } finally {
      setLoading(false);
    }
  }, [appliedRange]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const totalEmployees = useMemo(
    () => headcount.reduce((sum, row) => sum + row.headcount, 0),
    [headcount],
  );
  const chartData = useMemo(
    () =>
      headcount.map((row) => ({
        name: row.department_name,
        headcount: row.headcount,
      })),
    [headcount],
  );
  const statusChartData = useMemo(
    () =>
      status.map((row) => ({
        name: STATUS_LABELS[row.status] ?? row.status,
        value: row.count,
        status: row.status,
      })),
    [status],
  );

  const applyRange = (event) => {
    event.preventDefault();
    setAppliedRange({ from, to });
  };

  const exportCsv = (name) => {
    api.downloadCsv(name);
    notify("CSV download started.", "info");
  };

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">Insights</p>
          <h1>Reports</h1>
          <p className="page-subtitle">
            Headcount, payroll, and hiring insights. Export any report to CSV.
          </p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => exportCsv("headcount-by-department")}
          >
            Export headcount CSV
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => exportCsv("employee-directory")}
          >
            Export directory CSV
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

      <section className="stats-grid" aria-label="Report summary">
        <article className="stat-card">
          <p className="stat-label">Total employees</p>
          <p className="stat-value">
            {loading ? <Spinner label="Loading total" /> : formatNumber(totalEmployees)}
          </p>
          <p className="stat-hint">All departments</p>
        </article>
        <article className="stat-card stat-active">
          <p className="stat-label">Total payroll</p>
          <p className="stat-value stat-value-small">
            {loading || !salary ? (
              <Spinner label="Loading payroll" />
            ) : (
              formatCurrency(salary.meta.total_payroll)
            )}
          </p>
          <p className="stat-hint">Excludes terminated employees</p>
        </article>
        <article className="stat-card stat-neutral">
          <p className="stat-label">Average salary</p>
          <p className="stat-value stat-value-small">
            {loading || !salary ? (
              <Spinner label="Loading average salary" />
            ) : (
              formatCurrency(salary.meta.average_salary)
            )}
          </p>
          <p className="stat-hint">Across current employees</p>
        </article>
        <article className="stat-card stat-warning">
          <p className="stat-label">New hires</p>
          <p className="stat-value">
            {loading ? <Spinner label="Loading new hires" /> : formatNumber(hires.count)}
          </p>
          <p className="stat-hint">
            {appliedRange.from || appliedRange.to
              ? `${appliedRange.from || "start"} → ${appliedRange.to || "today"}`
              : "All time"}
          </p>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="card chart-card">
          <div className="card-heading">
            <div>
              <h2>Headcount by department</h2>
              <p>Total employees per department.</p>
            </div>
          </div>
          <div className="chart-area">
            {loading ? (
              <div className="chart-placeholder">
                <Spinner label="Loading chart" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tickLine={false} axisLine={false} />
                  <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Bar dataKey="headcount" fill="#0f766e" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </article>

        <article className="card chart-card">
          <div className="card-heading">
            <div>
              <h2>Status breakdown</h2>
              <p>Employees by current status.</p>
            </div>
          </div>
          <div className="chart-area">
            {loading ? (
              <div className="chart-placeholder">
                <Spinner label="Loading chart" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusChartData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="52%"
                    outerRadius="78%"
                    paddingAngle={2}
                  >
                    {statusChartData.map((entry) => (
                      <Cell
                        key={entry.status}
                        fill={STATUS_COLORS[entry.status] ?? "#94a3b8"}
                      />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </article>
      </section>

      <section className="card">
        <div className="card-heading">
          <div>
            <h2>Salary summary</h2>
            <p>Minimum, maximum, average, and total salary per department.</p>
          </div>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            onClick={() => exportCsv("salary-summary")}
          >
            Export salary CSV
          </button>
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Department</th>
                <th>Employees</th>
                <th>Minimum</th>
                <th>Maximum</th>
                <th>Average</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {loading || !salary ? (
                <tr>
                  <td colSpan={6}>
                    <div className="chart-placeholder">
                      <Spinner label="Loading salary summary" />
                    </div>
                  </td>
                </tr>
              ) : (
                salary.data.map((row) => (
                  <tr key={row.department_id}>
                    <td>{row.department_name}</td>
                    <td>{formatNumber(row.employee_count)}</td>
                    <td>{formatCurrency(row.min_salary)}</td>
                    <td>{formatCurrency(row.max_salary)}</td>
                    <td>{formatCurrency(row.average_salary)}</td>
                    <td>{formatCurrency(row.total_salary)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <div className="card-heading">
          <div>
            <h2>New hires</h2>
            <p>Filter by hire date and export the employee directory.</p>
          </div>
          <form className="inline-form" onSubmit={applyRange}>
            <label className="field">
              <span>From</span>
              <input type="date" value={from} onChange={(event) => setFrom(event.target.value)} />
            </label>
            <label className="field">
              <span>To</span>
              <input type="date" value={to} onChange={(event) => setTo(event.target.value)} />
            </label>
            <button type="submit" className="btn btn-sm btn-primary">
              Apply
            </button>
          </form>
        </div>
        <EmployeeTable
          employees={hires.data.slice(0, 10)}
          loading={loading}
          compact
          emptyMessage="No employees were hired in this date range."
        />
        {hires.count > 10 && (
          <p className="table-hint">
            Showing the 10 most recent of {hires.count} new hires.{" "}
            <Link to="/employees" className="text-link">
              Browse all employees
            </Link>
          </p>
        )}
      </section>
    </div>
  );
}
