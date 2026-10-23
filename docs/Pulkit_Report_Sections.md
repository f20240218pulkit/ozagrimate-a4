# OzAgriMate architecture and farm API sections

Author: Pulkit Sharma. Student number: insert verified student number before submission.

## Design basis

The submitted Assignment 2 report identifies Scalability, Availability and Interoperability as its top three driving characteristics, alongside Security, Elasticity, Reliability / Safety, and Performance. Its constraints require Australian data processing/residency, constrained field networks, offline operation, managed operations for at most eight engineers, and releases without planned seasonal downtime. These are project requirements; residency is not presented here as a general legal interpretation of the Privacy Act.

The target design uses service-based architecture with asynchronous telemetry processing, managed infrastructure, a farm-edge buffer, and local irrigation continuity. The assignment implementation contains only the eight selected REST operations across the team. This pack implements Pulkit's two. Production targets require separate validation.

## ADR-01

| Field | Content |
|---|---|
| Title | ADR-01 Adopt service-based architecture with asynchronous telemetry processing |
| Status | Proposed |
| Context | OzAgriMate must grow from 5,000 to over 50,000 farms while supporting heterogeneous devices, rural outages, and seasonal load spikes. Constraints C4 and C5 require managed operations by at most eight engineers and releases without planned seasonal downtime. A layered monolith couples scaling and releases; fine-grained microservices increase operational overhead. Coarse-grained services offer a middle ground. |
| Decision | Adopt service-based architecture with Farm Management, Telemetry, and Irrigation and Alerts services, plus an isolated AI Recommendation service. Use REST for immediate operations and managed durable messaging for telemetry-driven processing. Deploy on managed Australian-region infrastructure. Edge buffering and local approved schedules support disconnected farms. Coarse boundaries permit independent scaling and releases while limiting service proliferation. Isolating AI supports ASR21: baseline monitoring and alerts continue if recommendations fail. |
| Consequences | Independent scaling and failure isolation support seasonal growth and continuity. Distribution introduces network failures, eventual consistency, duplicate-message handling, contract management, and monitoring costs. Managed infrastructure reduces operational effort but creates vendor dependencies. Broker delivery requires idempotent consumers. The in-memory endpoint prototype demonstrates service structure, not production durability, elasticity, or uptime. |
| Compliance | Review code boundaries against diagrams; verify API contracts and AI-independent alert flow. Validate seasonal scaling, failover, and rolling releases through production-like load and resilience tests. |

Traceability: ASR3, ASR12, ASR15, ASR21, ASR22; constraints C1-C5. This style decision supports several QAs but does not replace the four dedicated QA ADRs.

## ADR-05

| Field | Content |
|---|---|
| Title | ADR-05 Enforce farm-scoped authorisation at every service boundary |
| Status | Proposed |
| Context | ASR19 requires scoped, time-limited access revocable within one minute; ASR26 requires farm isolation. Owners control access, while workers and agronomists need narrower permissions. Trusting caller-supplied farm identifiers or gateway-only checks risks cross-farm disclosure. Separate databases per farm offer stronger physical separation but increase operational cost at 50,000 farms. |
| Decision | Use managed OAuth access tokens and service-level authorisation against trusted farm and paddock grants. Restrict repository queries by authorised scope and deny by default. Give grants expiry times and invalidate cached permissions so revocation propagates within one minute. Distinguish owner, worker, agronomist, operations manager, and platform administrator permissions. Platform administration does not automatically grant farm-data access. The prototype substitutes fixed demonstration identities and implements only owner creation and owner-scoped retrieval. |
| Consequences | Scoped checks reduce cross-farm disclosure and support controlled sharing without per-farm database proliferation. Policy enforcement and grant invalidation add complexity and availability dependencies. Authentication alone does not establish authorisation. Missing and inaccessible farms return identical retrieval errors. Prototype fixtures do not validate OAuth, grant revocation, encryption, audit integrity, or production security. |
| Compliance | Test permitted and denied farm/paddock access and revocation within one minute. Review repository scoping, validate token controls, and independently assess production isolation. |

