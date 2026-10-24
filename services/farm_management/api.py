"""REST adapter for farm and alert-rule endpoints."""
import json
import re
from urllib.parse import urlsplit
from .models import ApiError
from .security import authenticate
from .alerts import AlertRuleService


def reject_constant(value):
    raise ValueError("Nonstandard JSON number: " + value)


class FarmApi:
    def __init__(self, service):
        self.service = service
        self.alerts = AlertRuleService(service)

    def dispatch(self, method, target, authorization="", content_type="", body=b""):
        try:
            path = urlsplit(target).path
            item = re.fullmatch(r"/farms/(farm-[0-9]+)", path)
            alert = re.fullmatch(
                r"/farms/(farm-[0-9]+)/alert-rules(?:/(rule-[0-9]+))?", path
            )
            if path != "/farms" and item is None and alert is None:
                raise ApiError(404, "ROUTE_NOT_FOUND", "Endpoint not found.")
            allowed = "POST" if path == "/farms" else "GET"
            if alert:
                allowed = "DELETE" if alert.group(2) else "POST"
            if method != allowed:
                return 405, {"Allow": allowed}, {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed."}}
            principal = authenticate(authorization)

            if alert and method == "DELETE":
                self.alerts.delete(principal, alert.group(1), alert.group(2))
                return 204, {}, None

            if method == "GET":
                return 200, {}, self.service.get(principal, item.group(1)).public()
            if content_type.split(";", 1)[0].strip().lower() != "application/json":
                raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Use application/json.")
            try:
                payload = json.loads(body.decode("utf-8"), parse_constant=reject_constant)
            except (ValueError, UnicodeError, RecursionError):
                raise ApiError(400, "INVALID_JSON", "Request body must be valid UTF-8 JSON.")

            if alert:
                rule = self.alerts.create(principal, alert.group(1), payload)
                return 201, {"Location": path + "/" + rule["ruleId"]}, rule

            farm = self.service.create(principal, payload)
            return 201, {"Location": "/farms/" + farm.id}, farm.public()
        except ApiError as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else {}
            return error.status, headers, {"error": {"code": error.code, "message": error.message}}
