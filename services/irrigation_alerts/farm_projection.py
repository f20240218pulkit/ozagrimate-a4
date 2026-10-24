"""Farm Access Projection: Irrigation and Alerts' own read-only copy of farms and grants (ADR-07).

Farm Management is authoritative. This service never reads Farm Management's store;
it applies farm/grant events, a source heartbeat and, when needed, a trusted snapshot.
Rules implemented here:
  * an event ID is recorded as seen only once it has been applied, so replays of
    events that could not yet be applied are not lost;
  * events at or below the farm's current version are ignored (per-farm ordering);
  * an event that arrives ahead of a missing version is buffered and the farm is
    marked as needing resynchronisation; when the missing version arrives, buffered
    events are applied in order and the flag clears once no gap remains;
  * restore_snapshot() is the trusted recovery path: it replaces the farm's entry
    with a consistent snapshot from Farm Management, then applies newer buffered events;
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
        self._applied_events = set()
        self._pending = {}          # farm_id -> {version: event} awaiting an earlier version
        self._lock = Lock()

    # --- event intake --------------------------------------------------------------
    def apply(self, event):
        """Apply one farm/grant event. Returns True if it changed the projection."""
        with self._lock:
            if event["eventId"] in self._applied_events:
                return False                       # duplicate of an applied event
            farm_id, version = event["farmId"], event["farmVersion"]
            current = self._farms.get(farm_id)
            expected = 1 if current is None else current.version + 1
            if version < expected:
                return False                       # stale or replayed out of order
            if version > expected:
                self._pending.setdefault(farm_id, {})[version] = event
                if current is not None:
                    current.needs_resync = True    # gap: an earlier event is missing
                return False
            self._apply_in_order(event)
            self._drain(farm_id)
            return True

    def restore_snapshot(self, snapshot):
        """Trusted recovery: replace a farm's entry with a consistent snapshot from Farm Management.

        snapshot = {"farmId", "farmVersion", "ownerUserId", "workers", "asOf"}
        Buffered events newer than the snapshot are then applied; older ones are discarded.
        """
        with self._lock:
            farm_id, version = snapshot["farmId"], snapshot["farmVersion"]
            current = self._farms.get(farm_id)
            if current is not None and version < current.version:
                return False                       # never roll the projection backwards
            self._farms[farm_id] = FarmAccess(farm_id, snapshot["ownerUserId"], version,
                                              set(snapshot.get("workers", ())), snapshot["asOf"])
            pending = self._pending.get(farm_id, {})
            for stale in [v for v in pending if v <= version]:
                del pending[stale]
            self._drain(farm_id)
            return True

    def heartbeat(self, farm_id, source_time):
        """Source confirms no further changes for this farm up to source_time."""
        with self._lock:
            entry = self._farms.get(farm_id)
            if entry is not None and not entry.needs_resync:
                entry.watermark = max(entry.watermark, source_time)

    # --- internal (lock held) ------------------------------------------------------
    def _apply_in_order(self, event):
        farm_id, kind = event["farmId"], event["type"]
        if kind == "FarmCreated":
            self._farms[farm_id] = FarmAccess(farm_id, event["ownerUserId"], event["farmVersion"],
                                              watermark=event["occurredAt"])
        else:
            entry = self._farms[farm_id]
            if kind == "WorkerGranted":
                entry.workers.add(event["userId"])
            elif kind == "WorkerRevoked":
                entry.workers.discard(event["userId"])
            entry.version = event["farmVersion"]
            entry.watermark = max(entry.watermark, event["occurredAt"])
        self._applied_events.add(event["eventId"])

    def _drain(self, farm_id):
        """Apply buffered events that are now contiguous; clear the flag when no gap remains."""
        pending = self._pending.get(farm_id, {})
        entry = self._farms.get(farm_id)
        while entry is not None and entry.version + 1 in pending:
            self._apply_in_order(pending.pop(entry.version + 1))
            entry = self._farms[farm_id]
        if not pending:
            self._pending.pop(farm_id, None)
        if entry is not None:
            entry.needs_resync = bool(pending)

    # --- authorisation ------------------------------------------------------------
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
