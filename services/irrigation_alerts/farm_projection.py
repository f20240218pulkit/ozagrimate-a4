"""Farm Access Projection: Irrigation and Alerts' own read-only copy of farms and grants (ADR-07).

Farm Management is authoritative. This service never reads Farm Management's store;
it applies farm/grant events and a source heartbeat. Rules implemented here:
  * duplicate events (same eventId) are ignored;
  * events older than the farm's current version are ignored (per-farm ordering);
  * a version gap marks the farm as needing resynchronisation from a snapshot;
  * access is only trusted while the source watermark is at most 60 seconds old.
When freshness cannot be established, protected mutations are rejected (503).
"""
from dataclasses import dataclass, field
from threading import Lock
from .models import ApiError

FRESHNESS_BUDGET_SECONDS = 60  # ASR19: revocation effective within one minute


@dataclass
class FarmAccess:
    farm_id: str
    owner_user_id: str
    version: int
    workers: set = field(default_factory=set)
    watermark: float = 0.0      # source time up to which this entry is known current
    needs_resync: bool = False


class FarmAccessProjection:
    def __init__(self):
        self._farms = {}
        self._seen_events = set()
        self._lock = Lock()

    def apply(self, event):
        """Apply one farm/grant event. Returns True if it changed the projection."""
        with self._lock:
            if event["eventId"] in self._seen_events:
                return False
            self._seen_events.add(event["eventId"])
            farm_id, version, kind = event["farmId"], event["farmVersion"], event["type"]
            current = self._farms.get(farm_id)
            if current is not None and version <= current.version:
                return False                       # stale or replayed out of order
            if current is not None and version > current.version + 1:
                current.needs_resync = True        # gap: an earlier event is missing
                return False
            if kind == "FarmCreated":
                self._farms[farm_id] = FarmAccess(farm_id, event["ownerUserId"], version,
                                                  watermark=event["occurredAt"])
                return True
            if current is None:
                return False                       # grant for an unknown farm: wait for snapshot
            if kind == "WorkerGranted":
                current.workers.add(event["userId"])
            elif kind == "WorkerRevoked":
                current.workers.discard(event["userId"])
            current.version = version
            current.watermark = max(current.watermark, event["occurredAt"])
            return True

    def heartbeat(self, farm_id, source_time):
        """Source confirms no further changes for this farm up to source_time."""
        with self._lock:
            entry = self._farms.get(farm_id)
            if entry is not None and not entry.needs_resync:
                entry.watermark = max(entry.watermark, source_time)

    def authorise_mutation(self, farm_id, principal, now):
        """Return the farm entry if the caller may change irrigation data on it."""
        with self._lock:
            entry = self._farms.get(farm_id)
            allowed = entry is not None and (
                (principal.role == "owner" and entry.owner_user_id == principal.user_id)
                or (principal.role == "worker" and principal.user_id in entry.workers))
            if not allowed:
                # Absent and inaccessible farms are indistinguishable (ADR-05).
                raise ApiError(404, "FARM_NOT_FOUND", "Farm not found or not accessible.")
            if entry.needs_resync or now - entry.watermark > FRESHNESS_BUDGET_SECONDS:
                raise ApiError(503, "FARM_ACCESS_STALE",
                               "Farm access cannot be confirmed as current; try again shortly.")
            return entry
