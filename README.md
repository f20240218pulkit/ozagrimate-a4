# OzAgriMate — ISYS3459 Assignment 4

Team: Pulkit Sharma, Aditya Singh, Thomas Wight and Bradley Shears.

Software architecture and REST API prototype for the OzAgriMate agricultural platform. The repository follows the service-based architecture in ADR-01: one Python package per backend container (`services/farm_management`, `services/telemetry`, `services/irrigation_alerts`), each with its own HTTP server, port and in-memory store. Implemented so far: farm (Pulkit), telemetry (Aditya) and irrigation-request (Thomas) endpoints. Alert-rule endpoints (Bradley) are pending. Target architectural decisions remain **Proposed**.

## Run everything (recommended for the demo)

Requires Python 3.10+ and uses only the standard library; `requirements.txt` lists no runtime packages.

```powershell
py -3 run_all.py          # Windows
python3 run_all.py        # macOS/Linux
```

This starts Farm Management on 8001, Telemetry on 8002 and Irrigation and Alerts on 8003 in one terminal. Each service keeps its own in-memory state, which resets on restart. Restart before each full Postman run so seeded data and generated IDs match the collections.

## Run Farm Management

Requires Python 3.10+ and uses only the standard library. No package installation is required.

From the repository root on Windows:

```powershell
py -3 -m services.farm_management.app
```

On macOS/Linux:

```bash
python3 -m services.farm_management.app
```

The local API listens at `http://127.0.0.1:8001`. Leave the terminal running while testing. Records are held in memory and reset on restart.

## Run Telemetry

```powershell
py -3 -m services.telemetry.app
```

Listens at `http://127.0.0.1:8002` (macOS/Linux: `python3 -m services.telemetry.app`). Seeded fixtures: farm-001 (owner A, worker A granted, gateway 001 registered) has three soil-moisture readings and one air-temperature reading; farm-002 (owner B, gateway 002) has one reading. Edge gateways submit with `Bearer demo-gateway-001`; owners and granted workers read. Import `postman/Aditya_Telemetry.postman_collection.json` and run its 19 requests in order against a freshly started server (recorded run: 59/59 assertions passed, `docs/Aditya_Newman_Run.txt`).

## Run Irrigation and Alerts

```powershell
py -3 -m services.irrigation_alerts.app
```

Listens at `http://127.0.0.1:8003` (macOS/Linux: `python3 -m services.irrigation_alerts.app`). Seeded fixtures: `farm-001` (owner A, worker A granted), `farm-002` (owner B), `farm-003` (owner A, stalled event source for the 503 demo) and `irr-001` (an APPROVED request for the 409 demo). Import `postman/Thomas_Irrigation.postman_collection.json` and run its 13 requests in order against a freshly started server.

## Test

```powershell
py -3 -m unittest discover -s tests -v
```

Current result: 49 tests pass (farm, telemetry, irrigation, projection and combined start-up).

## Build the submission ZIP

```powershell
py -3 scripts/package_submission.py
```

Writes `dist/OzAgriMate_Code_Repository.zip`, excluding git metadata, caches and private evidence, then extracts it to a temporary folder and runs the tests there.

On macOS/Linux replace `py -3` with `python3`.

Import `postman/Pulkit_Farms.postman_collection.json` into Postman. Run all 11 requests in their saved order with one iteration. The collection captures the created farm ID automatically. The supplied user-run result records **33 passed assertions, zero failures, zero skipped assertions and zero errors**. See `evidence/README.md`.

## Implemented endpoints

| Method | Service path | Purpose |
|---|---|---|
| POST | `/farms` | Create a farm owned by the authenticated demonstration owner |
| GET | `/farms/{farmId}` | Retrieve a farm accessible to that owner |
| POST | `/farms/{farmId}/telemetry` | Submit one sensor reading from a registered edge gateway |
| GET | `/farms/{farmId}/telemetry` | List a farm's readings with filters (owner / granted worker) |
| POST | `/farms/{farmId}/irrigation-requests` | Create a pending irrigation request |
| PUT | `/farms/{farmId}/irrigation-requests/{requestId}` | Replace a pending request's editable details |

Use `Authorization: Bearer demo-owner-a`. `demo-owner-b` represents another owner; it cannot retrieve owner A's farms. `demo-worker-a` is denied farm creation. These are public local fixtures, not production OAuth tokens. No production authentication or cloud deployment is implemented.

## Repository structure

| Path | Contents |
|---|---|
| `run_all.py` | Starts all three services side by side for the demonstration |
| `services/telemetry/` | Telemetry service (Aditya): REST controller, ingestion and query services, anomaly detector, repository, accepted-reading publisher, farm access read model, identity adapter |
| `scripts/package_submission.py` | Builds `dist/OzAgriMate_Code_Repository.zip` and re-runs the tests from the extracted copy |
| `services/irrigation_alerts/` | Irrigation and Alerts service: irrigation requests implemented (Thomas); alert rules pending (Bradley) |
| `services/farm_management/` | HTTP adapter, application service, repository, models and demonstration access policy |
| `tests/` | HTTP integration tests per service plus a combined start-up test (49 tests in total) |
| `postman/` | One collection per endpoint owner, each with success and error scenarios and assertions |
| `diagrams/` | Editable SVGs and high-resolution PNGs |
| `docs/Pulkit_A4_Report_Section.docx` | Editable report contribution |
| `docs/Pulkit_A4_Report_Section.pdf` | Rendered report contribution |
| `docs/Pulkit_Report_Sections.md` | Text version of the architecture and API sections |
| `docs/Team_Integration_Contract.md` | Proposed service names, endpoint allocation and shared contracts |
| `docs/A2_Feedback_Response.md` | Scope, QA and validation corrections arising from A2 feedback |
| `evidence/README.md` | Verified Postman result and evidence custody summary |

## Team integration

| Owner | Assigned endpoint operations |
|---|---|
| Pulkit | POST /farms; GET /farms/{farmId} |
| Aditya | POST and GET /farms/{farmId}/telemetry |
| Thomas | POST /farms/{farmId}/irrigation-requests; PUT /farms/{farmId}/irrigation-requests/{requestId} |
| Bradley | POST /farms/{farmId}/alert-rules; DELETE /farms/{farmId}/alert-rules/{ruleId} |

Keep endpoint contracts, diagram names and service packages consistent. Read `CONTRIBUTING.md` before adding work. Component diagram ownership does not change code ownership: Thomas's Farm Management component view should match Pulkit's modules.

The course submission remains the combined architecture PDF, code ZIP, a video no longer than five minutes demonstrating all eight endpoints, and the agreed contribution form. Six of the eight endpoints are implemented; Bradley's two alert-rule endpoints remain to be merged into `services/irrigation_alerts/`.
