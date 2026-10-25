"""Irrigation and Alerts composition root. Run locally: python -m services.irrigation_alerts.app"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time
from .alert_rule_service import AlertRuleService
from .api import IrrigationAlertsApi
from .farm_events import FixtureFarmEventSource
from .farm_projection import FarmAccessProjection
from .irrigation_service import IrrigationService
from .repository import InMemoryIrrigationRepository

MAX_BODY = 65536


def create_server(host="127.0.0.1", port=8003, clock=time.time):
    projection = FarmAccessProjection()
    events = FixtureFarmEventSource(projection, clock)
    api = IrrigationAlertsApi(IrrigationService(InMemoryIrrigationRepository(), projection, events, clock),
                              AlertRuleService(projection, events, clock))

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, headers, payload):
            data = b"" if status == 204 else json.dumps(payload, allow_nan=False).encode("utf-8")
            self.send_response(status)
            if status != 204:  # 204 No Content carries no body or entity headers
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def handle_request(self):
            # Local HTTP transport only; HTTPS belongs to the proposed managed gateway.
            if self.headers.get("Transfer-Encoding"):
                return self.respond(400, {}, {"error": {"code": "INVALID_FRAMING", "message": "Chunked bodies are unsupported."}})
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = -1
            if size < 0:
                return self.respond(400, {}, {"error": {"code": "INVALID_LENGTH", "message": "Invalid Content-Length."}})
            if size > MAX_BODY:
                return self.respond(413, {}, {"error": {"code": "BODY_TOO_LARGE", "message": "Body exceeds 65536 bytes."}})
            self.connection.settimeout(5)
            try:
                body = self.rfile.read(size)
            except TimeoutError:
                return self.respond(408, {}, {"error": {"code": "REQUEST_TIMEOUT", "message": "Request body timed out."}})
            if len(body) != size:
                return self.respond(400, {}, {"error": {"code": "INCOMPLETE_BODY", "message": "Incomplete request body."}})
            status, headers, payload = api.dispatch(self.command, self.path,
                self.headers.get("Authorization", ""), self.headers.get("Content-Type", ""), body)
            self.respond(status, headers, payload)

        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = handle_request

    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()
    server = create_server(port=args.port)
    print("Irrigation and Alerts demo: http://127.0.0.1:" + str(args.port), flush=True)
    print("Local fixtures only. In-memory state resets on restart. Seeded farms: farm-001, farm-002, farm-003 (stalled).", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
