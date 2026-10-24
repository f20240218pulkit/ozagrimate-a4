// Builds docs/Thomas_A4_Report_Section.docx. Run from repo root: node docs/build_thomas_report.js
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel,
  WidthType, ShadingType, PageOrientation, AlignmentType, BorderStyle, PageBreak, Footer, PageNumber,
} = require("docx");

const C = JSON.parse(fs.readFileSync("docs/thomas_report_content.json", "utf8"));
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

const POST_REQ = JSON.stringify({ paddockId: "north-paddock", scheduledStart: "2026-11-02T19:00:00Z", durationMinutes: 90, waterDepthMm: 18.5, notes: "Pre-heatwave watering" }, null, 1);
const POST_RES = JSON.stringify({ id: "irr-002", farmId: "farm-001", paddockId: "north-paddock", scheduledStart: "2026-11-02T19:00:00Z", durationMinutes: 90, waterDepthMm: 18.5, notes: "Pre-heatwave watering", status: "PENDING", requestedBy: "worker-a", version: 1 }, null, 1);
const PUT_REQ = JSON.stringify({ paddockId: "south-paddock", scheduledStart: "2026-11-03T18:30:00Z", durationMinutes: 60, waterDepthMm: 12 }, null, 1);
const PUT_RES = JSON.stringify({ id: "irr-002", farmId: "farm-001", paddockId: "south-paddock", scheduledStart: "2026-11-03T18:30:00Z", durationMinutes: 60, waterDepthMm: 12, notes: "", status: "PENDING", requestedBy: "worker-a", version: 2 }, null, 1);

function endpointTable(method, desc, url, req, res, status) {
  const w = [2200, W - 2200];
  const r = (k, v, code) => new TableRow({ children: [cell(k, w[0], { bold: true }), code ? codeCell(v, w[1]) : cell(v, w[1])] });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: w, rows: [
    new TableRow({ tableHeader: true, children: [cell("Specification", w[0], { head: true }), cell("Value", w[1], { head: true })] }),
    r("HTTP Method", method), r("Description", desc), r("Endpoint URL", url),
    r("Sample Request Body", req, true), r("Sample Response Body", res, true), r("Success status", status)] });
}

const body = [
  new Paragraph({ children: [run("OzAgriMate Irrigation Architecture and API", { size: 40, bold: true })], spacing: { after: 60 } }),
  para([run("Thomas Wight | ISYS3459 Assignment 4 | 24 October 2026", { size: 22, color: "486174" })], { after: 200 }),
  para("These sections document the architecture decisions, component and runtime views, and irrigation API contributed by Thomas Wight. The two irrigation endpoints pass 21 automated tests and a 13-request Postman replay. Architecture decisions remain Proposed pending team review."),

  h1("Design basis and scope"),
  para("The submitted Assignment 2 report lists Reliability / Safety and Availability among its seven driving characteristics. ASR5 requires suspicious readings not to trigger automated actions, ASR12 requires controllers to keep the last approved schedule for 48 hours offline, ASR19 requires access revocation within one minute and constraint C3 requires 72-hour offline edge operation. ADR-01 places irrigation in the Irrigation and Alerts service, which owns requests, approved schedules and alert rules in its own Operations Store partition."),
  para("This contribution implements only irrigation request creation and pending-request replacement. Owner approval, dispatch to the Farm Edge Gateway and physical execution are planned capabilities; the prototype never implies that water has been applied."),
  h2("Contribution coverage"),
  table([3000, W - 3000], [["Artefact", "Scope and status"],
    ["ADR-03", "Reliability / Safety with offline Availability; Proposed"],
    ["ADR-07", "Event-fed farm access projection (data/dependency decision); Proposed"],
    ["Farm Management component view", "Matches Pulkit's implemented modules; outbox publisher marked proposed"],
    ["Runtime view 2", "Irrigation request and processing; approval, dispatch and execution marked planned"],
    ["Irrigation API", "POST and PUT irrigation requests; local implementation on port 8003"],
    ["Testing evidence", "21 automated tests passed; 13 Postman requests replayed with expected results; user-run Postman screenshot pending"]]),

  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [run("ADR 03 Irrigation safety and offline continuity", { size: 30, bold: true })], spacing: { after: 120 } }),
  ...adr(C.adr03, "ASR5, ASR10, ASR12, ASR14, ASR21; constraint C3; Reliability / Safety and Availability driving QAs. Telemetry quarantine rules follow Aditya's ADR-02 and the team integration contract."),
  h1("ADR 07 Farm access projection"),
  ...adr(C.adr07, "ASR19, ASR26; ADR-01 service-owned stores; ADR-05 farm-scoped authorisation. Requires the Farm Management outbox shown as proposed in Figure 3."),

  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [run("Farm Management component view", { size: 30, bold: true })], spacing: { after: 120 } }),
  caption("Figure 3 OzAgriMate Farm Management C4 Component Diagram"),
  image("diagrams/Farm_Management_Components.png", 640),
  para("The view decomposes the Farm Management container into the modules Pulkit implemented, so the repository structure and diagram correspond one-to-one. The Farm Event Publisher is drawn dashed because the farm prototype does not yet publish events; it is required by ADR-07.", { before: 120 }),
  table([3000, 2200, W - 5200], [["Component", "Module", "Responsibility"],
    ["HTTP Server", "app.py", "Local HTTP transport and composition root"],
    ["Farm REST Controller", "api.py", "Routes the two farm endpoints; maps errors to the JSON envelope"],
    ["Identity Adapter", "security.py", "Resolves the bearer identity (demonstration fixtures locally)"],
    ["Farm Application Service", "service.py", "Owner-only creation and farm-scoped retrieval"],
    ["Farm Domain Model / Validator", "models.py", "Farm types and request validation"],
    ["Farm Repository", "repository.py", "In-memory storage with owner-scoped lookup"],
    ["Farm Event Publisher (Outbox)", "Proposed", "Publishes versioned farm and grant events after commit"]]),

];

