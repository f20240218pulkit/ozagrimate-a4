# Team integration contract proposal

Status: Proposed. Review together before independently extending code or diagrams. The workload allocation remains unchanged.

## Container and component vocabulary

| Container | Responsibility | Component diagram owner |
|---|---|---|
| Farm Management | Farms, ownership and scoped access | Thomas |
| Telemetry | Device adapters, normalisation, validation, ingestion and query | Aditya |
| Irrigation and Alerts | Irrigation requests, approved schedules, alert rules and notifications | Bradley |
| AI Recommendation | Isolated inference and explanation; no autonomous bypass of approval | No additional component view required |
| Integration Adapters | External feed normalisation, FMIS transfer and consented partner exchanges | No additional component view required |

The target also includes Web App, Mobile App, Farm Edge Gateway, API Gateway, Identity and Access, Event Broker and service-owned stores. Backend services are independently deployable. The component diagram for Farm Management must match Pulkit's actual modules even though Thomas draws it.

## Endpoint owners

| Owner | Endpoints |
|---|---|
| Pulkit | POST /farms; GET /farms/{farmId} |
| Aditya | POST /farms/{farmId}/telemetry; GET /farms/{farmId}/telemetry |
| Thomas | POST /farms/{farmId}/irrigation-requests; PUT /farms/{farmId}/irrigation-requests/{requestId} |
| Bradley | POST /farms/{farmId}/alert-rules; DELETE /farms/{farmId}/alert-rules/{ruleId} |

Proposed dedicated QA allocation: ADR-02 Scalability (Aditya), ADR-03 Reliability/Safety with offline Availability (Thomas), ADR-04 Interoperability (Bradley), ADR-05 Security (Pulkit). Thomas has proposed ADR-07 for an event-fed farm/access projection. Retain explicit availability scenarios and measures alongside safety so Assignment 2's driving availability concern remains covered. Elasticity and Performance also require individual rationales and measurable scenarios. These topics remain Proposed until team review.

## Contract rules

- Copy the canonical eight paths into the report and Postman collection. Do not mix prefixed and unprefixed URLs.
- Proposed local ports: Farm Management 8001, Telemetry 8002, Irrigation and Alerts 8003. Production gateway routes `/api/v1` to service routes; no gateway implementation is required by A4.
- Use JSON. Errors use `{"error":{"code":"...","message":"..."}}`. Agree endpoint-specific status codes before implementation.
- Each service owns its records. No cross-service dictionary/table access. ADR-07 proposes an event-fed, read-only farm/access projection in Irrigation and Alerts. The prototype may use a clearly documented trusted snapshot and event-consumer fixtures; an in-memory dictionary in one process does not automatically share data with another.
- This pack implements only farm owner access. Time-limited paddock grants and agronomist sharing are target capabilities, not completed code.
- Test two distinct owners. Cross-farm checks must not rely on identifiers supplied by the caller.
- Service authentication/authorisation must also cover broker consumption/publishing in production through scoped identities and topic permissions.
- Telemetry event identity must include a stable reading ID, farm ID, device ID, UTC observation time, metric, value, unit and schema version. Finalise field spelling with Aditya before using events in runtime diagrams.
- Only validated accepted readings may trigger downstream actions. Quarantine suspicious readings and retain reason/provenance. Replays must be idempotent.
- Baseline alerts must work without AI. Proposed irrigation advice requires explicit approval plus controller-side limits; the REST prototype must never imply physical actuation happened.
- Initial architecture and deployment are proposals; do not mark ADRs Accepted until reviewed by the team.

## Outstanding review

Confirm framework, container names, event contract, QA metric boundaries, extension scope, prototype authorisation approach, and integration fixtures. Then cross-review the diagram/code/API mapping. Pulkit reviews Thomas's two ADRs, Farm Management component view, irrigation runtime view and two endpoints when available. No such review has yet been claimed.

## Thomas and Bradley coordination proposal

Use `services/irrigation_alerts/` on port 8003. Agree these component names before drawing: REST Controller (`api.py`); Irrigation Application Service (`irrigation_service.py`, Thomas); Alert Rule Application Service (`alert_rule_service.py`, Bradley); Farm Access Projection (`farm_projection.py`); Repository (`repository.py`); Domain Model/Validator (`models.py`); Identity Adapter (`security.py`). Shared modules require a nominated editor and peer review to avoid conflicting changes. `app.py` starts the service. Proposed event consumption can be represented by `farm_events.py`; do not claim a deployed broker exists.

Farm Management is authoritative for farm ownership and scoped grants; Identity and Access issues/verifies identity tokens. Farm Management publishes farm/grant changes through the Event Broker; Irrigation and Alerts updates only its own read model. The current farm prototype does not publish these events. Thomas's Farm Management component view must distinguish implemented modules from a proposed Event Publisher/outbox adapter.

ADR-07 must address ASR19's revocation within one minute. Use versioned, ordered-per-farm events, idempotent application, durable delivery/outbox, recovery snapshots and a source freshness watermark/heartbeat. A recent unrelated event or an old unchanged grant is not proof of current authorisation. Define an end-to-end revocation budget of at most 60 seconds; reject new protected mutations when freshness cannot be established within that budget. Test revoked grants, duplicates, out-of-order events and stale projections. The prototype may demonstrate this with trusted fixtures; production guarantees remain unvalidated.

ADR-03 must define units, configurable safe bounds, observation freshness, anomaly/quarantine handling, approval authority, schedule expiry and a safe state after the 48-hour offline lease. Validate at request creation, approval and controller execution. Cloud grant revocation and cancellation on a disconnected controller are different guarantees: document and review that boundary against ASR19/ASR12 rather than promising offline immediate cancellation.

POST irrigation requests returns 201 with PENDING; PUT replaces editable details only while PENDING and returns 200. Non-pending updates return 409. Do not accept caller-supplied owner identity or approval status. Use the established JSON error envelope. Test authentication, cross-farm access, invalid/safe-limit inputs, missing resources and lifecycle conflicts. Seed an approved request for the 409 test if approval is outside the prototype.

The irrigation runtime diagram may show the full target workflow, but label approval, dispatch and physical execution as planned capabilities outside the two implemented endpoints. Include at least four participants. Suggested 18-word explanation: “Validated requests await owner approval; approved schedules reach the edge gateway, where controllers enforce safe limits during outages.”

Report assembly note: the updated standalone `diagrams/Container_View.svg` and `.png` supersede the container figure in the previously published Word/PDF report section. Replace that embedded figure when assembling the final team report.
