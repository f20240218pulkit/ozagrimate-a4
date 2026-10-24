"""Accepted Reading Publisher (outbox).

Target design (ADR-02): after a reading is durably stored, a ReadingAccepted event
is written to an outbox and relayed to the Event Broker, partitioned by farmId.
Irrigation and Alerts and AI Recommendation consume these events at their own
pace, so ingestion never waits for downstream processing.

No broker exists in this prototype. The outbox is an in-memory list so the rules
can be tested: only ACCEPTED readings are published, each reading at most once,
and quarantined readings are never published (ASR5).
"""
from threading import Lock
from .models import ACCEPTED, SCHEMA_VERSION


class AcceptedReadingPublisher:
    def __init__(self):
        self._outbox = []
        self._lock = Lock()

    def publish(self, reading):
        if reading.status != ACCEPTED:
            return None
        d = reading.details
        event = {"eventId": "evt-" + reading.farm_id + "-" + d.reading_id, "type": "ReadingAccepted",
                 "schemaVersion": SCHEMA_VERSION, "partitionKey": reading.farm_id,
                 "readingId": d.reading_id, "farmId": reading.farm_id, "deviceId": d.device_id,
                 "paddockId": d.paddock_id, "metric": d.metric, "value": d.value, "unit": d.unit,
                 "observedAt": d.observed_at}
        with self._lock:
            self._outbox.append(event)
        return event

    def pending_events(self):
        """Events awaiting relay to the broker (inspected by tests)."""
        with self._lock:
            return list(self._outbox)
