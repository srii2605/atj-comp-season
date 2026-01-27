import os
import csv
import io
import logging

import requests
from flask import Flask, jsonify, render_template, send_from_directory, abort

app = Flask(__name__, static_folder="static", template_folder="templates")

# Configure logging (Render captures stdout/stderr)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def sheet_csv_url() -> str:
    """Read the Google Sheet CSV URL from the environment."""
    return os.getenv("SHEET_CSV_URL", "").strip()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/data")
def data():
    url = sheet_csv_url()
    if not url:
        app.logger.error("SHEET_CSV_URL is not set")
        return jsonify({"error": "SHEET_CSV_URL is not set"}), 500

    try:
        app.logger.info("Fetching CSV from Google Sheets…")
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()

        text = resp.text
        if not text.strip():
            app.logger.error("CSV response was empty")
            return jsonify({"error": "CSV response was empty"}), 502

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        app.logger.info(
            "Parsed %d rows, %d columns",
            len(rows),
            len(reader.fieldnames or []),
        )
        return jsonify(rows)

    except requests.exceptions.Timeout:
        app.logger.exception("Timeout fetching CSV")
        return jsonify({"error": "Timeout fetching CSV"}), 504

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else 500
        app.logger.exception("HTTPError fetching CSV: status=%s", status)
        # 502 Bad Gateway since upstream (Google) failed
        return jsonify({"error": f"Upstream returned HTTP {status}"}), 502

    except Exception as e:
        app.logger.exception("Unexpected error fetching/parsing CSV")
        return jsonify({"error": "Unexpected error", "detail": str(e)}), 500


@app.route("/favicon.ico")
def favicon():
    # Serve favicon if it exists; otherwise 404 (harmless)
    try:
        return send_from_directory(app.static_folder, "favicon.ico")
    except Exception:
        abort(404)


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    # Render provides $PORT; default to 5050 for local runs
    port = int(os.environ.get("PORT", "5050"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
