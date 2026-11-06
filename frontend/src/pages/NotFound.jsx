import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="page-stack">
      <div className="card empty-state not-found">
        <p className="eyebrow">404</p>
        <h1>Page not found</h1>
        <p className="empty-text">
          The page you are looking for does not exist or has moved.
        </p>
        <Link to="/" className="btn btn-primary">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
