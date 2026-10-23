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

Proposed dedicated QA allocation remains ADR-02 Scalability (Aditya), ADR-03 Availability (Thomas), ADR-04 Interoperability (Bradley), ADR-05 Security (Pulkit). Elasticity and Reliability/Safety must still be addressed through these mechanisms and/or the remaining significant ADRs; all driving QAs need rationales. ADR-06/07/08 topics are not decided on behalf of their owners.

## Contract rules

- Copy the canonical eight paths into the report and Postman collection. Do not mix prefixed and unprefixed URLs.
- Proposed local ports: Farm Management 8001, Telemetry 8002, Irrigation and Alerts 8003. Production gateway routes `/api/v1` to service routes; no gateway implementation is required by A4.
- Use JSON. Errors use `{"error":{"code":"...","message":"..."}}`. Agree endpoint-specific status codes before implementation.
- Each service owns its records. No cross-service dictionary/table access. Services requiring farm existence/access should use the farm API or a clearly documented trusted fixture for the prototype; an in-memory dictionary in one process does not automatically share data with another.
- This pack implements only farm owner access. Time-limited paddock grants and agronomist sharing are target capabilities, not completed code.
- Test two distinct owners. Cross-farm checks must not rely on identifiers supplied by the caller.
- Service authentication/authorisation must also cover broker consumption/publishing in production through scoped identities and topic permissions.
- Telemetry event identity must include a stable reading ID, farm ID, device ID, UTC observation time, metric, value, unit and schema version. Finalise field spelling with Aditya before using events in runtime diagrams.
- Only validated accepted readings may trigger downstream actions. Quarantine suspicious readings and retain reason/provenance. Replays must be idempotent.
- Baseline alerts must work without AI. Proposed irrigation advice requires explicit approval plus controller-side limits; the REST prototype must never imply physical actuation happened.
- Initial architecture and deployment are proposals; do not mark ADRs Accepted until reviewed by the team.

## Outstanding review

Confirm framework, container names, event contract, QA metric boundaries, extension scope, prototype authorisation approach, and integration fixtures. Then cross-review the diagram/code/API mapping. Pulkit reviews Thomas's two ADRs, Farm Management component view, irrigation runtime view and two endpoints when available. No such review has yet been claimed.
