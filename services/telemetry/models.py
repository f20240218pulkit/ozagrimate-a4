"""Telemetry Domain Model / Validator (owner: Aditya).

Defines the versioned edge-to-cloud reading contract (ADR-06) and the schema-level
validation applied before a reading is stored. Schema bounds reject impossible
values with 422; well-formed but suspicious values are quarantined by the
Anomaly Detector instead (ASR5), never silently discarded.
"""
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from math import isfinite
import re


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


SCHEMA_VERSION = 1  # ADR-06: the only contract version this service accepts

# Metric catalogue: canonical unit and schema range. A range is a contract bound,
# not proof of agronomic accuracy; calibration is configured per sensor in production.
METRICS = {
    "soilMoisture":    {"unit": "%",    "min": 0.0,   "max": 100.0},   # volumetric water content
    "soilTemperature": {"unit": "degC", "min": -20.0, "max": 60.0},
    "airTemperature":  {"unit": "degC", "min": -50.0, "max": 60.0},
    "rainfall":        {"unit": "mm",   "min": 0.0,   "max": 500.0},   # since previous reading
}

READING_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,59}")
UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
FUTURE_TOLERANCE = timedelta(minutes=5)  # allows small device clock drift

ACCEPTED, QUARANTINED = "ACCEPTED", "QUARANTINED"


def invalid(message, code="VALIDATION_ERROR"):
    raise ApiError(422, code, message)


def parse_utc(value, field):
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        invalid(field + " must be a UTC timestamp such as 2026-10-23T20:45:00Z.")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        invalid(field + " is not a valid calendar date and time.")


def format_utc(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finite_number(value):
    try:
        return type(value) in (int, float) and isfinite(value)
    except (OverflowError, ValueError):
        return False


@dataclass(frozen=True)
class ReadingInput:
    """One normalised sensor reading as sent by a Farm Edge Gateway."""
    reading_id: str
    device_id: str
    paddock_id: str
    metric: str
    value: float
    unit: str
    observed_at: str

    FIELDS = frozenset({"schemaVersion", "readingId", "deviceId", "paddockId",
                        "metric", "value", "unit", "observedAt"})

    @classmethod
    def parse(cls, body, now):
        if not isinstance(body, dict):
            invalid("Request body must be a JSON object.")
        if set(body) != cls.FIELDS:
            invalid("Provide exactly schemaVersion, readingId, deviceId, paddockId, metric, value, "
                    "unit and observedAt. farmId comes from the URL; status is assigned by the service.")
        if type(body["schemaVersion"]) is not int or body["schemaVersion"] != SCHEMA_VERSION:
            invalid("schemaVersion must be 1.", "UNSUPPORTED_SCHEMA_VERSION")

        reading_id = body["readingId"]
        if not isinstance(reading_id, str) or READING_ID.fullmatch(reading_id) is None:
            invalid("readingId must be 1 to 80 letters, digits, '.', '_', ':' or '-'.")
        for field in ("deviceId", "paddockId"):
            if not isinstance(body[field], str) or SLUG.fullmatch(body[field]) is None:
                invalid(field + " must be 1 to 60 lowercase letters, digits or hyphens.")

        metric = body["metric"]
        if not isinstance(metric, str) or metric not in METRICS:
            invalid("metric must be one of " + ", ".join(METRICS) + ".")
        spec = METRICS[metric]
        if body["unit"] != spec["unit"]:
            invalid(metric + " must be reported in '" + spec["unit"] + "'.")
        value = body["value"]
        if not _finite_number(value) or not spec["min"] <= value <= spec["max"]:
            invalid(metric + " value must be a number from " + _num(spec["min"]) + " to " + _num(spec["max"]) + ".")

        observed = parse_utc(body["observedAt"], "observedAt")
        if observed > now + FUTURE_TOLERANCE:
            invalid("observedAt cannot be more than 5 minutes in the future.")

        return cls(reading_id, body["deviceId"], body["paddockId"], metric, value,
                   spec["unit"], body["observedAt"])


def _num(x):
    return str(int(x)) if float(x).is_integer() else str(x)


@dataclass(frozen=True)
class Reading:
    farm_id: str
    details: ReadingInput
    status: str
    quarantine_reasons: tuple
    received_at: str

    def with_status(self, status, reasons):
        return replace(self, status=status, quarantine_reasons=tuple(reasons))

    def public(self):
        d = self.details
        return {"readingId": d.reading_id, "farmId": self.farm_id, "deviceId": d.device_id,
                "paddockId": d.paddock_id, "metric": d.metric, "value": d.value, "unit": d.unit,
                "observedAt": d.observed_at, "receivedAt": self.received_at, "status": self.status,
                "quarantineReasons": list(self.quarantine_reasons), "schemaVersion": SCHEMA_VERSION}
