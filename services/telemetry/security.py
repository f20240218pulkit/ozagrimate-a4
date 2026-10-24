"""Identity Adapter. Local demonstration identities, NOT OAuth tokens or production security.

Person fixtures match Farm Management and Irrigation and Alerts. Telemetry adds
edge-gateway identities: in production each Farm Edge Gateway holds its own
scoped machine credential (mutual TLS / client credentials) bound to one farm.
Identity says who is calling; Farm Access decides what they may do (ADR-05).
"""
from dataclasses import dataclass
from .models import ApiError


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str  # owner | worker | gateway


DEMO_IDENTITIES = {
    "demo-owner-a": Principal("owner-a", "owner"),
    "demo-owner-b": Principal("owner-b", "owner"),
    "demo-worker-a": Principal("worker-a", "worker"),
    "demo-gateway-001": Principal("gateway-001", "gateway"),
    "demo-gateway-002": Principal("gateway-002", "gateway"),
}


def authenticate(authorization):
    parts = authorization.split()
    principal = DEMO_IDENTITIES.get(parts[1]) if len(parts) == 2 and parts[0].lower() == "bearer" else None
    if principal is None:
        raise ApiError(401, "UNAUTHENTICATED", "A valid local demonstration bearer token is required.")
    return principal
