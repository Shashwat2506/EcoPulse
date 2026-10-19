"""
EcoPulse: Smart Sustainability Tracker
Flask Application Factory & Route Definitions
"""

import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from config import Config
import database as db
from calculations import calculate_total_footprint, validate_metric_input

def create_app(config_class=Config) -> Flask:
    """Application factory for EcoPulse."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize the database
    with app.app_context():
        db.init_db(app.config.get("DATABASE_PATH"))

    # Register Routes
    @app.route("/")
    def index():
        """Main dashboard view."""
        entries = db.get_all_entries(app.config.get("DATABASE_PATH"))
        active_entry = None

        # Check if an entry_id was requested in query string
        selected_id = request.args.get("entry_id")
        if selected_id:
            try:
                active_entry = db.get_entry_by_id(int(selected_id), app.config.get("DATABASE_PATH"))
            except (ValueError, TypeError):
                active_entry = None

        # If no specific entry selected, default to latest entry or fresh default
        if not active_entry and entries:
            active_entry = db.get_entry_by_id(entries[-1]["id"], app.config.get("DATABASE_PATH"))

        # Default fallback calculation if no entries exist yet
        if not active_entry:
            default_calc = calculate_total_footprint({})
            active_entry = {
                "id": None,
                "title": "New Assessment",
                "inputs": default_calc["inputs"],
                "calculations": default_calc,
                "created_at": None,
                "is_new": True
            }

        return render_template(
            "index.html",
            entries=entries,
            active_entry=active_entry,
            config=app.config
        )

    @app.route("/about")
    def about():
        """About and methodology page."""
        return render_template("about.html")

    @app.route("/healthz")
    def health_check():
        """Kubernetes/Docker liveness and readiness health probe."""
        db_ok = True
        try:
            conn = db.get_connection(app.config.get("DATABASE_PATH"))
            conn.execute("SELECT 1;").fetchone()
            conn.close()
        except Exception:
            db_ok = False

        status_code = 200 if db_ok else 503
        return jsonify({
            "status": "healthy" if db_ok else "unhealthy",
            "service": "ecopulse",
            "database": "connected" if db_ok else "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), status_code

    # RESTful API Endpoints
    @app.route("/api/entries", methods=["GET"])
    def list_entries():
        """List all saved footprint logs."""
        entries = db.get_all_entries(app.config.get("DATABASE_PATH"))
        return jsonify({
            "count": len(entries),
            "entries": entries
        })

    @app.route("/api/entries", methods=["POST"])
    def create_new_entry():
        """Save a new sustainability assessment log."""
        data = request.get_json() or {}
        title = data.get("title")

        is_valid, errors, cleaned = validate_metric_input(data)
        if not is_valid:
            return jsonify({
                "success": False,
                "message": "Validation failed.",
                "errors": errors
            }), 400

        entry = db.create_entry(cleaned, title=title, db_path=app.config.get("DATABASE_PATH"))
        return jsonify({
            "success": True,
            "message": "Assessment log saved successfully.",
            "entry": entry
        }), 201

    @app.route("/api/entries/<int:entry_id>", methods=["GET"])
    def get_entry(entry_id: int):
        """Retrieve a specific entry with full calculation breakdown."""
        entry = db.get_entry_by_id(entry_id, app.config.get("DATABASE_PATH"))
        if not entry:
            return jsonify({"success": False, "message": "Entry not found."}), 404
        return jsonify({
            "success": True,
            "entry": entry
        })

    @app.route("/api/entries/<int:entry_id>", methods=["PUT"])
    def update_entry(entry_id: int):
        """Update an existing assessment log."""
        data = request.get_json() or {}
        title = data.get("title")

        is_valid, errors, cleaned = validate_metric_input(data)
        if not is_valid:
            return jsonify({
                "success": False,
                "message": "Validation failed.",
                "errors": errors
            }), 400

        updated = db.update_entry(entry_id, cleaned, title=title, db_path=app.config.get("DATABASE_PATH"))
        if not updated:
            return jsonify({"success": False, "message": "Entry not found to update."}), 404

        return jsonify({
            "success": True,
            "message": "Assessment log updated successfully.",
            "entry": updated
        })

    @app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
    def delete_entry(entry_id: int):
        """Delete an assessment log."""
        success = db.delete_entry(entry_id, app.config.get("DATABASE_PATH"))
        if not success:
            return jsonify({"success": False, "message": "Entry not found or already deleted."}), 404

        return jsonify({
            "success": True,
            "message": "Assessment log deleted successfully."
        })

    @app.route("/api/history", methods=["GET"])
    def get_history():
        """Retrieve timeline data for historical trends."""
        history = db.get_history_summary(app.config.get("DATABASE_PATH"))
        return jsonify({
            "success": True,
            "history": history,
            "benchmarks": {
                "global_average": Config.BENCHMARK_GLOBAL_AVG,
                "us_average": Config.BENCHMARK_US_AVG,
                "eu_average": Config.BENCHMARK_EU_AVG,
                "paris_target": Config.BENCHMARK_PARIS_TARGET
            }
        })

    @app.route("/api/calculate", methods=["POST"])
    def calculate_preview():
        """Live metric preview without committing to database."""
        data = request.get_json() or {}
        is_valid, errors, cleaned = validate_metric_input(data)
        calc = calculate_total_footprint(cleaned, Config)
        return jsonify({
            "is_valid": is_valid,
            "errors": errors,
            "calculations": calc
        })

    # Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Resource not found."}), 404
        return render_template("base.html", error="404 - Page Not Found"), 404

    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Internal server error."}), 500
        return render_template("base.html", error="500 - Internal Server Error"), 500

    return app

# Application entry point for Gunicorn and direct execution
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
