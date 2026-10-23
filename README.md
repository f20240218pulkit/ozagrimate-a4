# OzAgriMate — ISYS3459 Assignment 4

Team: Pulkit Sharma, Aditya Singh, Thomas Wight and Bradley Shears.

Software architecture and REST API prototype for the OzAgriMate agricultural platform. This initial contribution contains Pulkit's Farm Management implementation, two architectural decision records, container/deployment diagrams and API documentation. The remaining six endpoints and teammates' artefacts are pending integration. Target architectural decisions remain **Proposed**.

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

## Run Irrigation and Alerts

```powershell
py -3 -m services.irrigation_alerts.app
```

Listens at `http://127.0.0.1:8003` (macOS/Linux: `python3 -m services.irrigation_alerts.app`). Seeded fixtures: `farm-001` (owner A, worker A granted), `farm-002` (owner B), `farm-003` (owner A, stalled event source for the 503 demo) and `irr-001` (an APPROVED request for the 409 demo). Import `postman/Thomas_Irrigation.postman_collection.json` and run its 13 requests in order against a freshly started server.

## Test

```powershell
py -3 -m unittest discover -s tests -v
```

On macOS/Linux replace `py -3` with `python3`.

Import `postman/Pulkit_Farms.postman_collection.json` into Postman. Run all 11 requests in their saved order with one iteration. The collection captures the created farm ID automatically. The supplied user-run result records **33 passed assertions, zero failures, zero skipped assertions and zero errors**. See `evidence/README.md`.

## Implemented endpoints

| Method | Service path | Purpose |
|---|---|---|
| POST | `/farms` | Create a farm owned by the authenticated demonstration owner |
| GET | `/farms/{farmId}` | Retrieve a farm accessible to that owner |

Use `Authorization: Bearer demo-owner-a`. `demo-owner-b` represents another owner; it cannot retrieve owner A's farms. `demo-worker-a` is denied farm creation. These are public local fixtures, not production OAuth tokens. No production authentication or cloud deployment is implemented.

## Repository structure

| Path | Contents |
|---|---|
| `services/irrigation_alerts/` | Irrigation and Alerts service: irrigation requests implemented (Thomas); alert rules pending (Bradley) |
| `services/farm_management/` | HTTP adapter, application service, repository, models and demonstration access policy |
| `tests/` | Ten HTTP integration tests including validation and owner isolation |
| `postman/` | Eleven success/error request scenarios with assertions |
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

The course submission remains the combined architecture PDF, code ZIP, a video no longer than five minutes demonstrating all eight endpoints, and the agreed contribution form. This repository currently contains only Pulkit's implemented subset.
