# Telemetry demo steps for the team video (about 60 seconds)

For Bradley's recording. Start everything fresh first: `py -3 run_all.py` (or `python3 run_all.py`).

## Repository (10 s)

Open `services/telemetry/` and point at the modules that match the Telemetry component diagram:
`api.py` (REST Controller), `ingestion_service.py`, `query_service.py`, `farm_access.py`,
`models.py` (validator), `anomaly_detector.py`, `repository.py`, `event_publisher.py`, `app.py`.
One sentence: "Each box in the Telemetry component view is one module here; the service runs on its own port, 8002."

## Postman (about 50 s)

Collection: `postman/Aditya_Telemetry.postman_collection.json`. Run in order. If time is short, show these:

| Request | Shows | Expected |
|---|---|---|
| 01 Submit soil-moisture reading | Success | 201, status ACCEPTED |
| 02 Replay identical reading | Idempotent edge replay | 200, same record |
| 04 Submit spike reading | Quarantine (ASR5) | 201, status QUARANTINED, SPIKE_DETECTED |
| 07 Out-of-range value | Validation | 422 VALIDATION_ERROR |
| 05 Owner tries to submit | Gateway-only writes | 403 FORBIDDEN |
| 13 Owner lists soil-moisture readings | GET success | 200, four readings in time order |
| 16 Another owner reads farm-001 | Farm isolation | 404 FARM_NOT_FOUND |

Then open the Runner result: 19 requests, 59 assertions, 0 failures.
