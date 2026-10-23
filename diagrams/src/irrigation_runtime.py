"""Runtime Diagram 2: irrigation request and processing (UML sequence). Run: python3 diagrams/src/irrigation_runtime.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from drawlib import Canvas, BLUE, GREY, BROWN, PLANNED, LINE, INK, BORDER

PARTS = [  # title lines, tag, description, fill
    (["Farm Worker"], "[Person]", "Requests watering", GREY),
    (["Mobile App"], "[Container]", "Offline field client", GREY),
    (["API Gateway"], "[Container]", "Routes REST calls", GREY),
    (["REST Controller"], "[Component: api.py]", "Parses; maps errors", BLUE),
    (["Irrigation", "Application Service"], "[irrigation_service.py]", "Request lifecycle", BLUE),
    (["Farm Access", "Projection"], "[farm_projection.py]", "Fresh farm grants", BLUE),
    (["Repository"], "[Component: repository.py]", "Stores requests", BLUE),
    (["Farm Owner"], "[Person]", "Approves requests", GREY),
    (["Farm Edge Gateway"], "[Container: edge]", "Delivers schedules", GREY),
    (["Irrigation", "Controller"], "[External System]", "Executes locally", BROWN),
]
STEP, X0, BW, BH, TOP = 270, 170, 250, 150, 150
xs = [X0 + i * STEP for i in range(len(PARTS))]
W = xs[-1] + 190
H = 2200
c = Canvas(W, H)
c.text(40, 77, "OzAgriMate Runtime Diagram 2 - Irrigation request and processing (UML sequence)", 32, "bold", "start")
c.text(40, 107, "Irrigation and Alerts container | steps 1-17 are implemented by POST and PUT; steps 18-22 are planned capabilities", 19, "normal", "start")

# Section backgrounds are drawn first so lifelines sit on top of them.
SECTIONS = []
y = TOP + BH + 70
ROW = 58


def section(title, n_rows, fill, dashed=False):
    global y
    top = y
    height = 46 + n_rows * ROW + 10
    SECTIONS.append((top, height, title, fill, dashed))
    y += 46
    start = y
    y = top + height + 24
    return start


rows_a = section("Create - implemented: POST /farms/{farmId}/irrigation-requests", 11, "#f7fafc")
rows_b = section("opt [request is still PENDING] - implemented: PUT /farms/{farmId}/irrigation-requests/{requestId}", 6, "#f7fafc")
rows_c = section("PLANNED - outside the two implemented endpoints; the prototype never applies water", 6, PLANNED, True)
for top, height, title, fill, dashed in SECTIONS:
    c.rect(40, top, W - 80, height, fill, "#9bb0c0" if not dashed else "#b08a3c", 2, dashed)
    c.text(56, top + 30, title, 19, "bold", "start", "#7a5a17" if dashed else INK)

LIFE_END = y + 10
for x, (title, tag, desc, fill) in zip(xs, PARTS):
    c.arrow([(x, TOP + BH), (x, LIFE_END)], color="#9bb0c0", width=2, dashed=True, head=False)
for x, (title, tag, desc, fill) in zip(xs, PARTS):
    c.rect(x - BW / 2, TOP, BW, BH, fill)
    ty = TOP + 32
    for line in title:
        c.text(x, ty, line, 20, "bold")
        ty += 25
    c.text(x, ty + 2, tag, 15)
    c.text(x, ty + 30, desc, 16, "italic")


def msg(row_y, a, b, text, kind="call", planned=False):
    color = "#9a6b12" if planned else LINE
    if a == b:  # self call
        x = xs[a]
        d = -1 if a == len(xs) - 1 else 1
        c.arrow([(x, row_y - 10), (x + 55 * d, row_y - 10), (x + 55 * d, row_y + 18), (x + 4 * d, row_y + 18)],
                color=color, dashed=planned)
        c.label(x + 66 * d, row_y + 9, text, 16, anchor="start" if d > 0 else "end")
        return
    x1, x2 = xs[a], xs[b]
    ret = kind == "return"
    c.arrow([(x1, row_y), (x2 - (4 if x2 > x1 else -4), row_y)], color=color, dashed=ret or planned, open_head=ret)
    c.label((x1 + x2) / 2, row_y - 13, text, 16)


A = [(0, 1, "1. Enters paddock, start, minutes, mm"),
     (1, 2, "2. POST /farms/farm-001/irrigation-requests"),
     (2, 3, "3. Forwards request + bearer token"),
     (3, 4, "4. create(principal, farmId, body)"),
     (4, 5, "5. Owner/grant? Fresh within 60 s?"),
     (5, 4, "6. Allowed [else 404 / 503]", "return"),
     (4, 4, "7. Check safe limits: 1-240 min, 0.5-50 mm [else 422]"),
     (4, 6, "8. Store as PENDING"),
     (6, 4, "9. irr-002, version 1", "return"),
     (3, 2, "10. 201 Created + Location", "return"),
     (2, 1, "11. 201 Created (status PENDING)", "return")]
B = [(1, 2, "12. PUT .../irr-002 (full replacement)"),
     (2, 3, "13. Forwards request + token"),
     (3, 4, "14. replace(): authorise + validate"),
     (4, 6, "15. Save only if PENDING (version 2)"),
     (3, 2, "16. 200 OK | 409 REQUEST_NOT_EDITABLE", "return"),
     (2, 1, "17. Returns result to worker", "return")]
C = [(7, 4, "18. Approves irr-002 [via Web App]"),
     (4, 4, "19. Re-check limits; set expiry"),
     (4, 8, "20. Dispatch approved schedule + expiry [via Event Broker]"),
     (8, 9, "21. Install; 48 h offline lease"),
     (9, 9, "22. Run within local limits; stop at expiry")]

for start, rows, planned in [(rows_a, A, False), (rows_b, B, False), (rows_c, C, True)]:
    ry = start + 24
    for r in rows:
        msg(ry, r[0], r[1], r[2], r[3] if len(r) > 3 else "call", planned)
        ry += ROW + (22 if r[0] == r[1] else 0)

# Notes and legend
ny = LIFE_END + 50
c.text(40, ny, "Safe state: after 48 hours without cloud contact the controller stops automatic watering and reverts to manual control.", 18, "italic", "start")
c.text(40, ny + 30, "A disconnected controller cannot receive cloud cancellations; schedule expiry and local overrides are the safeguard (ADR-03).", 18, "italic", "start")
ly = ny + 85
c.arrow([(40, ly), (160, ly)]); c.text(175, ly + 6, "Synchronous call", 18, "normal", "start")
c.arrow([(470, ly), (590, ly)], dashed=True, open_head=True); c.text(605, ly + 6, "Return", 18, "normal", "start")
c.arrow([(820, ly), (940, ly)], color="#9a6b12", dashed=True); c.text(955, ly + 6, "Planned interaction (not implemented)", 18, "normal", "start")
c.rect(1440, ly - 18, 50, 32, BLUE); c.text(1505, ly + 6, "Irrigation and Alerts component", 18, "normal", "start")
c.rect(1880, ly - 18, 50, 32, GREY); c.text(1945, ly + 6, "Person / other container", 18, "normal", "start")

# Crop canvas height to content
final_h = int(ly + 60)
c.img = c.img.crop((0, 0, W, final_h))
c.svg[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{final_h}" viewBox="0 0 {W} {final_h}">'
c.save(os.path.join(os.path.dirname(__file__), "..", "Irrigation_Runtime"))
