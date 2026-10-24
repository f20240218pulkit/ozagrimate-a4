"""Anomaly Detector: decides ACCEPTED or QUARANTINED for a schema-valid reading (ASR5).

Quarantined readings are stored with reason codes and provenance but are never
published as accepted-reading events, so they cannot trigger irrigation or alerts.
Thresholds are prototype defaults; production configures them per sensor type,
calibration and sampling interval.
"""
from .models import ACCEPTED, QUARANTINED, parse_utc

# Maximum plausible change between consecutive accepted readings from one device.
SPIKE_LIMITS = {"soilMoisture": 25.0, "soilTemperature": 10.0, "airTemperature": 15.0}
SPIKE_WINDOW_SECONDS = 3600
RAINFALL_PLAUSIBLE_MAX_MM = 100.0  # per reading; larger values need manual review


class AnomalyDetector:
    def __init__(self, repository):
        self.repository = repository

    def classify(self, farm_id, details):
        reasons = []
        if details.metric == "rainfall" and details.value > RAINFALL_PLAUSIBLE_MAX_MM:
            reasons.append("IMPLAUSIBLE_VALUE")
        limit = SPIKE_LIMITS.get(details.metric)
        if limit is not None:
            previous = self.repository.latest_accepted_before(farm_id, details.device_id,
                                                              details.metric, details.observed_at)
            if previous is not None:
                gap = (parse_utc(details.observed_at, "observedAt")
                       - parse_utc(previous.details.observed_at, "observedAt")).total_seconds()
                if gap <= SPIKE_WINDOW_SECONDS and abs(details.value - previous.details.value) > limit:
                    reasons.append("SPIKE_DETECTED")
        return (QUARANTINED if reasons else ACCEPTED), reasons
