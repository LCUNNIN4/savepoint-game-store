"""Flask entry point. Run python app.py to start the local store."""
from datetime import date, datetime
from decimal import Decimal

import mysql.connector
from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider

from routes import customers, games, genres, orders, publishers, stats
from utils import ApiError


class JSONProvider(DefaultJSONProvider):
    """Serialize MySQL decimal and date values."""

    def default(self, value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="seconds")
        if isinstance(value, date):
            return value.isoformat()
        return super().default(value)


app = Flask(__name__, static_folder="static", static_url_path="")
app.json = JSONProvider(app)

for module in (publishers, genres, games, customers, orders, stats):
    app.register_blueprint(module.bp)


@app.get("/")
def home():
    """Serve the single-page frontend."""
    return app.send_static_file("index.html")


# API error responses

@app.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({"error": error.message}), error.status


@app.errorhandler(mysql.connector.Error)
def handle_database_error(error):
    """Map database constraint failures to API responses."""
    messages = {
        1062: ("That already exists (duplicate value).", 409),          # UNIQUE
        1451: ("Cannot delete: other records still refer to this.", 409),  # FK RESTRICT
        1452: ("A referenced record does not exist.", 400),             # FK missing parent
        3819: ("A value is outside its allowed range.", 400),           # CHECK
    }
    if error.errno in messages:
        message, status = messages[error.errno]
        return jsonify({"error": message}), status
    app.logger.exception("Database error")
    return jsonify({"error": "Database error. Is MySQL running and .env correct?"}), 500


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def handle_bad_method(error):
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(debug=True)
