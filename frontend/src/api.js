/**
 * Tiny fetch wrapper around the Flask API.
 *
 * All URLs are relative (`/api/...`) so the Vite dev server can proxy them
 * to Flask. The same build works when the frontend is served from any host.
 */

const API_BASE = "/api";

export class ApiError extends Error {
  constructor(message, status, fields) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields || {};
  }
}

function queryString(params) {
  if (!params) return "";
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

async function request(path, options = {}) {
  const { body, headers, ...rest } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(headers || {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const message =
      (payload && payload.error) || `Request failed with status ${response.status}.`;
    throw new ApiError(message, response.status, payload?.fields);
  }

  return payload;
}

export const api = {
  // Employees
  getEmployees: (params) => request(`/employees${queryString(params)}`),
  getEmployee: (id) => request(`/employees/${id}`),
  createEmployee: (payload) =>
    request("/employees", { method: "POST", body: payload }),
  updateEmployee: (id, payload) =>
    request(`/employees/${id}`, { method: "PUT", body: payload }),
  deleteEmployee: (id, hard = false) =>
    request(`/employees/${id}${hard ? "?hard=true" : ""}`, { method: "DELETE" }),

  // Departments
  getDepartments: () => request("/departments"),
  createDepartment: (payload) =>
    request("/departments", { method: "POST", body: payload }),
  updateDepartment: (id, payload) =>
    request(`/departments/${id}`, { method: "PUT", body: payload }),
  deleteDepartment: (id) =>
    request(`/departments/${id}`, { method: "DELETE" }),

  // Reports
  getReport: (name, params) => request(`/reports/${name}${queryString(params)}`),

  /** Trigger a browser download for a CSV report. */
  downloadCsv: (name, params) => {
    const url = `${API_BASE}/reports/${name}${queryString(params)}`;
    const link = document.createElement("a");
    link.href = url;
    link.download = "";
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};
