"""Repository: single-process in-memory storage for Irrigation and Alerts records.

State is intentionally lost on restart. Production uses this service's own
partition of the Operations Store.
"""
from threading import Lock
from .models import APPROVED, IrrigationInput, IrrigationRequest


class InMemoryIrrigationRepository:
    def __init__(self, seed=True):
        self._requests = {}
        self._lock = Lock()
        if seed:
            # Approval is a planned capability, so one APPROVED request is seeded
            # to demonstrate the 409 lifecycle conflict on PUT.
            details = IrrigationInput("north-paddock", "2026-11-01T19:00:00Z", 45, 12.0,
                                      "Seeded approved request for the demonstration.")
            self._requests["irr-001"] = IrrigationRequest("irr-001", "farm-001", "owner-a",
                                                          APPROVED, 1, details)

    def add(self, farm_id, requested_by, status, details):
        with self._lock:
            request_id = "irr-" + str(len(self._requests) + 1).zfill(3)
            record = IrrigationRequest(request_id, farm_id, requested_by, status, 1, details)
            self._requests[request_id] = record
            return record

    def find(self, farm_id, request_id):
        with self._lock:
            record = self._requests.get(request_id)
            return record if record and record.farm_id == farm_id else None

    def save(self, record):
        with self._lock:
            self._requests[record.id] = record
            return record
