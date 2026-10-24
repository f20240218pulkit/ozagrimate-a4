"""Runtime Diagram 1: telemetry submission and processing (UML sequence). Run: python3 diagrams/src/telemetry_runtime.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from drawlib import Canvas, BLUE, GREY, BROWN, PLANNED, LINE, INK, BORDER

PARTS = [  # title lines, tag, description, fill
    (["Soil Moisture", "Sensor"], "[External System]", "Measures conditions", BROWN),
    (["Farm Edge", "Gateway"], "[Container: target]", "Not in prototype", GREY),
    (["REST Controller"], "[Component: api.py]", "Routes; maps errors", BLUE),
    (["Telemetry", "Ingestion Service"], "[ingestion_service.py]", "Ingestion use case", BLUE),
    (["Farm Access", "Read Model"], "[farm_access.py]", "Gateway bindings", BLUE),
    (["Anomaly Detector"], "[anomaly_detector.py]", "Accept or quarantine", BLUE),
    (["Repository"], "[Component: repository.py]", "Per-farm readings", BLUE),
    (["Accepted Reading", "Publisher"], "[event_publisher.py]", "Outbox", BLUE),
    (["Event Broker"], "[Container: target]", "Not in prototype", GREY),
    (["Irrigation", "and Alerts"], "[Container]", "Consumes events", GREY),
]
STEP, X0, BW, BH, TOP = 285, 170, 268, 160, 150
xs = [X0 + i * STEP for i in range(len(PARTS))]
W = xs[-1] + 190
H = 2600
c = Canvas(W, H)
c.text(40, 77, "OzAgriMate Runtime Diagram 1 - Telemetry submission and processing (UML sequence)", 36, "bold", "start")
c.text(40, 110, "Telemetry container | prototype implements steps 4-16 and the idempotent replay (19-21); dashed boxes are target containers; amber steps are planned", 22, "normal", "start")

# Section backgrounds are drawn first so lifelines sit on top of them.
SECTIONS = []
y = TOP + BH + 70
ROW = 64


def section(title, n_rows, fill, dashed=False):
    global y
    top = y
    height = 60 + n_rows * ROW + 10
    SECTIONS.append((top, height, title, fill, dashed))
    y += 60
    start = y
    y = top + height + 24
    return start


rows_a = section("Submit - implemented: POST /farms/{farmId}/telemetry", 16, "#f7fafc")
rows_b = section("opt [uplink outage] - edge buffering planned; idempotent replay implemented", 5, "#f7fafc")
rows_c = section("async, PLANNED - broker relay and consumption; the prototype keeps an in-memory outbox", 3, PLANNED, True)
for top, height, title, fill, dashed in SECTIONS:
    c.rect(40, top, W - 80, height, fill, "#9bb0c0" if not dashed else "#b08a3c", 2, dashed)
    c.text(56, top + 32, title, 23, "bold", "start", "#7a5a17" if dashed else INK)

LIFE_END = y + 10
for x, (title, tag, desc, fill) in zip(xs, PARTS):
    c.arrow([(x, TOP + BH), (x, LIFE_END)], color="#9bb0c0", width=2, dashed=True, head=False)
for x, (title, tag, desc, fill) in zip(xs, PARTS):
    c.rect(x - BW / 2, TOP, BW, BH, fill, dashed="target" in tag)
    ty = TOP + 32
    for line in title:
        c.text(x, ty, line, 23, "bold")
        ty += 27
    c.text(x, ty + 2, tag, 17)
    c.text(x, ty + 30, desc, 19, "italic")


def msg(row_y, a, b, text, kind="call", planned=False):
    color = "#9a6b12" if planned else LINE
    if a == b:  # self call
        x = xs[a]
        d = -1 if a == len(xs) - 1 else 1
        c.arrow([(x, row_y - 10), (x + 55 * d, row_y - 10), (x + 55 * d, row_y + 18), (x + 4 * d, row_y + 18)],
                color=color, dashed=planned)
        c.label(x + 66 * d, row_y + 9, text, 21, anchor="start" if d > 0 else "end")
        return
    x1, x2 = xs[a], xs[b]
    ret = kind == "return"
    c.arrow([(x1, row_y), (x2 - (4 if x2 > x1 else -4), row_y)], color=color, dashed=ret or planned, open_head=ret)
    c.label((x1 + x2) / 2, row_y - 14, text, 21)


A = [(0, 1, "1. Soil moisture 29.7 % [field protocol]", "call", True),
     (1, 1, "2. Normalise to schema v1; assign readingId", "call", True),
     (1, 2, "3. POST /farms/farm-001/telemetry + gateway token", "call", True),
     (2, 3, "4. submit(principal, farmId, body)"),
     (3, 4, "5. Gateway registered to farm?"),
     (4, 3, "6. Yes [else 403 / 404]", "return"),
     (3, 3, "7. Validate unit, range, UTC time [else 422]"),
     (3, 6, "8. find(farmId, readingId) - replay check"),
     (6, 3, "9. Not found [same: 200 | different: 409]", "return"),
     (3, 5, "10. classify(reading)"),
     (5, 6, "11. Last accepted value for this device"),
     (5, 3, "12. ACCEPTED | QUARANTINED + reasons", "return"),
     (3, 6, "13. Store reading with status"),
     (3, 7, "14. publish(reading) - ACCEPTED only"),
     (3, 2, "15. Stored reading", "return"),
     (2, 1, "16. 201 Created (status, reasons)", "return")]
B = [(1, 1, "17. Hold readings up to 72 h while offline", "call", True),
     (1, 2, "18. Resend same readingId after reconnect", "call", True),
     (2, 3, "19. submit(): same readingId, same content"),
     (3, 2, "20. Original record [not stored or published again]", "return"),
     (2, 1, "21. 200 OK + original record", "return")]
C = [(7, 8, "22. Relay ReadingAccepted, key = farmId", "call", True),
     (8, 9, "23. Deliver at least once", "call", True),
     (9, 9, "24. Skip seen eventId; evaluate alert rules", "call", True)]

for start, rows in [(rows_a, A), (rows_b, B), (rows_c, C)]:
    ry = start + 24
    for r in rows:
        msg(ry, r[0], r[1], r[2], r[3] if len(r) > 3 else "call", r[4] if len(r) > 4 else False)
        ry += ROW + (24 if r[0] == r[1] else 0)

# Notes and legend
ny = LIFE_END + 50
c.text(40, ny, "Quarantined readings (step 12) are stored with reason codes but never published, so they cannot trigger irrigation or alerts (ASR5).", 21, "italic", "start")
c.text(40, ny + 34, "The gateway receives 201 once the reading is stored; downstream processing is asynchronous and scales separately (ADR-02).", 21, "italic", "start")
c.text(40, ny + 68, "Prototype: no edge gateway or broker. Postman calls the REST Controller directly at 127.0.0.1:8002, standing in for steps 3, 16, 18 and 21.", 21, "italic", "start")
ly = ny + 130
c.arrow([(40, ly), (160, ly)]); c.text(175, ly + 6, "Synchronous call", 21, "normal", "start")
c.arrow([(470, ly), (590, ly)], dashed=True, open_head=True); c.text(605, ly + 6, "Return", 21, "normal", "start")
c.arrow([(820, ly), (940, ly)], color="#9a6b12", dashed=True); c.text(955, ly + 6, "Planned interaction (not implemented)", 21, "normal", "start")
c.rect(1520, ly - 18, 50, 32, BLUE); c.text(1585, ly + 6, "Telemetry component", 21, "normal", "start")
c.rect(1990, ly - 18, 50, 32, GREY); c.text(2055, ly + 6, "Person / other container", 21, "normal", "start")
c.rect(2420, ly - 18, 50, 32, GREY, dashed=True); c.text(2485, ly + 6, "Target container (not in prototype)", 21, "normal", "start")

# Crop canvas height to content
final_h = int(ly + 60)
c.img = c.img.crop((0, 0, W, final_h))
c.svg[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{final_h}" viewBox="0 0 {W} {final_h}">'
c.save(os.path.join(os.path.dirname(__file__), "..", "Telemetry_Runtime"))
