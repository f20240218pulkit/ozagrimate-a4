"""Farm creation and farm-scoped retrieval use cases."""
from .models import ApiError, FarmInput


class FarmService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, principal, payload):
        if principal.role != "owner":
            raise ApiError(403, "FORBIDDEN", "Only a farm owner may create a farm.")
        details = FarmInput.parse(payload)
        return self.repository.create(details, principal.user_id)

    def get(self, principal, farm_id):
        farm = self.repository.find_for_owner(farm_id, principal.user_id)
        if farm is None:
            raise ApiError(404, "FARM_NOT_FOUND", "Farm not found or not accessible.")
        return farm
