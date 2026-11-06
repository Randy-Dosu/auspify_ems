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

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [recent, setRecent] = useState([]);
  const [headcount, setHeadcount] = useState([]);
  const [status, setStatus] = useState([]);
  const [salary, setSalary] = useState(null);
  const [departmentCount, setDepartmentCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [recentResponse, departments, headcountResponse, statusResponse, salaryResponse] =
        await Promise.all([
          api.getEmployees({ per_page: 5, sort: "hire_date", order: "desc" }),
          api.getDepartments(),
          api.getReport("headcount-by-department"),
          api.getReport("status-breakdown"),
          api.getReport("salary-summary"),
        ]);
      setRecent(recentResponse.data);
      setDepartmentCount(departments.meta.total);
      setHeadcount(headcountResponse.data);
      setStatus(statusResponse.data);
      setSalary(salaryResponse.meta);
    } catch (err) {
      setError(err.message || "Could not load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const totalEmployees = useMemo(
    () => headcount.reduce((sum, row) => sum + row.headcount, 0),
    [headcount],
  );
  const statusCounts = useMemo(
    () => Object.fromEntries(status.map((row) => [row.status, row.count])),
    [status],
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

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Dashboard</h1>
          <p className="page-subtitle">
            A live snapshot of your organisation&apos;s people and payroll.
          </p>
        </div>
        <div className="page-actions">
          <Link to="/reports" className="btn btn-secondary">
            View reports
          </Link>
          <Link to="/employees/new" className="btn btn-primary">
            Add employee
          </Link>
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

      <section className="stats-grid" aria-label="Key metrics">
        <article className="stat-card">
          <p className="stat-label">Total employees</p>
          <p className="stat-value">
            {loading ? <Spinner label="Loading total employees" /> : formatNumber(totalEmployees)}
          </p>
          <p className="stat-hint">
            {departmentCount
              ? `Across ${departmentCount} departments`
              : "No departments yet"}
          </p>
        </article>
        <article className="stat-card stat-active">
          <p className="stat-label">Active</p>
          <p className="stat-value">
            {loading ? <Spinner label="Loading active employees" /> : formatNumber(statusCounts.active ?? 0)}
          </p>
          <p className="stat-hint">Currently working</p>
        </article>
        <article className="stat-card stat-warning">
          <p className="stat-label">On leave</p>
          <p className="stat-value">
            {loading ? <Spinner label="Loading employees on leave" /> : formatNumber(statusCounts.on_leave ?? 0)}
          </p>
          <p className="stat-hint">Temporary absence</p>
        </article>
        <article className="stat-card stat-neutral">
          <p className="stat-label">Total payroll</p>
          <p className="stat-value stat-value-small">
            {loading || !salary ? <Spinner label="Loading payroll" /> : formatCurrency(salary.total_payroll)}
          </p>
          <p className="stat-hint">
            {salary ? `${formatCurrency(salary.average_salary)} average` : "Excludes terminated"}
          </p>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="card chart-card">
          <div className="card-heading">
            <div>
              <h2>Headcount by department</h2>
              <p>Active, on-leave, and terminated employees per department.</p>
            </div>
            <Link to="/reports" className="text-link">
              Details
            </Link>
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
              <p>Distribution of employee statuses.</p>
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
            <h2>Recent hires</h2>
            <p>The five newest members of the team.</p>
          </div>
          <Link to="/employees" className="text-link">
            View all employees
          </Link>
        </div>
        <EmployeeTable
          employees={recent}
          loading={loading}
          compact
          emptyMessage="No employees have been hired yet."
        />
      </section>
    </div>
  );
}