const runtime = [
  h1("Runtime view: irrigation request and processing"),
  caption("Figure 4 OzAgriMate Runtime Diagram 2: irrigation request and processing (UML sequence)"),
  para([run("Interaction flow: ", { bold: true }), run(C.runtime_explanation)], { after: 60 }),
  image("diagrams/Irrigation_Runtime.png", 700),
];

const api = [
  h1("Irrigation API design"),
  para("Paths follow the team integration contract. Production versioning is proposed as /api/v1 at the gateway; the prototype exposes the unprefixed service paths at http://127.0.0.1:8003."),
  h2("POST /farms/{farmId}/irrigation-requests"),
  endpointTable("POST", "Create a pending irrigation request for a farm paddock", "/farms/{farmId}/irrigation-requests", POST_REQ, POST_RES, "201 Created, with a Location header"),
  h2("PUT /farms/{farmId}/irrigation-requests/{requestId}"),
  endpointTable("PUT", "Replace a pending irrigation request's editable details", "/farms/{farmId}/irrigation-requests/{requestId}", PUT_REQ, PUT_RES, "200 OK"),
  para("The irr-002 example assumes the first creation after server startup; irr-001 is a seeded APPROVED request used to demonstrate the lifecycle conflict. Consumers should use the returned ID. PUT is a full replacement: an omitted notes field becomes empty, and the version increases by one.", { before: 120 }),

  h2("Validation and error behaviour"),
  para("A body must contain paddockId, scheduledStart, durationMinutes and waterDepthMm; notes is optional. Any other field, including caller-supplied id, status, requestedBy or owner fields, is rejected. paddockId is 1 to 60 lowercase letters, digits or hyphens. scheduledStart is a valid UTC timestamp such as 2026-11-02T19:00:00Z. The ADR-03 safe limits apply: durationMinutes is a whole number from 1 to 240 and waterDepthMm is a number from 0.5 to 50. notes is at most 500 characters. Booleans, nulls and numeric strings are rejected."),
  para("Demonstration identities match Farm Management. demo-owner-a owns farm-001 and demo-worker-a holds an operations grant on it, so both may create and replace requests there. demo-owner-b owns farm-002 and cannot see farm-001. farm-003 belongs to owner A but its event source is deliberately stalled to demonstrate the ADR-07 freshness rule."),
  table([1000, 3500, W - 4500], [["Status", "Code", "Relevant condition"],
    ["400", "INVALID_JSON", "Malformed UTF-8 JSON or literal NaN/Infinity"],
    ["401", "UNAUTHENTICATED", "Missing or invalid demonstration bearer identity"],
    ["404", "FARM_NOT_FOUND", "Farm absent or not accessible to the caller (identical bodies)"],
    ["404", "IRRIGATION_REQUEST_NOT_FOUND", "Request absent or belongs to another farm"],
    ["404", "ROUTE_NOT_FOUND", "Unknown path or malformed identifier"],
    ["405", "METHOD_NOT_ALLOWED", "Unsupported method; Allow header names the supported one"],
    ["409", "REQUEST_NOT_EDITABLE", "PUT on a request that is no longer PENDING"],
    ["413", "BODY_TOO_LARGE", "Body exceeds 65,536 bytes"],
    ["415", "UNSUPPORTED_MEDIA_TYPE", "Content-Type is not application/json"],
    ["422", "VALIDATION_ERROR", "Missing/extra fields, invalid values or safe limits exceeded"],
    ["503", "FARM_ACCESS_STALE", "Farm access cannot be confirmed within 60 seconds; Retry-After: 5"]]),
  para([run("Error response example:", { bold: true })], { before: 120, after: 40 }),
  para([mono('{"error":{"code":"REQUEST_NOT_EDITABLE","message":"Only PENDING requests can be replaced; this request is APPROVED."}}')]),

  h2("Where the endpoints sit in the architecture"),
  para("Both endpoints are served by the Irrigation and Alerts container. In production, the Web or Mobile App calls the API Gateway, which routes them to this service. The REST Controller delegates to the Irrigation Application Service, which checks the Farm Access Projection rather than Farm Management's store, validates ADR-03 limits and persists through the Repository to the service's Operations Store partition. No AI Recommendation dependency exists, so irrigation requests continue during AI outages (ASR21)."),

  h1("Repository and component alignment"),
  para("The code lives in services/irrigation_alerts/, matching the module names agreed with Bradley for the Irrigation and Alerts component view."),
  table([3200, 2900, W - 6100], [["Component", "Module", "Status"],
    ["REST Controller (shared routing)", "api.py", "Implemented; irrigation routes"],
    ["Irrigation Application Service", "irrigation_service.py", "Implemented (Thomas)"],
    ["Alert Rule Application Service", "alert_rule_service.py", "Placeholder (Bradley)"],
    ["Farm Access Projection", "farm_projection.py", "Implemented; ADR-07 rules"],
    ["Repository", "repository.py", "Implemented; in-memory"],
    ["Domain Model / Validator", "models.py", "Implemented; ADR-03 limits"],
    ["Identity Adapter", "security.py", "Implemented; demonstration identities"],
    ["Farm Event Consumer", "farm_events.py", "Proposed; local fixture source only"],
    ["HTTP Server", "app.py", "Composition root, port 8003"]]),

  h1("Validation evidence"),
  para("Twenty-one automated tests run against the code. Fifteen HTTP integration tests start a real local server and cover the exact create and replace contracts, owner and worker access, cross-owner denial, the stale-projection 503, rejected caller-supplied fields, safe-limit boundaries, partial PUT bodies, the 409 lifecycle conflict, missing requests, authentication, media type and method handling. Six unit tests cover ADR-07 projection rules: revocation, duplicate events, out-of-order replay, version gaps and watermark expiry. The full repository suite, including Pulkit's ten farm tests, passed 31 of 31."),
  table([4800, W - 4800], [["Measure", "Observed result"],
    ["Automated tests (irrigation)", "21 passed, 0 failed"],
    ["Full repository suite", "31 passed, 0 failed"],
    ["Postman collection", "postman/Thomas_Irrigation.postman_collection.json, 13 requests, 40 assertions"],
    ["Request replay against running service", "13 of 13 returned the expected status and error code"],
    ["User-run Postman screenshot", "Pending; to be added before submission"]]),
  para("The request replay was produced by a script that sends each saved collection request and checks its status and error code; it does not execute Postman's JavaScript assertions. The official Postman run will replace it as primary evidence. Local results do not demonstrate production durability, broker latency, one-minute revocation or offline controller behaviour.", { before: 120 }),

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
const footer = () => new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run("Thomas Wight | page ", { size: 17 }), new TextRun({ children: [PageNumber.CURRENT], size: 17, font: "Calibri" })] })] });

const doc = new Document({
  creator: "Thomas Wight", title: "OzAgriMate Irrigation Architecture and API",
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  sections: [
    { properties: { page: PORTRAIT }, footers: { default: footer() }, children: body },
    { properties: { page: LANDSCAPE }, footers: { default: footer() }, children: runtime },
    { properties: { page: PORTRAIT }, footers: { default: footer() }, children: api },
  ],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("docs/Thomas_A4_Report_Section.docx", b); console.log("written"); });
