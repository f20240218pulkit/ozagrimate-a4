// Builds docs/Aditya_A4_Report_Section.docx. Run from repo root: node docs/build_aditya_report.js
// Helpers copied from Thomas's builder so all report sections share one style.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel,
  WidthType, ShadingType, PageOrientation, AlignmentType, BorderStyle, PageBreak, Footer, PageNumber,
} = require("docx");

const C = JSON.parse(fs.readFileSync("docs/aditya_report_content.json", "utf8"));
const INK = "183047", HEAD = "D9EBFA", RULE = "9BB0C0";
const W = 9638; // A4 text width at 2 cm margins (DXA)

const run = (text, o = {}) => new TextRun({ text, font: "Calibri", size: o.size || 21, bold: o.bold, italics: o.italics, color: o.color || INK });
const mono = (text) => new TextRun({ text, font: "Consolas", size: 17, color: INK });
const para = (children, o = {}) => new Paragraph({ children: typeof children === "string" ? [run(children)] : children, spacing: { after: o.after ?? 120, before: o.before ?? 0 }, alignment: o.align });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(t, { size: 30, bold: true })], spacing: { before: 280, after: 120 } });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(t, { size: 24, bold: true })], spacing: { before: 200, after: 100 } });
const caption = (t) => new Paragraph({ children: [run(t, { size: 19, bold: true })], spacing: { before: 60, after: 160 } });

const border = { style: BorderStyle.SINGLE, size: 4, color: RULE };
const borders = { top: border, bottom: border, left: border, right: border };
function cell(content, width, o = {}) {
  const children = Array.isArray(content) ? content : [new Paragraph({ children: [o.code ? mono(content) : run(content, { bold: o.bold, size: o.size || 18 })] })];
  return new TableCell({ children, width: { size: width, type: WidthType.DXA }, borders,
    shading: o.head ? { type: ShadingType.CLEAR, color: "auto", fill: HEAD } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 } });
}
function table(widths, rows, headRow = true) {
  return new Table({ width: { size: widths.reduce((a, b) => a + b), type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: headRow && i === 0,
      children: r.map((v, j) => cell(v, widths[j], { head: headRow && i === 0, bold: (headRow && i === 0) || (!headRow && j === 0) })) })) });
}
const codeCell = (v, w) => cell(v.split("\n").map(l => new Paragraph({ children: [mono(l)] })), w);
function image(path, widthPx) {
  const data = fs.readFileSync(path);
  const w = data.readUInt32BE(16), h = data.readUInt32BE(20);
  return new Paragraph({ children: [new ImageRun({ type: "png", data, transformation: { width: widthPx, height: Math.round(widthPx * h / w) },
    altText: { title: path, description: path, name: path } })], spacing: { after: 60 } });
}
function adr(a, trace) {
  const rows = ["Title", "Status", "Context", "Decision", "Consequences", "Compliance"].map(k => [k, a[k]]);
  return [table([1800, W - 1800], [["Field", "Architectural decision record"], ...rows]),
    para([run("Traceability: ", { bold: true, size: 19 }), run(trace, { size: 19 })], { before: 80 })];
}


const R = { schemaVersion: 1, readingId: "sm-north-01-20261023T2045Z", deviceId: "sm-north-01", paddockId: "north-paddock", metric: "soilMoisture", value: 29.7, unit: "%", observedAt: "2026-10-23T20:45:00Z" };
const POST_REQ = JSON.stringify(R, null, 1);
const POST_RES = JSON.stringify({ readingId: R.readingId, farmId: "farm-001", deviceId: R.deviceId, paddockId: R.paddockId, metric: R.metric, value: R.value, unit: R.unit, observedAt: R.observedAt, receivedAt: "2026-10-24T12:06:37Z", status: "ACCEPTED", quarantineReasons: [], schemaVersion: 1 }, null, 1);
const GET_RES = JSON.stringify({ farmId: "farm-001", count: 2, hasMore: false, readings: [
  { readingId: "sm-north-01-20261023T2030Z", farmId: "farm-001", deviceId: "sm-north-01", paddockId: "north-paddock", metric: "soilMoisture", value: 30.1, unit: "%", observedAt: "2026-10-23T20:30:00Z", receivedAt: "2026-10-23T20:30:04Z", status: "ACCEPTED", quarantineReasons: [], schemaVersion: 1 },
  { readingId: "sm-north-01-20261023T2045Z", farmId: "farm-001", deviceId: "sm-north-01", paddockId: "north-paddock", metric: "soilMoisture", value: 29.7, unit: "%", observedAt: "2026-10-23T20:45:00Z", receivedAt: "2026-10-24T12:06:37Z", status: "ACCEPTED", quarantineReasons: [], schemaVersion: 1 }] }, null, 1);

