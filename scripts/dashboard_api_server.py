#!/usr/bin/env python3
import json
import os
import posixpath
import subprocess
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

HOST = "127.0.0.1"
PORT = 8001

DASHBOARD_DIR = "/Users/gayathri/Library/CloudStorage/OneDrive-AnthologyInc/Documents/Power Bi"
DASHBOARD_FILE = "Galaxy PR Metrics Dashboard.html"
DASHBOARD_PATH = os.path.join(DASHBOARD_DIR, DASHBOARD_FILE)

REFRESH_SCRIPT = "/Users/gayathri/galaxy-dashboards/scripts/refresh_galaxy_prs.py"
GENERATE_SCRIPT = "/Users/gayathri/galaxy-dashboards/scripts/generate_dashboard.py"
PYTHON_BIN = "/usr/bin/python3"

state_lock = threading.Lock()
state = {
    "running": False,
    "last_started": None,
    "last_completed": None,
    "last_ok": None,
    "last_error": None,
    "last_duration_sec": None,
}


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def json_response(handler, payload, status=200):
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(data)


def run_refresh_pipeline():
    started = time.time()
    with state_lock:
        if state["running"]:
            return False, "Refresh already in progress"
        state["running"] = True
        state["last_started"] = now_iso()
        state["last_error"] = None

    try:
        env = os.environ.copy()

        refresh = subprocess.run(
            [PYTHON_BIN, REFRESH_SCRIPT],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(REFRESH_SCRIPT),
            env=env,
            timeout=1800,
        )
        if refresh.returncode != 0:
            err = (refresh.stderr or refresh.stdout or "refresh_galaxy_prs.py failed").strip()
            raise RuntimeError(err[-3000:])

        generate = subprocess.run(
            [PYTHON_BIN, GENERATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(GENERATE_SCRIPT),
            env=env,
            timeout=600,
        )
        if generate.returncode != 0:
            err = (generate.stderr or generate.stdout or "generate_dashboard.py failed").strip()
            raise RuntimeError(err[-3000:])

        duration = round(time.time() - started, 2)
        with state_lock:
            state["running"] = False
            state["last_completed"] = now_iso()
            state["last_ok"] = True
            state["last_duration_sec"] = duration
            state["last_error"] = None
        return True, f"Refresh completed in {duration}s"

    except Exception as exc:
        duration = round(time.time() - started, 2)
        with state_lock:
            state["running"] = False
            state["last_completed"] = now_iso()
            state["last_ok"] = False
            state["last_duration_sec"] = duration
            state["last_error"] = str(exc)
        return False, str(exc)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            with state_lock:
                payload = dict(state)
            return json_response(self, payload)

        if path == "/api/refresh/galaxy-pr":
            ok, message = run_refresh_pipeline()
            with state_lock:
                payload = {
                    "ok": ok,
                    "message": message,
                    **state,
                }
            return json_response(self, payload, status=200 if ok else 500)

        self.serve_static(path)

    def serve_static(self, path):
        if path in ("/", ""):
            rel = DASHBOARD_FILE
        else:
            rel = unquote(path.lstrip("/"))

        rel = posixpath.normpath(rel)
        if rel.startswith("../") or rel == "..":
            self.send_error(403, "Forbidden")
            return

        full_path = os.path.join(DASHBOARD_DIR, rel)
        if not os.path.isfile(full_path):
            self.send_error(404, "File not found")
            return

        ctype = "text/html; charset=utf-8" if full_path.endswith(".html") else "application/octet-stream"
        with open(full_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[{now_iso()}] {self.address_string()} {fmt % args}")


def main():
    if not os.path.exists(DASHBOARD_PATH):
        raise FileNotFoundError(f"Dashboard file not found: {DASHBOARD_PATH}")

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Dashboard API server running at http://{HOST}:{PORT}")
    print(f"Serving directory: {DASHBOARD_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
