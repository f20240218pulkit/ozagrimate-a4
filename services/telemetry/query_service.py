"""Telemetry Query Service (owner: Aditya).

Use case: return a farm's readings to its owner or granted workers, filtered and
bounded. Every query is scoped to one farm partition and capped at 500 rows
(ADR-02), so a large farm or a long history cannot produce unbounded responses.
"""
import re
from urllib.parse import parse_qs
from .models import ACCEPTED, METRICS, QUARANTINED, SLUG, invalid, parse_utc

DEFAULT_LIMIT, MAX_LIMIT = 100, 500
STATUSES = (ACCEPTED, QUARANTINED, "ALL")
PARAMETERS = ("metric", "deviceId", "paddockId", "from", "to", "status", "limit")


class TelemetryQueryService:
    def __init__(self, repository, farm_access):
        self.repository = repository
        self.farm_access = farm_access

    def list(self, principal, farm_id, query_string):
        self.farm_access.authorise_read(farm_id, principal)
        f = self._parse(query_string)
        readings, has_more = self.repository.query(farm_id, lambda r: self._matches(r, f), f["limit"])
        return {"farmId": farm_id, "count": len(readings), "hasMore": has_more,
                "readings": [r.public() for r in readings]}

    @staticmethod
    def _parse(query_string):
        raw = parse_qs(query_string, keep_blank_values=True)
        unknown = set(raw) - set(PARAMETERS)
        if unknown:
            invalid("Unsupported query parameter(s): " + ", ".join(sorted(unknown)) + ".")
        if any(len(v) > 1 for v in raw.values()):
            invalid("Each query parameter may appear only once.")
        q = {k: v[0] for k, v in raw.items()}

        if "metric" in q and q["metric"] not in METRICS:
            invalid("metric must be one of " + ", ".join(METRICS) + ".")
        for key in ("deviceId", "paddockId"):
            if key in q and SLUG.fullmatch(q[key]) is None:
                invalid(key + " must be 1 to 60 lowercase letters, digits or hyphens.")
        for key in ("from", "to"):
            if key in q:
                parse_utc(q[key], key)
        if "from" in q and "to" in q and q["from"] > q["to"]:
            invalid("from must not be later than to.")
        status = q.get("status", ACCEPTED)
        if status not in STATUSES:
            invalid("status must be ACCEPTED, QUARANTINED or ALL.")
        limit = q.get("limit", str(DEFAULT_LIMIT))
        if re.fullmatch(r"[0-9]{1,3}", limit) is None or not 1 <= int(limit) <= MAX_LIMIT:
            invalid("limit must be a whole number from 1 to 500.")
        return {**q, "status": status, "limit": int(limit)}

    @staticmethod
    def _matches(reading, f):
        d = reading.details
        return ((f["status"] == "ALL" or reading.status == f["status"])
                and f.get("metric", d.metric) == d.metric
                and f.get("deviceId", d.device_id) == d.device_id
                and f.get("paddockId", d.paddock_id) == d.paddock_id
                and f.get("from", d.observed_at) <= d.observed_at <= f.get("to", d.observed_at))
