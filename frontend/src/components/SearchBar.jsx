/**
 * Controlled search input. The parent owns the value so it can debounce it
 * (see `useDebounce`) before calling the API.
 */
export default function SearchBar({
  value,
  onChange,
  placeholder = "Search by name, email, or employee code…",
  label = "Search employees",
}) {
  return (
    <div className="search-field">
      <span className="search-icon" aria-hidden="true">
        ⌕
      </span>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={label}
        autoComplete="off"
      />
      {value && (
        <button
          type="button"
          className="search-clear"
          onClick={() => onChange("")}
          aria-label="Clear search"
        >
          ×
        </button>
      )}
    </div>
  );
}
