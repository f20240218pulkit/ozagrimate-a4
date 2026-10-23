"""Single-process in-memory storage. State is intentionally lost on restart."""
from threading import Lock
from .models import Farm


class InMemoryFarmRepository:
    def __init__(self):
        self._farms = {}
        self._lock = Lock()

    def create(self, details, owner_user_id):
        with self._lock:
            farm = Farm("farm-" + str(len(self._farms) + 1).zfill(3), owner_user_id, details)
            self._farms[farm.id] = farm
            return farm

    def find_for_owner(self, farm_id, owner_user_id):
        with self._lock:
            farm = self._farms.get(farm_id)
            return farm if farm and farm.owner_user_id == owner_user_id else None