function endpointTable(method, desc, url, req, res, status) {
  const w = [2200, W - 2200];
  const r = (k, v, code) => new TableRow({ children: [cell(k, w[0], { bold: true }), code ? codeCell(v, w[1]) : cell(v, w[1])] });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: w, rows: [
    new TableRow({ tableHeader: true, children: [cell("Specification", w[0], { head: true }), cell("Value", w[1], { head: true })] }),
    r("HTTP Method", method), r("Description", desc), r("Endpoint URL", url),
    r("Sample Request Body", req, req !== "N/A"), r("Sample Response Body", res, true), r("Success status", status)] });
}
const pb = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [run(t, { size: 30, bold: true })], spacing: { after: 120 } });

const body = [
  new Paragraph({ children: [run("OzAgriMate Telemetry Architecture and API", { size: 40, bold: true })], spacing: { after: 60 } }),
  para([run("Aditya Singh | ISYS3459 Assignment 4 | 24 October 2026", { size: 22, color: "486174" })], { after: 200 }),
  para("These sections document the architecture decisions, Telemetry component view, telemetry runtime view and telemetry API contributed by Aditya Singh, plus the repository integration work. The two telemetry endpoints pass 14 automated HTTP tests and a 19-request Postman collection with 59 of 59 assertions passing. Architecture decisions remain Proposed pending team review."),

  h1("Design basis and scope"),
  para("The submitted Assignment 2 report lists Scalability among its top driving characteristics: the platform must grow from 5,000 to over 50,000 farms with tenfold seasonal telemetry spikes. ASR1 targets ingestion below two seconds, ASR5 requires suspicious readings not to trigger automated actions, ASR16 requires versioned APIs, constraint C3 requires 72-hour offline edge operation and C4 limits operations to at most eight engineers. ADR-01 places telemetry in its own Telemetry service, which owns the Telemetry Store and publishes accepted readings through the Event Broker."),
  para("This contribution implements reading submission and farm-scoped reading retrieval. The Farm Edge Gateway, Event Broker, autoscaling and the time-series database are target architecture; the prototype uses in-memory partitions and an in-memory outbox."),
  h2("Contribution coverage"),
  table([3000, W - 3000], [["Artefact", "Scope and status"],
    ["ADR-02", "Scalability (driving QA A); Proposed"],
    ["ADR-06", "Edge-to-cloud reading contract (technology/interface decision); Proposed"],
    ["Telemetry component view", "Ten components, one-to-one with services/telemetry/ modules"],
    ["Runtime view 1", "Telemetry submission and processing; edge buffering and broker steps marked planned"],
    ["Telemetry API", "POST and GET /farms/{farmId}/telemetry; local implementation on port 8002"],
    ["Repository integration", "run_all.py, requirements.txt, README start-up instructions, clean ZIP builder"],
    ["Testing evidence", "14 telemetry tests; 49 of 49 repository tests; Newman run 19 requests, 59 of 59 assertions"]]),

  pb("ADR 02 Scalable telemetry ingestion"),
  ...adr(C.adr02, "Scalability driving QA (5,000 to 50,000+ farms; tenfold seasonal spikes); ASR1; constraints C3 and C4; supports Elasticity. Builds on ADR-01 asynchronous telemetry processing; quarantined readings are never published (ASR5, ADR-03)."),
  h1("ADR 06 Edge-to-cloud reading contract"),
  ...adr(C.adr06, "ASR5, ASR16; constraint C3; Interoperability and Scalability QAs. Event fields satisfy the team integration contract (stable reading ID, farm ID, device ID, UTC time, metric, value, unit, schema version). Enables ADR-02 idempotent replay."),

  pb("Telemetry component view"),
  caption("OzAgriMate Telemetry C4 Component Diagram"),
  image("diagrams/Telemetry_Components.png", 560),
  para("The view decomposes the Telemetry container into the modules implemented in services/telemetry/, so diagram and repository correspond one-to-one. Field-protocol adaptation happens on the Farm Edge Gateway (ADR-06), so Telemetry contains no vendor adapters. Interactions with the Event Broker and consuming services are dashed because no broker is deployed.", { before: 120 }),
  table([3000, 2600, W - 5600], [["Component", "Module", "Responsibility"],
    ["HTTP Server", "app.py", "Local HTTP transport and composition root, port 8002"],
    ["Telemetry REST Controller", "api.py", "Routes POST and GET telemetry; maps errors to the JSON envelope"],
    ["Identity Adapter", "security.py", "Resolves user or gateway principal (demonstration fixtures)"],
    ["Telemetry Ingestion Service", "ingestion_service.py", "Authorise, validate, de-duplicate, classify, store, publish"],
    ["Telemetry Query Service", "query_service.py", "Farm-scoped filtered reads capped at 500 rows"],
    ["Farm Access Read Model", "farm_access.py", "Local copy of farms, grants and gateway bindings"],
    ["Reading Model / Validator", "models.py", "Schema v1 contract, units, ranges and timestamps"],
    ["Anomaly Detector", "anomaly_detector.py", "Spike and plausibility checks; quarantine reasons"],
    ["Telemetry Repository", "repository.py", "Per-farm partitions keyed by readingId"],
    ["Accepted Reading Publisher", "event_publisher.py", "Outbox of ReadingAccepted events, partitioned by farmId"]]),
];

