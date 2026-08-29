#!/usr/bin/env python3
"""
SIH26170 - Backend REST API & Frontend Static Web Server
=============================================================================
Zero-dependency HTTP server providing REST API endpoints and serving the
interactive frontend dashboard.

Endpoints:
- GET  /                           -> Serves frontend/index.html
- GET  /frontend/<file>            -> Serves frontend static assets (CSS, JS)
- GET  /api/dataset-sample         -> Returns sampled dataset points for scatterplots
- POST /api/pipeline/run           -> Master screening flow with auto-scaling & AI explanation
- POST /api/predict                -> Fast prediction only
- POST /api/chat                   -> Conversational AI chat with DB logging
- GET  /api/history                -> Query SQLite screening records
- GET  /api/models                 -> Model parameters & scaler statistics
- GET  /api/stats                  -> Screening summary stats
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.pipeline import ScreeningPipeline
    from backend.scaler import MINMAX_BOUNDS, MinMaxScaler
except (ImportError, ModuleNotFoundError):
    from pipeline import ScreeningPipeline
    from scaler import MINMAX_BOUNDS, MinMaxScaler

# Global master pipeline instance
pipeline_instance = ScreeningPipeline()

FRONTEND_DIR = ROOT_DIR / "frontend"
DATASET_DIR = ROOT_DIR / "final_data" / "dataset"


def sample_dataset(model_type: str, max_points: int = 150):
    """Load and sample (X, Y) points from dataset CSV for scatterplot rendering."""
    m_key = model_type.lower().replace("-", "").replace("_", "")
    if "break" in m_key:
        csv_file = DATASET_DIR / "Breakdown.csv"
        x_col, y_col = "Collector_Emitter_Voltage_Vce", "Leakage_Current_Ic"
    elif "leak" in m_key:
        csv_file = DATASET_DIR / "LeakageIV.csv"
        x_col, y_col = "Applied_Voltage", "Leakage_Current"
    elif "turn" in m_key or "on" in m_key:
        csv_file = DATASET_DIR / "TurnOn.csv"
        x_col, y_col = "Gate_Voltage", "Collector_Current"
    else:
        return []

    if not csv_file.exists():
        # Fallback to drafts if dataset not in final_data/dataset
        csv_file = ROOT_DIR / "final_data" / "drafts" / f"{csv_file.name}"

    points = []
    if csv_file.exists():
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)
            step = max(1, len(all_rows) // max_points)
            for row in all_rows[::step][:max_points]:
                try:
                    y_raw = float(row[y_col])
                    # If in Amperes (< 0.1), scale to microAmpere (uA)
                    y_micro = y_raw * 1e6 if y_raw < 0.1 else y_raw
                    t_val = float(row.get("time_minutes", 0.0))
                    points.append({
                        "t": t_val,
                        "x": float(row[x_col]),
                        "y": y_micro
                    })
                except (ValueError, KeyError):
                    continue
    return points


class BackendAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for REST APIs and Frontend Static Files."""

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. Frontend Static Files Serving
        if path in ("/", "/index.html"):
            index_file = FRONTEND_DIR / "index.html"
            if index_file.exists():
                self._set_headers(200, "text/html; charset=utf-8")
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"Frontend not found. Please create frontend/index.html.")
            return

        elif path.startswith("/frontend/") or path in ("/styles.css", "/app.js"):
            file_name = path.replace("/frontend/", "").lstrip("/")
            target_file = FRONTEND_DIR / file_name
            if target_file.exists() and target_file.is_file():
                ext = target_file.suffix.lower()
                mime = "text/css" if ext == ".css" else ("application/javascript" if ext == ".js" else "text/plain")
                self._set_headers(200, f"{mime}; charset=utf-8")
                with open(target_file, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"File not found.")
                return

        # 2. REST API Endpoints
        elif path == "/api/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "healthy",
                "service": "SIH26170-Fullstack-System",
                "ai_provider": pipeline_instance.chatbot.api_client.provider
            }).encode("utf-8"))

        elif path == "/api/models":
            self._set_headers(200)
            self.wfile.write(json.dumps(MINMAX_BOUNDS).encode("utf-8"))

        elif path == "/api/timeseries-data":
            model_type = query.get("model", ["breakdown"])[0]
            limit = int(query.get("limit", [120])[0])
            ts_data = pipeline_instance.model_engine.get_timeseries_data(model_type, max_points=limit)
            self._set_headers(200)
            self.wfile.write(json.dumps(ts_data).encode("utf-8"))

        elif path == "/api/dataset-sample":
            model_type = query.get("model", ["breakdown"])[0]
            limit = int(query.get("limit", [150])[0])
            points = sample_dataset(model_type, max_points=limit)
            self._set_headers(200)
            self.wfile.write(json.dumps({"model": model_type, "count": len(points), "points": points}).encode("utf-8"))

        elif path == "/api/stats":
            stats = pipeline_instance.database.get_summary_stats()
            self._set_headers(200)
            self.wfile.write(json.dumps(stats).encode("utf-8"))

        elif path in ("/api/history", "/api/screenings"):
            limit = int(query.get("limit", [50])[0])
            offset = int(query.get("offset", [0])[0])
            model_type = query.get("model_type", [None])[0]
            risk_decision = query.get("risk_decision", [None])[0]

            records = pipeline_instance.database.get_screenings(
                limit=limit,
                offset=offset,
                model_type=model_type,
                risk_decision=risk_decision
            )
            self._set_headers(200)
            self.wfile.write(json.dumps({"total": len(records), "records": records, "screenings": records}).encode("utf-8"))

        elif path.startswith("/api/history/") or path.startswith("/api/screenings/"):
            try:
                rec_id = int(path.split("/")[-1])
                rec = pipeline_instance.database.get_screening_by_id(rec_id)
                if rec:
                    self._set_headers(200)
                    self.wfile.write(json.dumps(rec).encode("utf-8"))
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": f"Record {rec_id} not found"}).encode("utf-8"))
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid record ID"}).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "API endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON format"}).encode("utf-8"))
            return

        if path == "/api/pipeline/run":
            model_type = data.get("model_type", "breakdown")
            try:
                raw_input = float(data["raw_input"])
            except (KeyError, ValueError, TypeError):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "'raw_input' must be a valid number"}).encode("utf-8"))
                return

            user_said_output = float(data["user_said_output"]) if "user_said_output" in data and data["user_said_output"] is not None else None
            component_id = data.get("component_id", "DUT-01")
            use_ai = data.get("use_ai", True)

            time_minutes = float(data["time_minutes"]) if "time_minutes" in data and data["time_minutes"] is not None else None

            try:
                result = pipeline_instance.process_screening(
                    model_type=model_type,
                    raw_input=raw_input,
                    user_said_output=user_said_output,
                    component_id=component_id,
                    time_minutes=time_minutes,
                    use_ai=use_ai
                )
                self._set_headers(200)
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/predict":
            model_type = data.get("model_type", "breakdown")
            try:
                raw_input = float(data["raw_input"])
            except (KeyError, ValueError, TypeError):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "'raw_input' must be a valid number"}).encode("utf-8"))
                return

            try:
                pred = pipeline_instance.model_engine.predict(model_type, raw_input)
                self._set_headers(200)
                self.wfile.write(json.dumps(pred).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/chat":
            message = data.get("message", "")
            session_id = data.get("session_id", "default_session")
            if not message:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "'message' is required"}).encode("utf-8"))
                return

            try:
                chat_res = pipeline_instance.chat(message, session_id=session_id)
                self._set_headers(200)
                self.wfile.write(json.dumps(chat_res).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/config":
            provider = data.get("provider", "offline")
            key = data.get("api_key", None)
            pipeline_instance.chatbot.set_api_key(provider, key)
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "updated",
                "active_provider": provider,
                "has_key": bool(key)
            }).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="SIH26170 Backend & Frontend Web Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, BackendAPIHandler)
    print("=" * 75)
    print(f" SIH26170 Semiconductor Screening Web Application")
    print(f" Frontend & API active at http://{args.host}:{args.port}/")
    print(f" SQLite Database: {pipeline_instance.database.db_path}")
    print(f" AI Explainer Engine: {pipeline_instance.chatbot.api_client.provider.upper()}")
    print("=" * 75)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n Stopping server...")
        httpd.server_close()


if __name__ == "__main__":
    main()
