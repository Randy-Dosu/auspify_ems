import { lazy, Suspense, useEffect } from "react";
import {
  BrowserRouter,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import Navbar from "./components/Navbar";
import PageLoader from "./components/PageLoader";
import { NotificationProvider } from "./context/NotificationContext";

// Route pages are lazy-loaded so the initial bundle stays small (Step 5).
const Dashboard = lazy(() => import("./pages/Dashboard"));
const EmployeeList = lazy(() => import("./pages/EmployeeList"));
const EmployeeForm = lazy(() => import("./pages/EmployeeForm"));
const EmployeeDetails = lazy(() => import("./pages/EmployeeDetails"));
const Departments = lazy(() => import("./pages/Departments"));
const Reports = lazy(() => import("./pages/Reports"));
const NotFound = lazy(() => import("./pages/NotFound"));

/** Scroll to the top whenever the route changes. */
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <NotificationProvider>
      <BrowserRouter>
        <ScrollToTop />
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        <div className="app-shell">
          <Navbar />
          <main id="main-content" className="main-content">
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/employees" element={<EmployeeList />} />
                <Route path="/employees/new" element={<EmployeeForm />} />
                <Route path="/employees/:id" element={<EmployeeDetails />} />
                <Route path="/employees/:id/edit" element={<EmployeeForm />} />
                <Route path="/departments" element={<Departments />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </main>
          <footer className="app-footer">
            <p>
              <strong>Auspify EMS</strong> · Employee Management System
            </p>
          </footer>
        </div>
      </BrowserRouter>
    </NotificationProvider>
  );
}
