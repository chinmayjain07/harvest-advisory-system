"""
Dashboard HTTP Server for Intelligent Harvest Advisory Pipeline.
Exposes REST API endpoints for simulation stepping, manual upload, daily sync,
and visualizes forecasts and replay progress in a modern web UI.
"""

import io
import json
import os
import sys
import cgi
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Setup path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from replay_service import ReplayService
from daily_updater import DailyUpdater
from upload_service import MandiUploadService
from retrain_service import ForecastRefresher

UI_HTML_PATH = PROJECT_ROOT / "ui" / "index.html"
FORECAST_FILE = PROJECT_ROOT / "reports" / "latest_forecasts.json"


class DashboardHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status_code: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, content: bytes, status_code: int = 200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        url_path = self.path.split("?")[0]

        if url_path in ["/", "/index.html"]:
            if UI_HTML_PATH.exists():
                with open(UI_HTML_PATH, "rb") as f:
                    self._send_html(f.read())
            else:
                self._send_html(b"<h1>UI HTML file missing.</h1>", 404)

        elif url_path == "/api/forecasts":
            if FORECAST_FILE.exists():
                with open(FORECAST_FILE, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception:
                        data = {}
                self._send_json(data)
            else:
                # Generate on the fly
                refresher = ForecastRefresher()
                data = refresher.refresh_all_forecasts()
                self._send_json(data)

        elif url_path == "/api/simulation/status":
            replay = ReplayService()
            status = replay.get_status()
            self._send_json(status)

        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        url_path = self.path.split("?")[0]

        if url_path == "/api/simulation/step":
            replay = ReplayService()
            res = replay.step_forward()
            self._send_json(res)

        elif url_path == "/api/simulation/reset":
            replay = ReplayService()
            res = replay.reset_simulation()
            self._send_json(res)

        elif url_path == "/api/sync":
            updater = DailyUpdater()
            res = updater.run_daily_sync()
            self._send_json(res)

        elif url_path == "/api/upload":
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers["Content-Type"]}
                )
                if "file" in form:
                    file_item = form["file"]
                    file_bytes = file_item.file.read()
                    uploader = MandiUploadService()
                    res = uploader.process_uploaded_file(io.BytesIO(file_bytes))
                    self._send_json(res)
                    return
            self._send_json({"success": False, "message": "No file uploaded"}, 400)

        else:
            self._send_json({"error": "Endpoint not found"}, 404)


def run_server(port: int = 8000):
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"==================================================")
    print(f"HARVEST ADVISORY CONTROL PANEL RUNNING AT:")
    print(f"http://127.0.0.1:{port}/")
    print(f"==================================================")
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
