"""Farm Access Read Model: Telemetry's own read-only copy of farms, grants and registered gateways.

Farm Management is authoritative for farms and grants. Telemetry never reads the
Farm Store. In the target design this read model is fed by the same versioned
farm/grant events and freshness rules as ADR-07; device registration events add
gateway bindings. The prototype loads a trusted fixture snapshot instead, so no
broker is implied. Fixture identities match the other two services:
  farm-001  owner-a, worker-a granted, gateway-001 registered
  farm-002  owner-b,                   gateway-002 registered
"""
from dataclasses import dataclass, field
from threading import Lock
from .models import ApiError

FIXTURE_SNAPSHOT = [
    {"farmId": "farm-001", "ownerUserId": "owner-a", "workers": ["worker-a"], "gateways": ["gateway-001"]},
    {"farmId": "farm-002", "ownerUserId": "owner-b", "workers": [], "gateways": ["gateway-002"]},
]

NOT_FOUND = ("FARM_NOT_FOUND", "Farm not found or not accessible.")


@dataclass
class FarmAccess:
    farm_id: str
    owner_user_id: str
    workers: set = field(default_factory=set)
    gateways: set = field(default_factory=set)


class FarmAccessReadModel:
    def __init__(self, snapshot=FIXTURE_SNAPSHOT):
        self._lock = Lock()
        self._farms = {s["farmId"]: FarmAccess(s["farmId"], s["ownerUserId"], set(s["workers"]),
                                               set(s["gateways"])) for s in snapshot}

    def authorise_submission(self, farm_id, principal):
        """Only an edge gateway registered to this farm may submit readings."""
        if principal.role != "gateway":
            raise ApiError(403, "FORBIDDEN", "Only a registered edge gateway may submit readings.")
        with self._lock:
            entry = self._farms.get(farm_id)
            if entry is None or principal.user_id not in entry.gateways:
                raise ApiError(404, *NOT_FOUND)  # absent and foreign farms look identical
            return entry

    def authorise_read(self, farm_id, principal):
        """Farm owner and granted workers may read readings; gateways are write-only."""
        if principal.role == "gateway":
            raise ApiError(403, "FORBIDDEN", "Edge gateways may only submit readings.")
        with self._lock:
            entry = self._farms.get(farm_id)
            allowed = entry is not None and (
                (principal.role == "owner" and entry.owner_user_id == principal.user_id)
                or (principal.role == "worker" and principal.user_id in entry.workers))
            if not allowed:
                raise ApiError(404, *NOT_FOUND)
            return entry