const runtime = [
  h1("Runtime view: telemetry submission and processing"),
  caption("OzAgriMate Runtime Diagram 1: telemetry submission and processing (UML sequence)"),
  para([run("Interaction flow: ", { bold: true }), run(C.runtime_explanation)], { after: 60 }),
  image("diagrams/Telemetry_Runtime.png", 700),
];

const api = [
  h1("Telemetry API design"),
  para("Paths follow the team integration contract. Production versioning is proposed as /api/v1 at the gateway; the prototype exposes the unprefixed service paths at http://127.0.0.1:8002."),
  h2("POST /farms/{farmId}/telemetry"),
  endpointTable("POST", C.post_description, "/farms/{farmId}/telemetry", POST_REQ, POST_RES, "201 Created (new reading); 200 OK (identical replay returns the original record)"),
  h2("GET /farms/{farmId}/telemetry"),
  endpointTable("GET", C.get_description, "/farms/{farmId}/telemetry?metric=soilMoisture&from=2026-10-23T20:30:00Z", "N/A", GET_RES, "200 OK"),
  para("receivedAt is assigned by the server, so its value differs on each run. A spike or implausible value is still stored (201) but with status QUARANTINED and reasons such as SPIKE_DETECTED or IMPLAUSIBLE_VALUE; it is never published as an accepted reading.", { before: 120 }),

  h2("Validation and error behaviour"),
  para("A POST body must contain exactly schemaVersion, readingId, deviceId, paddockId, metric, value, unit and observedAt. farmId comes from the URL and status from the service; caller-supplied farmId, status or receivedAt is rejected. schemaVersion must be 1. readingId is 1 to 80 letters, digits, '.', '_', ':' or '-'. deviceId and paddockId are lowercase slugs. Supported metrics and units: soilMoisture in % (0 to 100), soilTemperature in degC (-20 to 60), airTemperature in degC (-50 to 60) and rainfall in mm (0 to 500). observedAt is a UTC timestamp at most five minutes in the future."),
  para("GET accepts optional metric, deviceId, paddockId, from, to, status (ACCEPTED by default, QUARANTINED or ALL) and limit (1 to 500, default 100). Readings return in observation order; hasMore shows that the limit truncated the result. Unknown or repeated parameters are rejected."),
  para("Demonstration identities match the other services. demo-gateway-001 is registered to farm-001 and demo-gateway-002 to farm-002; only gateways may submit. demo-owner-a owns farm-001 and demo-worker-a holds a grant on it, so both may read it; demo-owner-b owns farm-002."),
  table([1000, 3500, W - 4500], [["Status", "Code", "Relevant condition"],
    ["400", "INVALID_JSON", "Malformed UTF-8 JSON or literal NaN/Infinity"],
    ["401", "UNAUTHENTICATED", "Missing or invalid demonstration bearer identity"],
    ["403", "FORBIDDEN", "Non-gateway submits a reading, or a gateway tries to read"],
    ["404", "FARM_NOT_FOUND", "Farm absent, not accessible, or gateway not registered to it (identical bodies)"],
    ["404", "ROUTE_NOT_FOUND", "Unknown path or malformed farm identifier"],
    ["405", "METHOD_NOT_ALLOWED", "Unsupported method; Allow: GET, POST"],
    ["409", "READING_ID_CONFLICT", "readingId reused with different content"],
    ["413", "BODY_TOO_LARGE", "Body exceeds 65,536 bytes"],
    ["415", "UNSUPPORTED_MEDIA_TYPE", "Content-Type is not application/json"],
    ["422", "VALIDATION_ERROR", "Missing/extra fields, wrong unit, out-of-range value or invalid query parameter"],
    ["422", "UNSUPPORTED_SCHEMA_VERSION", "schemaVersion is not 1"]]),
  para([run("Error response example:", { bold: true })], { before: 120, after: 40 }),
  para([mono('{"error":{"code":"READING_ID_CONFLICT","message":"readingId sm-north-01-20261023T2045Z was already stored with different content."}}')]),

  h2("Where the endpoints sit in the architecture"),
  para("Both endpoints are served by the Telemetry container. In production, Farm Edge Gateways call POST over HTTPS with farm-bound machine credentials, and the Web and Mobile Apps call GET through the API Gateway. The REST Controller delegates to the Ingestion or Query Service, which authorises against Telemetry's own Farm Access Read Model rather than Farm Management's store and reads or writes the Telemetry Store through the Repository. Accepted readings leave the service only as ReadingAccepted events, consumed by Irrigation and Alerts and AI Recommendation, so Telemetry never waits for them."),

  h1("Repository integration"),
  para("As repository integrator, Aditya added a single start-up path and packaging for the whole team. The structure keeps one package per backend container from the Container Diagram, matching ADR-01."),
  table([3200, W - 3200], [["Item", "Purpose"],
    ["run_all.py", "Starts Farm Management (8001), Telemetry (8002) and Irrigation and Alerts (8003) in one terminal"],
    ["requirements.txt", "Records that the prototype needs only the Python 3.10+ standard library"],
    ["README.md", "Start-up, test, Postman and packaging instructions for all services"],
    ["scripts/package_submission.py", "Builds the clean code ZIP and re-runs all tests from the extracted copy"],
    ["tests/test_run_all.py", "Checks all three services start together and answer on their own ports"]]),

  h1("Validation evidence"),
  para("Fourteen HTTP integration tests start a real local server with a fixed clock and cover the exact POST contract, idempotent replay, 409 conflicts, spike and rainfall quarantine (including that quarantined readings are not published), gateway-only submission, foreign-gateway denial, schema and unit validation, rejected server-owned fields, schema versions, ordered and filtered retrieval, windows and limits, worker access, cross-owner denial, invalid query parameters, authentication, media type and method handling."),
  table([4800, W - 4800], [["Measure", "Observed result"],
    ["Automated tests (telemetry)", "14 passed, 0 failed"],
    ["Full repository suite", "49 passed, 0 failed"],
    ["Postman collection (Newman 6, fresh server)", "postman/Aditya_Telemetry.postman_collection.json: 19 requests, 59 of 59 assertions passed"],
    ["Combined run via run_all.py", "Farm 33/33, Telemetry 59/59 and Irrigation 40/40 assertions passed"],
    ["Clean ZIP check", "Extracted archive passed the full test suite"]]),
  para("The collection was executed with Newman, Postman's command-line runner, which executes the saved JavaScript assertions; the transcript is in docs/Aditya_Newman_Run.txt. Local results do not demonstrate production throughput, autoscaling, broker lag or 72-hour edge replay.", { before: 120 }),

  h1("References"),
  ...[
    "[1] Brown, S. (n.d.). Component diagram. C4 model. https://c4model.com/diagrams/component. Accessed 24 October 2026.",
    "[2] Brown, S. (n.d.). Dynamic diagram. C4 model. https://c4model.com/diagrams/dynamic. Accessed 24 October 2026.",
    "[3] Sharma, P., Singh, A., Wight, T., and Shears, B. (2026). OzAgriMate Software Architecture Proposal. Submitted ISYS3459 Assignment 2 report.",
    "[4] Sharma, P. (2026). OzAgriMate Architecture and Farm API; Team Integration Contract. ozagrimate-a4 repository.",
    "[5] RMIT University. (2026). ISYS3459 Assignment 4 Software Architecture Project activity instructions. Supplied course material.",
    "[6] RMIT University. (2026). ADR Template. Supplied course material.",
  ].map(t => para([run(t, { size: 19 })], { after: 60 })),
];

const PORTRAIT = { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } };
const LANDSCAPE = { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 700, bottom: 700, left: 1000, right: 1000 } };
const footer = () => new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run("Aditya Singh | page ", { size: 17 }), new TextRun({ children: [PageNumber.CURRENT], size: 17, font: "Calibri" })] })] });

const doc = new Document({
  creator: "Aditya Singh", title: "OzAgriMate Telemetry Architecture and API",
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  sections: [
    { properties: { page: PORTRAIT }, footers: { default: footer() }, children: body },
    { properties: { page: LANDSCAPE }, footers: { default: footer() }, children: runtime },
    { properties: { page: PORTRAIT }, footers: { default: footer() }, children: api },
  ],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("docs/Aditya_A4_Report_Section.docx", b); console.log("written"); });
