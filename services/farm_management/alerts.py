
from math import isfinite
from threading import Lock
from time import monotonic
from .models import ApiError


def finite_number(value):
    try:
        return type(value) in (int, float) and isfinite(value)
    except OverflowError:
        return False


class AlertRuleService:
    def __init__(self, farms):
        self.farms = farms
        self.rules = {}
        self.states = {}
        self.notifications = []
        self._next_id = 1
        self._lock = Lock()

    def authorise(self, principal, farm_id):
        if principal.role != "owner":
            raise ApiError(403, "FORBIDDEN", "Only farm owners may manage alert rules.")
        self.farms.get(principal, farm_id)

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

        #assign an id and a vlidate rule
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

                #track each rule independently for this farm and sensor.
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

                #a normal reading resolves the current incident.
                ## once it resolves it also means it can send other alerts
                if not triggered:
                    self.states[key] = {"active": False, "lastEvaluated": now}
                    continue

                #notify on a new incident, or when a critical reminder is due.
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
