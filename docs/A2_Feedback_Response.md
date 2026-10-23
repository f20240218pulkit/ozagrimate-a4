# Assignment 2 feedback response for Assignment 4

## Correct baseline

Use the supplied OzAgriMate Report.pdf, authored by Pulkit Sharma, Aditya Singh, Thomas Wight and Bradley Shears. Earlier reports with placeholder authors are superseded as design inputs. The submitted report has seven driving characteristics, not three driving plus security as an implicit characteristic.

## Scope boundary proposal

Keep farm monitoring, telemetry, irrigation management, alerts and AI-assisted decision support as core. Retain carbon verification, autonomous dosing, commodity trading and agri-finance as bounded extension capabilities because they appear in A2. They are outside the eight-endpoint prototype. The Integration Adapters boundary may export consented records and receive external evidence, but this prototype neither certifies carbon credits nor executes trades, lending decisions, drone dispatch or chemical dosing. If the team removes an extension from the target architecture, record that as an explicit A4 scope revision and update affected ASRs/context relationships rather than silently omitting it.

For any retained carbon-verification capability, the team must identify an accepted methodology, reference measurements, error tolerance, calibration procedure and independent verification before claiming accuracy. No unsupported accuracy target is invented here.

## Stakeholder separation

- Farm Owner: controls ownership, sharing and consent; can create a farm.
- Farm Worker: performs authorised operational tasks; does not inherit ownership or sharing authority.
- Agronomist: accesses only granted farms/paddocks and advises or overrides within scope.
- Operations Manager: oversees expressly authorised farms; no blanket cross-tenant access.
- Platform Administrator: manages platform configuration; infrastructure administration does not imply permission to read all farm records.

## ASR5 telemetry validation proposal

Aditya's telemetry work and Thomas's irrigation workflow should agree on metric-specific units, bounds, timestamp rules, device identity, replay rules and handling before implementation. An example validation fixture is soil moisture as volumetric water content in percent, with numeric bounds 0-100; this is a schema range, not proof of agronomic accuracy. Spike thresholds depend on sensor type, calibration and sampling interval and require explicit configuration.

Reject malformed readings with a documented error. Quarantine well-formed but suspicious readings with reason codes and provenance; exclude them from action-triggering events. Do not silently discard evidence. Duplicate replayed readings must not create duplicate actions. Thresholds and quarantine behaviour are proposals for the responsible teammates to finalise, not implemented features of Pulkit's farm API.

## Missing driving QA rationales

Retain all seven driving characteristics and add the missing four individual rationales. These proposed additions are each at most 25 words.

| QA | Proposed concise rationale |
|---|---|
| Security | Protect farm isolation and scoped sharing; verify cross-farm access is denied and access revocation propagates within one minute. |
| Elasticity | Seasonal telemetry can spike tenfold; scale ingestion automatically while preserving accepted readings, then release excess capacity after demand falls. |
| Reliability / Safety | Rural outages and faulty sensors must not cause unsafe actuation; validate readings and preserve locally approved schedules with bounded controller operation. |
| Performance | Timely decisions protect crops; measure ingestion below two seconds, irrigation recommendations within sixty seconds, and critical alert delivery within sixty seconds. |

Each rationale needs a detailed scenario or verification plan in the QA section. Add testable descriptions for retained implicit and other characteristics as well; four added lines alone do not complete the entire QA template.

## Targets needing reconciliation

- ASR1 says ingestion under two seconds; the scalability rationale says sub-second. Proposed reconciliation: p95 durable acceptance below one second, and p95 end-to-end normalisation/storage below two seconds. Define the workload, payload, device count, farm count and measurement boundaries before treating this as a valid acceptance target.
- ASR10 requires emergency alerts within 60 seconds; ASR13 allows two minutes. Proposed classification: critical emergencies within 60 seconds; other alerts within 120 seconds. Define classes and external-provider delivery assumptions.
- 99.9% seasonal availability does not mean every outage is under five minutes. Track uptime percentage and maximum interruption separately. Agree on measurement window, exclusions, incident start/end and external notification dependency handling.
- 50,000 farms and a tenfold spike are not a message rate. Workload assumptions must specify devices per farm, reporting frequency, message size and backlog replay rate.
- A 72-hour buffer cannot always drain within 15 minutes over a constrained uplink. Size local storage and reconnection bandwidth against a defined workload; reserve live-ingestion capacity and detect replay duplicates.
- C1 is a stated residency constraint. Validate Australian processing for databases, backups, identity, logs and chosen providers; do not infer a universal legal residency obligation.

## Context relationships

Bradley's context view should label direction and information exchanged for every retained external system. Split incoming telemetry and outgoing approved commands. Separate consented partner exports from price-feed ingestion and any proposed trade execution. Distinguish future extensions from core capability. All people and systems require descriptions inside diagram elements.

## Responsibility and completion

Pulkit supplies the corrected basis, style/security decisions and target diagrams. Thomas integrates the revised QA template and scope note into the report; Bradley updates context relationships; Aditya finalises telemetry validation. These are coordination inputs within the existing allocation, not additional completed work attributed to those members.
