"""Transport validation and domain types for the Farm Management container."""
from dataclasses import dataclass
from math import isfinite


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


@dataclass(frozen=True)
class FarmInput:
    name: str
    latitude: float
    longitude: float
    area_hectares: float

    @classmethod
    def parse(cls, value):
        required = {"name", "latitude", "longitude", "areaHectares"}
        if not isinstance(value, dict) or set(value) != required:
            raise ApiError(422, "VALIDATION_ERROR", "Provide exactly name, latitude, longitude and areaHectares.")
        name = value["name"]
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
            raise ApiError(422, "VALIDATION_ERROR", "name must contain 1 to 120 nonblank characters after trimming.")
        numbers = {}
        for field in ("latitude", "longitude", "areaHectares"):
            number = value[field]
            try:
                valid = type(number) in (int, float) and isfinite(number)
            except (OverflowError, ValueError):
                valid = False
            if not valid:
                raise ApiError(422, "VALIDATION_ERROR", field + " must be a finite JSON number.")
            numbers[field] = number
        if not -90 <= numbers["latitude"] <= 90:
            raise ApiError(422, "VALIDATION_ERROR", "latitude must be between -90 and 90.")
        if not -180 <= numbers["longitude"] <= 180:
            raise ApiError(422, "VALIDATION_ERROR", "longitude must be between -180 and 180.")
        if numbers["areaHectares"] <= 0:
            raise ApiError(422, "VALIDATION_ERROR", "areaHectares must be greater than zero.")
        return cls(name.strip(), numbers["latitude"], numbers["longitude"], numbers["areaHectares"])


@dataclass(frozen=True)
class Farm:
    id: str
    owner_user_id: str
    details: FarmInput

    def public(self):
        return {"id": self.id, "name": self.details.name,
                "latitude": self.details.latitude, "longitude": self.details.longitude,
                "areaHectares": self.details.area_hectares}
