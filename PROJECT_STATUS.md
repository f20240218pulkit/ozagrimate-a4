# OzAgriMate project status

Updated 23 October 2026. Keep this file with the project for continuity.

Pulkit's allocation remains ADR-01, ADR-05, container view, deployment view, two farm endpoints with documentation/testing, architecture coordination, and review of Thomas's work.

Verified user-supplied Postman evidence: 11 request scenarios, 33 assertions passed, zero failures, zero skipped, zero errors, one iteration. The original screenshot and integrity record are retained in Pulkit's saved work pack. This public repository contains evidence/README.md with the verified results and checksum. The run used Postman web with Desktop Agent against 127.0.0.1:8001.

Farm API implementation previously passed ten integration tests in the assistant environment. It uses standard-library Python, fixed demonstration identities and in-memory records. No production OAuth or cloud deployment is implemented.

ADRs and target diagrams are proposed for team review. Team framework, boundaries and contracts still need alignment. No review of Thomas's artefacts or implementation of the other six endpoints is claimed. Final report assembly, combined-code validation, five-minute team video and agreed contribution form remain outstanding.

The submitted OzAgriMate Report.pdf supersedes earlier placeholder-author A2 drafts. Security is a driving QA. Security references are ASR19, ASR26 and ASR28.

## Update 24 October 2026 (Aditya)

Telemetry service added at `services/telemetry/` (port 8002): POST and GET `/farms/{farmId}/telemetry`, 14 HTTP tests, Postman collection with 19 requests and 59 assertions (Newman run passed, `docs/Aditya_Newman_Run.txt`). ADR-02 (Scalability) and ADR-06 (edge-to-cloud reading contract), Telemetry component view and Runtime Diagram 1 are in `docs/Aditya_A4_Report_Section.docx/.pdf` and `diagrams/`.

Integration: `run_all.py` starts all three services; `requirements.txt` records stdlib-only runtime; `scripts/package_submission.py` builds and verifies the clean ZIP. Full suite 49/49. With `run_all.py`, the farm, telemetry and irrigation Postman collections all passed (33, 59, 40 assertions).

Bradley's alert-rule endpoints now live in `services/irrigation_alerts/` (moved from Farm Management on 25 October so the code matches ADR-01 and the container view) and are served on port 8003 as `run_all.py` lists. Outstanding: Aditya's cross-review of Bradley's work and re-running the ZIP builder after the final merge.
