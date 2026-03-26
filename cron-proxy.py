#!/usr/bin/env python3
"""
Tiny HTTP proxy that accepts cron job requests and runs openclaw CLI on the host.
Listens on 0.0.0.0:18799 so Docker containers can reach it via host.docker.internal.

This is needed because:
1. The openclaw CLI isn't installed inside Docker containers
2. The gateway's /tools/invoke HTTP API doesn't expose cron.* methods
3. The gateway's WebSocket RPC requires device identity for admin scopes

This proxy bridges the gap by accepting simple HTTP requests and translating
them into openclaw CLI calls on the host.
"""
import http.server
import json
import os
import subprocess

OPENCLAW = os.environ.get(
    "OPENCLAW_BIN",
    os.path.expanduser("~/.nvm/versions/node/v22.19.0/bin/openclaw"),
)
NODE = os.environ.get(
    "NODE_BIN",
    os.path.expanduser("~/.nvm/versions/node/v22.19.0/bin/node"),
)
ENV = {
    **os.environ,
    "PATH": os.path.dirname(NODE) + ":" + os.environ.get("PATH", ""),
}


class CronProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}

        if self.path == "/cron/add":
            cmd = [
                NODE, OPENCLAW, "cron", "add",
                "--name", body["name"],
                "--cron", body["cron"],
                "--tz", body.get("tz", "America/New_York"),
                "--session", body.get("session", "isolated"),
                "--message", body["message"],
                "--no-deliver",
                "--json",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, env=ENV,
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    data = {"raw": result.stdout.strip()}
                resp = {"ok": True, "result": data}
            else:
                resp = {"ok": False, "error": (result.stdout + result.stderr).strip()}

        elif self.path == "/cron/remove":
            job_id = body.get("jobId", "")
            result = subprocess.run(
                [NODE, OPENCLAW, "cron", "remove", job_id],
                capture_output=True, text=True, timeout=10, env=ENV,
            )
            resp = {"ok": result.returncode == 0}

        elif self.path == "/cron/list":
            result = subprocess.run(
                [NODE, OPENCLAW, "cron", "list", "--json"],
                capture_output=True, text=True, timeout=10, env=ENV,
            )
            try:
                data = json.loads(result.stdout) if result.returncode == 0 else []
            except json.JSONDecodeError:
                data = []
            resp = {"ok": result.returncode == 0, "result": data}

        elif self.path == "/health":
            resp = {"ok": True, "service": "cron-proxy"}

        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())

    def log_message(self, fmt, *args):
        # Suppress normal request logging; errors still go to stderr
        pass


if __name__ == "__main__":
    port = int(os.environ.get("CRON_PROXY_PORT", "18799"))
    server = http.server.HTTPServer(("0.0.0.0", port), CronProxyHandler)
    print(f"OpenClaw cron proxy listening on 0.0.0.0:{port}")
    server.serve_forever()
