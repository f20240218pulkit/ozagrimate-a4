"""Farm Event Consumer (PROPOSED).

Target design: consume versioned farm/grant events and heartbeats from the Event
Broker, published by Farm Management through an outbox (ADR-07). No broker exists
in this prototype and Farm Management does not yet publish events.

This module therefore provides a trusted local fixture source with the same event
shape, so the projection rules (dedupe, ordering, freshness) run for real:
  farm-001  owner-a, worker-a granted    healthy source (heartbeat on every poll)
  farm-002  owner-b                      healthy source
  farm-003  owner-a                      STALLED source (no heartbeat; demonstrates 503)
"""

FIXTURE_EVENTS = [
    {"eventId": "evt-001", "type": "FarmCreated", "farmId": "farm-001", "farmVersion": 1,
     "ownerUserId": "owner-a", "occurredAt": 0.0},
    {"eventId": "evt-002", "type": "WorkerGranted", "farmId": "farm-001", "farmVersion": 2,
     "userId": "worker-a", "occurredAt": 0.0},
    {"eventId": "evt-003", "type": "FarmCreated", "farmId": "farm-002", "farmVersion": 1,
     "ownerUserId": "owner-b", "occurredAt": 0.0},
    {"eventId": "evt-004", "type": "FarmCreated", "farmId": "farm-003", "farmVersion": 1,
     "ownerUserId": "owner-a", "occurredAt": 0.0},
]

HEALTHY_FARMS = ("farm-001", "farm-002")


class FixtureFarmEventSource:
    """Stands in for the broker subscription. Not a production consumer."""

    def __init__(self, projection, clock):
        self.projection = projection
        self.clock = clock
        start = clock()
        for event in FIXTURE_EVENTS:
            projection.apply({**event, "occurredAt": start - 3600})  # snapshot is an hour old

    def poll(self):
        """Deliver pending heartbeats. A healthy source confirms it is current."""
        now = self.clock()
        for farm_id in HEALTHY_FARMS:
            self.projection.heartbeat(farm_id, now)
