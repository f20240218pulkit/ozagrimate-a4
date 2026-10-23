"""Local demonstration identities. These are NOT OAuth tokens or production security."""
from dataclasses import dataclass
from .models import ApiError


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str


DEMO_IDENTITIES = {
    "demo-owner-a": Principal("owner-a", "owner"),
    "demo-owner-b": Principal("owner-b", "owner"),
    "demo-worker-a": Principal("worker-a", "worker"),
}


def authenticate(authorization):
    parts = authorization.split()
    principal = DEMO_IDENTITIES.get(parts[1]) if len(parts) == 2 and parts[0].lower() == "bearer" else None
    if principal is None:
        raise ApiError(401, "UNAUTHENTICATED", "A valid local demonstration bearer token is required.")
    return principal
