"""Domain Model / Validator for the Irrigation and Alerts container.

Irrigation types are owned by Thomas. Alert-rule types are added by Bradley.
"""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from math import isfinite
import re


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


# ADR-03 safe limits. Units are part of the field names. Production makes these
# configurable per paddock; the prototype uses one conservative default set.
SAFE_LIMITS = {
    "durationMinutes": (1, 240),     # whole minutes per request
    "waterDepthMm": (0.5, 50.0),     # millimetres of applied water
}

PADDOCK_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,59}")
UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

PENDING, APPROVED = "PENDING", "APPROVED"


def _invalid(message):
    raise ApiError(422, "VALIDATION_ERROR", message)


def _finite_number(value):
    try:
        return type(value) in (int, float) and isfinite(value)
    except (OverflowError, ValueError):
        return False


@dataclass(frozen=True)
class IrrigationInput:
    """Editable details. Identity, status, owner and requester are never caller-supplied."""
    paddock_id: str
    scheduled_start: str
    duration_minutes: int
    water_depth_mm: float
    notes: str

    REQUIRED = frozenset({"paddockId", "scheduledStart", "durationMinutes", "waterDepthMm"})
    OPTIONAL = frozenset({"notes"})

    @classmethod
    def parse(cls, value):
        if not isinstance(value, dict):
            _invalid("Request body must be a JSON object.")
        keys = set(value)
        if not cls.REQUIRED <= keys or not keys <= cls.REQUIRED | cls.OPTIONAL:
            _invalid("Provide paddockId, scheduledStart, durationMinutes and waterDepthMm; notes is optional. No other fields are accepted.")

        paddock = value["paddockId"]
        if not isinstance(paddock, str) or PADDOCK_ID.fullmatch(paddock) is None:
            _invalid("paddockId must be 1 to 60 lowercase letters, digits or hyphens.")

        start = value["scheduledStart"]
        if not isinstance(start, str) or UTC_TIMESTAMP.fullmatch(start) is None:
            _invalid("scheduledStart must be a UTC timestamp such as 2026-11-02T19:00:00Z.")
        try:
            datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            _invalid("scheduledStart is not a valid calendar date and time.")

        duration = value["durationMinutes"]
        low, high = SAFE_LIMITS["durationMinutes"]
        if type(duration) is not int or not low <= duration <= high:
            _invalid("durationMinutes must be a whole number from 1 to 240.")

        depth = value["waterDepthMm"]
        low, high = SAFE_LIMITS["waterDepthMm"]
        if not _finite_number(depth) or not low <= depth <= high:
            _invalid("waterDepthMm must be a number from 0.5 to 50.")

        notes = value.get("notes", "")
        if not isinstance(notes, str) or len(notes) > 500:
            _invalid("notes must be text of at most 500 characters.")

        return cls(paddock, start, duration, depth, notes.strip())


@dataclass(frozen=True)
class IrrigationRequest:
    id: str
    farm_id: str
    requested_by: str
    status: str
    version: int
    details: IrrigationInput

    def replaced(self, details):
        return replace(self, details=details, version=self.version + 1)

    def public(self):
        d = self.details
        return {"id": self.id, "farmId": self.farm_id, "paddockId": d.paddock_id,
                "scheduledStart": d.scheduled_start, "durationMinutes": d.duration_minutes,
                "waterDepthMm": d.water_depth_mm, "notes": d.notes, "status": self.status,
                "requestedBy": self.requested_by, "version": self.version}
