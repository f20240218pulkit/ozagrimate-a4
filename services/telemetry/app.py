"""Telemetry composition root (HTTP Server). Run locally: python -m services.telemetry.app"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time
from .anomaly_detector import AnomalyDetector
from .api import TelemetryApi
from .event_publisher import AcceptedReadingPublisher
from .farm_access import FarmAccessReadModel
from .ingestion_service import TelemetryIngestionService
from .query_service import TelemetryQueryService
from .repository import InMemoryTelemetryRepository

MAX_BODY = 65536


def create_server(host="127.0.0.1", port=8002, clock=time.time):
    repository = InMemoryTelemetryRepository()
    farm_access = FarmAccessReadModel()
    publisher = AcceptedReadingPublisher()
    api = TelemetryApi(
        TelemetryIngestionService(repository, farm_access, AnomalyDetector(repository), publisher, clock),
        TelemetryQueryService(repository, farm_access))

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, headers, payload):
            data = json.dumps(payload, allow_nan=False).encode("utf-8")
            self.send_response(status)
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

    server = ThreadingHTTPServer((host, port), Handler)
    server.publisher = publisher  # exposes the outbox to tests; no broker is deployed
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()
    server = create_server(port=args.port)
    print("Telemetry demo: http://127.0.0.1:" + str(args.port), flush=True)
    print("Local fixtures only. In-memory state resets on restart. Seeded readings on farm-001 and farm-002.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
