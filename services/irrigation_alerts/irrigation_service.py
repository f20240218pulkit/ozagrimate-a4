"""Irrigation Application Service (owner: Thomas).

Use cases: create an irrigation request (always PENDING) and replace a pending
request's editable details. Approval, dispatch to the Farm Edge Gateway and
physical execution are planned capabilities and are NOT implemented: nothing here
implies that any water has been applied.
"""
from .models import ApiError, IrrigationInput, PENDING


class IrrigationService:
    def __init__(self, repository, projection, event_source, clock):
        self.repository = repository
        self.projection = projection
        self.event_source = event_source
        self.clock = clock

    def _authorise(self, principal, farm_id):
        self.event_source.poll()
        return self.projection.authorise_mutation(farm_id, principal, self.clock())

    def create(self, principal, farm_id, payload):
        self._authorise(principal, farm_id)
        details = IrrigationInput.parse(payload)
        return self.repository.add(farm_id, principal.user_id, PENDING, details)

    def replace(self, principal, farm_id, request_id, payload):
        self._authorise(principal, farm_id)
        record = self.repository.find(farm_id, request_id)
        if record is None:
            raise ApiError(404, "IRRIGATION_REQUEST_NOT_FOUND", "Irrigation request not found on this farm.")
        details = IrrigationInput.parse(payload)
        if record.status != PENDING:
            raise ApiError(409, "REQUEST_NOT_EDITABLE",
                           "Only PENDING requests can be replaced; this request is " + record.status + ".")
        return self.repository.save(record.replaced(details))
