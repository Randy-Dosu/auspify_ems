"""
Auspify EMS - Employee Management System API.

The application factory creates the Flask app, ensures the SQLite schema
exists, registers the API blueprints, and adds JSON error handlers. The app
starts with an empty database; there is no demo or seed data.

Run locally:
    python app.py
Then open: http://127.0.0.1:5000/api/health
"""

import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS

from database import close_db, get_db, init_db
from routes.departments import departments_bp
from routes.employees import employees_bp
from routes.reports import reports_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.environ.get(
    "EMS_DB_PATH", os.path.join(BASE_DIR, "ems.db")
)


def create_app(config=None) -> Flask:
    """Application factory (also used by the pytest suite)."""
    app = Flask(__name__)
    app.config.from_mapping(
        DB_PATH=DEFAULT_DB_PATH,
        REPORT_CACHE_ENABLED=True,
        REPORT_CACHE_TTL=15,
        SQLITE_WAL=True,
        JSON_SORT_KEYS=False,
    )

    if config:
        app.config.update(config)

    # Allow the Vite dev server and hosted preview to call the API.
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Create the schema on first run. Tests pass a temporary path.
    init_db(app.config["DB_PATH"], wal=app.config["SQLITE_WAL"])

    app.register_blueprint(employees_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(reports_bp)

    app.teardown_appcontext(close_db)

    @app.get("/api/health")
    def health():
        """Liveness probe with a real database round-trip."""
        try:
            db = get_db()
            db.execute("SELECT 1").fetchone()
            database = "ok"
        except sqlite3.Error:
            database = "unavailable"

        return (
            jsonify(
                {
                    "status": "ok" if database == "ok" else "degraded",
                    "service": "Auspify EMS API",
                    "version": "1.0.0",
                    "step": 5,
                    "database": database,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            200 if database == "ok" else 503,
        )

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify({"error": "Internal server error."}), 500

    return app


# Module-level app instance for `flask --app app run` and `python app.py`.
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
