"""ADR-07 projection rules: duplicates, ordering, gaps, revocation and freshness."""
import unittest
from services.irrigation_alerts.farm_projection import FarmAccessProjection
from services.irrigation_alerts.models import ApiError
from services.irrigation_alerts.security import Principal

OWNER = Principal("owner-a", "owner")
WORKER = Principal("worker-a", "worker")


def event(event_id, kind, version, at=1000.0, **extra):
    return {"eventId": event_id, "type": kind, "farmId": "farm-001", "farmVersion": version,
            "occurredAt": at, **extra}


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.p = FarmAccessProjection()
        self.p.apply(event("e1", "FarmCreated", 1, ownerUserId="owner-a"))
        self.p.apply(event("e2", "WorkerGranted", 2, userId="worker-a"))

    def assert_denied(self, principal, now, code):
        with self.assertRaises(ApiError) as caught:
            self.p.authorise_mutation("farm-001", principal, now)
        self.assertEqual(caught.exception.code, code)

    def test_granted_worker_allowed_while_fresh(self):
        self.p.authorise_mutation("farm-001", WORKER, now=1030.0)

    def test_revocation_takes_effect_on_next_event(self):
        self.p.apply(event("e3", "WorkerRevoked", 3, at=1010.0, userId="worker-a"))
        self.assert_denied(WORKER, 1011.0, "FARM_NOT_FOUND")
        self.p.authorise_mutation("farm-001", OWNER, now=1011.0)

    def test_duplicate_event_is_ignored(self):
        self.p.apply(event("e3", "WorkerRevoked", 3, userId="worker-a"))
        self.assertFalse(self.p.apply(event("e3", "WorkerRevoked", 3, userId="worker-a")))

    def test_out_of_order_event_cannot_restore_revoked_grant(self):
        self.p.apply(event("e3", "WorkerRevoked", 3, userId="worker-a"))
        self.assertFalse(self.p.apply(event("e2-replay", "WorkerGranted", 2, userId="worker-a")))
        self.assert_denied(WORKER, 1001.0, "FARM_NOT_FOUND")

    def test_version_gap_blocks_mutations_until_resync(self):
        self.assertFalse(self.p.apply(event("e5", "WorkerGranted", 5, userId="worker-b")))
        self.assert_denied(OWNER, 1001.0, "FARM_ACCESS_STALE")

    def test_stale_watermark_blocks_mutations_and_heartbeat_restores(self):
        self.assert_denied(OWNER, 1061.0, "FARM_ACCESS_STALE")
        self.p.heartbeat("farm-001", 1060.0)
        self.p.authorise_mutation("farm-001", OWNER, now=1061.0)


if __name__ == "__main__":
    unittest.main()
