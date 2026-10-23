# Farm API execution evidence

Pulkit supplied a screenshot of the completed Postman run on 23 October 2026. The run used the Postman web interface with Desktop Agent against http://127.0.0.1:8001.

| Measure | Observed result |
|---|---|
| Request scenarios | 11 across POST /farms and GET /farms/{farmId} |
| Passed assertions | 33 |
| Failed assertions | 0 |
| Skipped assertions | 0 |
| Run errors | 0 |
| Iterations | 1 |
| Displayed run time | 03:11:47 AM |
| Displayed duration | 2 seconds 166 milliseconds |
| Displayed average response time | 5 milliseconds |

The screenshot visibly confirms 201 creation, 200 retrieval and an expected 404 for denied cross-owner access. The collection includes the other validation/authentication scenarios. These results concern the local Farm Management subset, not the remaining six team endpoints or production performance targets.

The original screenshot is preserved separately in Pulkit's saved work pack as `evidence/Postman_Run_2026-10-23.png`. It is omitted from this public repository because it contains browser/account details. Original SHA-256: `8923891397fac46ea87ac9f5411d193bdcf8a2fd7b094f6fba91e25d07a95e8f`.

Ten HTTP integration tests also passed during implementation; see `tests/test_farm_http.py` and `docs/Validation_Result.txt`.
