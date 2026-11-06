"""Small in-memory cache for report endpoints (Step 5).

Reports are read-heavy and change only when an employee or department is
written. A short TTL keeps the UI fast without serving stale data for long.
Every write endpoint calls ``invalidate_report_cache()``.
"""

import threading
import time
from functools import wraps

from flask import Response, current_app, jsonify, request

# key -> (stored_at_monotonic, payload)
_cache = {}
_lock = threading.Lock()


def invalidate_report_cache():
    """Clear all cached report responses. Called after any write."""
    with _lock:
        _cache.clear()


def get_cached(key):
    """Return a cached payload if it exists and has not expired."""
    now = time.monotonic()
    with _lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        stored_at, payload = entry
        ttl = current_app.config.get("REPORT_CACHE_TTL", 15)
        if now - stored_at < ttl:
            return payload
        del _cache[key]
        return None


def set_cached(key, payload):
    """Store a report payload with the current timestamp."""
    with _lock:
        _cache[key] = (time.monotonic(), payload)


def cached_report(producer):
    """Decorator: cache a JSON report response for a short time.

    The cache key includes the path and query string, so different filters
    do not collide. Responses carry an ``X-Cache`` header (HIT, MISS, or
    BYPASS) to make the behaviour visible in tests and during profiling.
    CSV responses bypass the cache because they are streamed downloads.
    """

    @wraps(producer)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("REPORT_CACHE_ENABLED", True):
            result = producer(*args, **kwargs)
            return _make_response(result, "BYPASS")

        key = request.path + "?" + request.query_string.decode("utf-8")
        payload = get_cached(key)
        if payload is not None:
            return _make_response(payload, "HIT")

        result = producer(*args, **kwargs)
        # Only cache plain JSON dictionaries; errors and CSV are not cached.
        if isinstance(result, dict):
            set_cached(key, result)
            return _make_response(result, "MISS")
        return _make_response(result, "BYPASS")

    return wrapper


def _make_response(result, cache_header):
    """Turn a producer result into a Flask response with an X-Cache header."""
    if isinstance(result, Response):
        result.headers["X-Cache"] = "BYPASS"
        return result

    if isinstance(result, tuple):
        payload, status_code = result
        response = jsonify(payload)
        response.status_code = status_code
    else:
        response = jsonify(result)

    response.headers["X-Cache"] = cache_header
    return response
