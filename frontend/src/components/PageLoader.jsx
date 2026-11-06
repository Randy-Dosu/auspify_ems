import Spinner from "./Spinner";

/** Fallback shown while a lazily-loaded route chunk is downloading. */
export default function PageLoader() {
  return (
    <div className="page-loader">
      <Spinner label="Loading page" />
      <p>Loading page…</p>
    </div>
  );
}
