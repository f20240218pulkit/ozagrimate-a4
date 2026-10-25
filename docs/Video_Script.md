# Team video script (target 4:45, hard limit 5:00)

Only the first five minutes are marked. The spec asks for two things: how the repository
structure reflects the Container and Component diagrams, and a Postman demo of all eight
endpoints with successful and relevant error responses. ADRs and code detail are not needed.

## Before recording

1. `git pull` on `main`, then start everything fresh: `py -3 run_all.py`. Leave it running.
   Restart it before every take, because IDs and seeded data reset only on restart.
2. In Postman import `postman/OzAgriMate_Video_Demo.postman_collection.json`.
   Open the collection > **Variables** and check `farmUrl` = `http://127.0.0.1:8001`,
   `telemetryUrl` = `http://127.0.0.1:8002`, `irrigationAlertsUrl` = `http://127.0.0.1:8003`.
   Postman sometimes drops collection variables on import.
3. Do a full practice run with the Collection Runner (17 requests, 50 assertions), then restart
   `run_all.py` before the real take.
4. Have open, in this order: the container diagram, the repo in your editor/file explorer,
   the three component diagrams, Postman. Close anything showing email or account details.

## 0:00-0:15 Intro (15 s)

> "This is the OzAgriMate prototype. We used a service-based architecture, so each backend
> container in our design is its own Python service with its own port and in-memory data."

## 0:15-1:30 Repository vs diagrams (75 s)

| Time | Show | Say |
|---|---|---|
| 0:15 | `diagrams/Container_View.png` | "The container view has three backend services we implemented: Farm Management, Telemetry, and Irrigation and Alerts." |
| 0:30 | `services/` folder | "Each one is a package under `services`: `farm_management`, `telemetry` and `irrigation_alerts`, on ports 8001, 8002 and 8003. Containers we didn't implement, like AI Recommendation, have no package; the spec allows that." |
| 0:45 | Farm Management component diagram, then `services/farm_management/` | "Each component is one module: REST Controller is `api.py`, Application Service is `service.py`, Repository is `repository.py`, plus models and the identity adapter." |
| 1:00 | Telemetry component diagram, then `services/telemetry/` | "Same for Telemetry: ingestion service, query service, anomaly detector, repository and event publisher are separate modules." |
| 1:15 | Irrigation and Alerts component diagram, then `services/irrigation_alerts/` | "Irrigation and Alerts shares one REST controller between `irrigation_service.py` and `alert_rule_service.py`, and checks farm access against its own `farm_projection.py` instead of reading Farm Management's data." |

Then `run_all.py` running in the terminal (2 s): "`run_all.py` starts all three side by side."

## 1:30-4:25 Postman: all eight endpoints (about 10 s per request)

Send each request and point at the status code and the key field. Folder headings show the port.

| # | Request | Point at |
|---|---|---|
| 01 | POST /farms | 201, server-assigned `farm-001`, Location header |
| 02 | GET /farms/{farmId} | 200, same farm |
| 03 | GET as owner B | 404 FARM_NOT_FOUND: other owners can't see the farm |
| 04 | POST /farms as worker | 403 FORBIDDEN |
| 05 | POST /telemetry from gateway | 201, status ACCEPTED |
| 06 | POST spike reading | 201 but QUARANTINED: suspicious readings don't trigger actions |
| 07 | POST 101 % moisture | 422 VALIDATION_ERROR |
| 08 | GET /telemetry as owner | 200, readings in time order |
| 09 | GET /telemetry as owner B | 404 |
| 10 | POST /irrigation-requests as worker | 201, status PENDING |
| 11 | PUT /irrigation-requests/{id} | 200, full replacement, version 2, still PENDING |
| 12 | PUT on approved request irr-001 | 409 REQUEST_NOT_EDITABLE |
| 13 | POST 241 minutes | 422: above the safe limit |
| 14 | POST /alert-rules as owner | 201, `rule-001` |
| 15 | POST /alert-rules as worker | 403: only owners manage rules |
| 16 | DELETE /alert-rules/{id} | 204 No Content |
| 17 | DELETE same rule again | 404 RULE_NOT_FOUND |

If you are running long, drop 04, 09 and 15 (about 30 s saved); every endpoint still shows a
success and an error.

## 4:25-4:45 Runner result and close (20 s)

Show a Collection Runner result for the demo collection: 17 requests, 50 assertions passed,
0 failed. Restart `run_all.py` first if you already sent the requests by hand, or show a
screenshot of an earlier run.

> "All eight endpoints work with success and error cases, and each service's folders mirror its
> container and component diagrams. Thanks."

## Fallbacks

- **Connection refused / no response:** `run_all.py` isn't running, or a variable is blank.
- **Wrong IDs or an unexpected 409/404:** restart `run_all.py` and run from 01 again.
- **Over time:** cut lines from the repository section first. The endpoint demo carries the marks.
