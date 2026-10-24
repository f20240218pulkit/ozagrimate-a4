"""Telemetry Repository: single-process in-memory storage, partitioned by farm.

State is intentionally lost on restart. Production uses the Telemetry Store
(managed time-series data) partitioned by farmId and observation time (ADR-02),
so writes and bounded queries for one farm never scan another farm's data.
Readings are keyed by (farmId, readingId), which makes edge replays idempotent (ADR-06).
"""
from threading import Lock
from .models import ACCEPTED, Reading, ReadingInput

SEED_READINGS = [  # demonstration data, loaded on every start for reproducible Postman runs
    ("farm-001", "sm-north-01-20261023T2000Z", "sm-north-01", "north-paddock", "soilMoisture", 31.2, "%", "2026-10-23T20:00:00Z"),
    ("farm-001", "sm-north-01-20261023T2015Z", "sm-north-01", "north-paddock", "soilMoisture", 30.8, "%", "2026-10-23T20:15:00Z"),
    ("farm-001", "sm-north-01-20261023T2030Z", "sm-north-01", "north-paddock", "soilMoisture", 30.1, "%", "2026-10-23T20:30:00Z"),
    ("farm-001", "wx-01-20261023T2030Z", "wx-01", "north-paddock", "airTemperature", 24.6, "degC", "2026-10-23T20:30:00Z"),
    ("farm-002", "sm-east-01-20261023T2030Z", "sm-east-01", "east-paddock", "soilMoisture", 22.4, "%", "2026-10-23T20:30:00Z"),
]


class InMemoryTelemetryRepository:
    def __init__(self, seed=True):
        self._partitions = {}  # farm_id -> {reading_id: Reading}
        self._lock = Lock()
        if seed:
            for farm, rid, device, paddock, metric, value, unit, observed in SEED_READINGS:
                details = ReadingInput(rid, device, paddock, metric, value, unit, observed)
                self.add(Reading(farm, details, ACCEPTED, (), observed[:-3] + "04Z"))

    def add(self, reading):
        """Store a reading unless its ID already exists; returns (stored_or_existing, created)."""
        with self._lock:
            partition = self._partitions.setdefault(reading.farm_id, {})
            existing = partition.get(reading.details.reading_id)
            if existing is not None:
                return existing, False
            partition[reading.details.reading_id] = reading
            return reading, True

    def find(self, farm_id, reading_id):
        with self._lock:
            return self._partitions.get(farm_id, {}).get(reading_id)

    def latest_accepted_before(self, farm_id, device_id, metric, observed_at):
        with self._lock:
            candidates = [r for r in self._partitions.get(farm_id, {}).values()
                          if r.status == ACCEPTED and r.details.device_id == device_id
                          and r.details.metric == metric and r.details.observed_at < observed_at]
        return max(candidates, key=lambda r: r.details.observed_at, default=None)

    def query(self, farm_id, matches, limit):
        """Return up to `limit` matching readings in observation order, plus whether more exist."""
        with self._lock:
            rows = [r for r in self._partitions.get(farm_id, {}).values() if matches(r)]
        rows.sort(key=lambda r: (r.details.observed_at, r.details.reading_id))
        return rows[:limit], len(rows) > limit
