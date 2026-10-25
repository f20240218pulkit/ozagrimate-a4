"""REST Controller for the Irrigation and Alerts container (shared routing).

Routes Thomas's irrigation-request operations and Bradley's alert-rule operations.
"""
import json
import re
from urllib.parse import urlsplit
from .models import ApiError
from .security import authenticate

FARM = r"/farms/(farm-[0-9]+)"
ROUTES = [
    # (pattern, allowed method, handler name)
    (re.compile(FARM + r"/irrigation-requests"), "POST", "create_irrigation_request"),
    (re.compile(FARM + r"/irrigation-requests/(irr-[0-9]+)"), "PUT", "replace_irrigation_request"),
    (re.compile(FARM + r"/alert-rules"), "POST", "create_alert_rule"),
    (re.compile(FARM + r"/alert-rules/(rule-[0-9]+)"), "DELETE", "delete_alert_rule"),
]


def reject_constant(value):
    raise ValueError("Nonstandard JSON number: " + value)


def parse_json(content_type, body):
    if content_type.split(";", 1)[0].strip().lower() != "application/json":
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Use application/json.")
    try:
        return json.loads(body.decode("utf-8"), parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ApiError(400, "INVALID_JSON", "Request body must be valid UTF-8 JSON.")


class IrrigationAlertsApi:
    def __init__(self, irrigation_service, alert_rule_service):
        self.irrigation = irrigation_service
        self.alert_rules = alert_rule_service

    def dispatch(self, method, target, authorization="", content_type="", body=b""):
        try:
            path = urlsplit(target).path
            for pattern, allowed, handler in ROUTES:
                match = pattern.fullmatch(path)
                if match:
                    break
            else:
                raise ApiError(404, "ROUTE_NOT_FOUND", "Endpoint not found.")
            if method != allowed:
                return 405, {"Allow": allowed}, {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed."}}
            principal = authenticate(authorization)
            return getattr(self, handler)(principal, *match.groups(), content_type=content_type, body=body)
        except ApiError as error:
            headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else {}
            if error.status == 503:
                headers["Retry-After"] = "5"
            return error.status, headers, {"error": {"code": error.code, "message": error.message}}

    def create_irrigation_request(self, principal, farm_id, content_type, body):
        payload = parse_json(content_type, body)
        record = self.irrigation.create(principal, farm_id, payload)
        location = "/farms/" + farm_id + "/irrigation-requests/" + record.id
        return 201, {"Location": location}, record.public()

    def replace_irrigation_request(self, principal, farm_id, request_id, content_type, body):
        payload = parse_json(content_type, body)
        return 200, {}, self.irrigation.replace(principal, farm_id, request_id, payload).public()

    def create_alert_rule(self, principal, farm_id, content_type, body):
        payload = parse_json(content_type, body)
        rule = self.alert_rules.create(principal, farm_id, payload)
        return 201, {"Location": "/farms/" + farm_id + "/alert-rules/" + rule["ruleId"]}, rule

    def delete_alert_rule(self, principal, farm_id, rule_id, content_type, body):
        self.alert_rules.delete(principal, farm_id, rule_id)
        return 204, {}, None