Traceability: ASR19, ASR26, ASR28; Security driving QA. The referenced ASR identifiers follow the submitted Assignment 2 report.

## Container view

Insert `diagrams/Container_View.png` as a readable landscape figure, or use its SVG where supported. Caption: OzAgriMate proposed C4 Container Diagram.

Farm Management owns farm records and grants. Telemetry normalises readings through adapters, validates them, stores accepted readings and publishes accepted-reading events. Irrigation and Alerts owns irrigation requests, schedules and alert rules, consuming accepted readings without depending on AI availability. AI Recommendation consumes relevant observations and weather data and emits advice; it does not bypass approval or controller limits. A shared managed data platform exposes separate service-owned stores and credentials. No service reads another service's tables directly. Farm Management publishes farm/grant events through the Event Broker to Irrigation and Alerts, which maintains its own read-only projection. This messaging flow is target architecture; the current farm prototype does not publish events. ADR-07 must bound projection staleness to satisfy ASR19's one-minute revocation requirement.

Web and mobile applications call the managed API gateway, which routes to backend services. The mobile app and edge gateway retain offline data. Field transport is adapted at the edge; ISOBUS, ADAPT, LoRaWAN and NB-IoT are not treated as interchangeable protocols. The cloud-facing envelope is normalised JSON. Managed OAuth identity and service-level policies secure REST requests; messaging identities and topic permissions secure asynchronous paths.

Additional external integrations are grouped in the view to keep it readable. The Integration Adapters container mediates BOM/biosecurity feeds, FMIS imports, and approved partner exchanges. The team must preserve these names and responsibilities in its component and runtime views. Architecture coverage exceeds the prototype's implemented endpoint subset.

## Deployment view

Insert `diagrams/Deployment_View.png` as a readable landscape figure. Caption: OzAgriMate proposed C4 Deployment Diagram.

The target environment places the API gateway, managed compute, identity, data, messaging, and operational telemetry in Australian regions. Two availability zones host backend service instances; shared durable data and messaging prevent dependence on process-local state. Rolling deployments retain compatible API/event schemas and route traffic only to ready instances. The mobile device and farm gateway run on-farm; gateways buffer telemetry for 72 hours and controllers retain the last approved schedule for 48 hours with local safety limits and overrides.

Backups and an Australian recovery region support the proposed four-hour RTO and fifteen-minute RPO. Meeting these targets requires measured backup/replication lag, restore rehearsals and regional failover tests. The picture does not establish that the targets are achieved. Check all chosen managed services, backups, identity data and logs against C1 before implementation.

The local prototype runs only Farm Management in one Python process at 127.0.0.1:8001 with an in-memory repository. No cloud, broker, gateway, OAuth provider or production database has been deployed.

## API design

Paths are preserved from the team allocation. Production versioning required by ASR16 is proposed at the gateway as `/api/v1` plus these service paths. This prototype exposes the service paths directly. Do not silently add a prefix in one teammate's implementation.

| HTTP Method | Description | Endpoint URL | Sample Request Body | Sample Response Body |
|---|---|---|---|---|
| POST | Create a farm owned by the authenticated owner | /farms | Creation JSON below | Farm JSON below |
| GET | Retrieve details of an accessible farm | /farms/{farmId} | N/A | Farm JSON below |

Creation JSON:

```json
{"name":"Riverbend Farm","latitude":-36.36,"longitude":145.4,"areaHectares":125.5}
```

Farm JSON, assuming the first creation after starting the server:

```json
{"id":"farm-001","name":"Riverbend Farm","latitude":-36.36,"longitude":145.4,"areaHectares":125.5}
```

POST returns 201 with `Location: /farms/{id}`; GET returns 200. IDs are generated server-side and should be treated as opaque by consumers. Subsequent records receive different IDs. Duplicate names are allowed. Names are trimmed. The JSON object must contain exactly the four documented request fields. Name length after trimming is 1-120; latitude is -90 to 90; longitude is -180 to 180; area is a finite number greater than zero. Booleans, nulls and numeric strings are rejected. Coordinates are validated numerically; this prototype does not geofence Australian land.

