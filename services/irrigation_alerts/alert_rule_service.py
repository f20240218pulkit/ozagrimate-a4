"""Alert Rule Application Service (owner: Bradley).

Use cases: create a sensor alert rule and delete one. Rule validation, storage and
the evaluate() incident logic are Bradley's implementation, moved here from
Farm Management so alert rules live in the Irrigation and Alerts container (ADR-01).

Farm existence and access are checked against this service's own Farm Access
Projection (ADR-07), not Farm Management's store. Only farm owners manage rules.
evaluate() is the planned hook for accepted-reading events; no endpoint exposes it.
"""
from math import isfinite
from threading import Lock
from time import monotonic
from .models import ApiError

# Metric catalogue for alert rules. It mirrors the Telemetry reading contract (ADR-06)
# so a rule can only be written in the unit that accepted readings use. A rule's
# sensorId is matched against the reading's deviceId (for example "sm-north-01").
METRIC_UNITS = {
    "soilMoisture": "%",
    "soilTemperature": "degC",
    "airTemperature": "degC",
    "rainfall": "mm",
}


def finite_number(value):
    try:
        return type(value) in (int, float) and isfinite(value)
    except OverflowError:
        return False


class AlertRuleService:
    def __init__(self, projection, event_source, clock):
        self.projection = projection
        self.event_source = event_source
        self.clock = clock
        self.rules = {}
        self.states = {}
        self.notifications = []
        self._next_id = 1
        self._lock = Lock()

    def authorise(self, principal, farm_id):
        if principal.role != "owner":
            raise ApiError(403, "FORBIDDEN", "Only farm owners may manage alert rules.")
        self.event_source.poll()
        self.projection.authorise_mutation(farm_id, principal, self.clock())

    def create(self, principal, farm_id, payload):
        self.authorise(principal, farm_id)

        # Validate the rule before storing it.
        required = {
            "name",
            "sensorId",
            "metric",
            "operator",
            "threshold",
            "unit",
            "severity",
            "reminderMinutes",
        }
        if not isinstance(payload, dict) or set(payload) != required:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Provide exactly: " + ", ".join(sorted(required)),
            )
        for field in ("name", "sensorId", "metric", "unit"):
            if (
                not isinstance(payload[field], str)
                or not 1 <= len(payload[field].strip()) <= 120
            ):
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    field + " must contain 1 to 120 nonblank characters.",
                )
        metric, unit = payload["metric"].strip(), payload["unit"].strip()
        if metric not in METRIC_UNITS:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "metric must be one of " + ", ".join(METRIC_UNITS) + ".",
            )
        if unit != METRIC_UNITS[metric]:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                metric + " must use unit '" + METRIC_UNITS[metric] + "'.",
            )
        if payload["operator"] not in (">", "<") or payload["severity"] not in (
            "warning",
            "critical",
        ):
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Use operator > or < and severity warning or critical.",
            )
        if not finite_number(payload["threshold"]):
            raise ApiError(
                422, "VALIDATION_ERROR", "threshold must be a finite JSON number."
            )
        reminder = payload["reminderMinutes"]
        if reminder is not None and (
            type(reminder) is not int or not 1 <= reminder <= 10080
        ):
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "reminderMinutes must be null or an integer from 1 to 10080.",
            )

        # Assign an ID and store the validated rule.
        with self._lock:
            rule = {
                **payload,
                "ruleId": "rule-" + str(self._next_id).zfill(3),
                "farmId": farm_id,
            }
            for field in ("name", "sensorId", "metric", "unit"):
                rule[field] = rule[field].strip()
            self._next_id += 1
            self.rules[rule["ruleId"]] = rule
            return dict(rule)

    def delete(self, principal, farm_id, rule_id):
        self.authorise(principal, farm_id)
        with self._lock:
            rule = self.rules.get(rule_id)
            if rule is None or rule["farmId"] != farm_id:
                raise ApiError(
                    404, "RULE_NOT_FOUND", "Alert rule not found or not accessible."
                )
            del self.rules[rule_id]
            self.states.pop((farm_id, rule["sensorId"], rule_id), None)

    def evaluate(self, farm_id, sensor_id, metric, value, unit, now=None):
        now = monotonic() if now is None else now
        if not finite_number(value) or not finite_number(now):
            raise ValueError("Reading value and time must be finite numbers.")
        emitted = []
        with self._lock:
            for rule in self.rules.values():
                if (rule["farmId"], rule["sensorId"], rule["metric"], rule["unit"]) != (
                    farm_id,
                    sensor_id,
                    metric,
                    unit,
                ):
                    continue

                # Track each rule independently for this farm and sensor.
                key = (farm_id, sensor_id, rule["ruleId"])
                state = self.states.get(key)
                if state and now < state["lastEvaluated"]:
                    continue
                triggered = (
                    value > rule["threshold"]
                    if rule["operator"] == ">"
                    else value < rule["threshold"]
                )
                kind = None

                # A normal reading resolves the current incident, so later
                # breaches can raise new alerts.
                if not triggered:
                    self.states[key] = {"active": False, "lastEvaluated": now}
                    continue

                # Notify on a new incident, or when a critical reminder is due.
                if not state or not state["active"]:
                    state = {"active": True, "firstTriggered": now, "lastNotified": now}
                    kind = "triggered"
                elif (
                    rule["severity"] == "critical"
                    and rule["reminderMinutes"] is not None
                    and now - state["lastNotified"] >= rule["reminderMinutes"] * 60
                ):
                    state["lastNotified"] = now
                    kind = "reminder"

                state["lastEvaluated"] = now
                self.states[key] = state

                if kind:
                    notification = {
                        "farmId": farm_id,
                        "sensorId": sensor_id,
                        "ruleId": rule["ruleId"],
                        "kind": kind,
                        "value": value,
                        "time": now,
                    }
                    self.notifications.append(notification)
                    emitted.append(dict(notification))
        return emitted
