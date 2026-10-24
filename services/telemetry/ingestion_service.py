"""Telemetry Ingestion Service (owner: Aditya).

Use case: accept one normalised reading from a registered Farm Edge Gateway.
Steps: authorise gateway -> validate contract -> idempotency check -> classify
(accept or quarantine) -> store -> publish ReadingAccepted for accepted readings only.
The response is returned once the reading is stored; downstream processing is
asynchronous (ADR-02). Replays after an edge outage return the original record
instead of creating duplicates (ADR-06).
"""
from datetime import datetime, timezone
from .models import ApiError, Reading, ReadingInput, format_utc


class TelemetryIngestionService:
    def __init__(self, repository, farm_access, detector, publisher, clock):
        self.repository = repository
        self.farm_access = farm_access
        self.detector = detector
        self.publisher = publisher
        self.clock = clock

    def submit(self, principal, farm_id, payload):
        """Returns (reading, created). created is False for an identical replay."""
        self.farm_access.authorise_submission(farm_id, principal)
        now = datetime.fromtimestamp(self.clock(), timezone.utc)
        details = ReadingInput.parse(payload, now)

        existing = self.repository.find(farm_id, details.reading_id)
        if existing is not None:
            return self._replay(existing, details), False

        status, reasons = self.detector.classify(farm_id, details)
        reading, created = self.repository.add(Reading(farm_id, details, status, tuple(reasons), format_utc(now)))
        if not created:  # a concurrent replay stored it first
            return self._replay(reading, details), False
        self.publisher.publish(reading)
        return reading, True

    @staticmethod
    def _replay(existing, details):
        if existing.details != details:
            raise ApiError(409, "READING_ID_CONFLICT",
                           "readingId " + details.reading_id + " was already stored with different content.")
        return existing