GET request body: N/A. Use the ID captured from POST. A syntactically valid but nonexistent or inaccessible farm returns 404 with the same body. Malformed route identifiers do not match the route and return ROUTE_NOT_FOUND. There is no list or delete endpoint in this subset.

Both endpoints require `Authorization: Bearer demo-owner-a` in the demonstration. Caller-supplied ownership fields are rejected. The trusted fixture identity determines ownership. Owner B cannot access owner A's record. Workers and agronomists have no implemented read grants in this subset; that does not remove their proposed production roles.

| Operation | Status | Error code | Trigger |
|---|---|---|---|
| Both | 401 | UNAUTHENTICATED | Missing or invalid local fixture bearer token |
| POST | 403 | FORBIDDEN | Authenticated worker attempts farm creation |
| POST | 400 | INVALID_JSON | Malformed UTF-8 JSON or literal NaN/Infinity |
| POST | 415 | UNSUPPORTED_MEDIA_TYPE | Content-Type is not application/json |
| POST | 422 | VALIDATION_ERROR | Missing/unknown fields or invalid values |
| GET | 404 | FARM_NOT_FOUND | Record absent or inaccessible |
| Transport | 413 | BODY_TOO_LARGE | Body exceeds 65,536 bytes |
| Transport | 408 | REQUEST_TIMEOUT | Request body read times out |
| Transport | 400 | INVALID_LENGTH / INVALID_FRAMING / INCOMPLETE_BODY | Invalid or unsupported HTTP framing |
| Known path | 405 | METHOD_NOT_ALLOWED | Unsupported method; Allow header states supported method |
| Unknown path | 404 | ROUTE_NOT_FOUND | No matching application endpoint |

Error response example:

```json
{"error":{"code":"FARM_NOT_FOUND","message":"Farm not found or not accessible."}}
```

## Repository and component alignment

Farm Management's component view, owned by Thomas, should represent these three principal components: Farm REST Controller (`api.py`), Farm Application Service (`service.py`), Farm Repository (`repository.py`). Supporting Domain Models (`models.py`) and Access Policy (`security.py`) can also be shown. `app.py` is the HTTP composition root. HTTP handling delegates to the application service, which delegates scoped storage access to the repository.

The code implements the diagram's Farm Management container only. Other component diagrams are owned by their allocated authors. Package paths are supplied for integration; empty folders must not be represented as implemented services.

## Demonstration evidence

Ten Python integration tests exercise real local HTTP requests. They cover create/read contract agreement; owner isolation; rejected caller ownership; worker denial; absent/invalid authentication; numeric/name validation; malformed and non-finite JSON; missing/extra fields; media type/body limits/method handling; generated IDs and trimming. Pulkit ran the collection through the Postman web interface using the Desktop Agent. The supplied screenshot records 11 request scenarios, 33 assertions passed, zero failed, zero skipped and zero errors. The run shows 201 for creation, 200 for retrieval, and expected 404 for cross-owner access denial. This is execution evidence for the two farm endpoints, not all eight team endpoints.

Production QA targets, UI behaviour, cloud failover, 50,000-farm load, physical actuation and provider interoperability have not been verified by these tests. Do not present proposed architecture mechanisms as achieved test results.

## Sources

1. Team submission, OzAgriMate Report.pdf, pp. 1-10, supplied by Pulkit; primary baseline for ASR and constraint IDs.
2. ISYS3459 Assignment 4 activity PDF, pp. 1-4, supplied course instructions.
3. Supplied ADR Template.pdf; field structure and maximum word counts.
4. Assignment 2 marker feedback supplied by Pulkit; scope, stakeholder, validation, QA rationale and relationship issues.

5. Brown, S. (n.d.). Container diagram. C4 model. https://c4model.com/diagrams/container (accessed 23 October 2026).
6. Brown, S. (n.d.). Deployment diagram. C4 model. https://c4model.com/diagrams/deployment (accessed 23 October 2026).

Architecture decisions remain Proposed until team review. The final team document must include all names/student numbers and the completed A2 QA template.
