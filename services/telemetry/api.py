"""Telemetry REST Controller (owner: Aditya).

Routes the two Telemetry endpoints and maps errors to the team JSON envelope
{"error": {"code": "...", "message": "..."}}:
  POST /farms/{farmId}/telemetry   submit one reading (edge gateway)
  GET  /farms/{farmId}/telemetry   list a farm's readings (owner / granted worker)
"""
import json
import re
from urllib.parse import urlsplit
from .models import ApiError
from .security import authenticate

TELEMETRY = re.compile(r"/farms/(farm-[0-9]+)/telemetry")
ALLOWED = ("GET", "POST")


def reject_constant(value):
    raise ValueError("Nonstandard JSON number: " + value)


def parse_json(content_type, body):
    if content_type.split(";", 1)[0].strip().lower() != "application/json":
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Use application/json.")
    try:
        return json.loads(body.decode("utf-8"), parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ApiError(400, "INVALID_JSON", "Request body must be valid UTF-8 JSON.")


class TelemetryApi:
    def __init__(self, ingestion_service, query_service):
        self.ingestion = ingestion_service
        self.queries = query_service

    def dispatch(self, method, target, authorization="", content_type="", body=b""):
        try:
            parts = urlsplit(target)
            match = TELEMETRY.fullmatch(parts.path)
            if match is None:
                raise ApiError(404, "ROUTE_NOT_FOUND", "Endpoint not found.")
            if method not in ALLOWED:
                return 405, {"Allow": ", ".join(ALLOWED)}, {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed."}}
            principal = authenticate(authorization)
            farm_id = match.group(1)
            if method == "GET":
                return 200, {}, self.queries.list(principal, farm_id, parts.query)
            reading, created = self.ingestion.submit(principal, farm_id, parse_json(content_type, body))
            # 201 for a newly stored reading; 200 when an identical replay returns the original.
            return (201 if created else 200), {}, reading.public()
        except ApiError as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else {}
            return error.status, headers, {"error": {"code": error.code, "message": error.message}}
