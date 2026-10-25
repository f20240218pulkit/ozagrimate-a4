"""OzAgriMate C4 System Context Diagram (Bradley's view, redrawn).
Run: python3 diagrams/src/system_context.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from drawlib import Canvas, BLUE, GREY, BROWN

c = Canvas(2400, 1720)
c.text(40, 77, "OzAgriMate - C4 System Context Diagram", 32, "bold", "start")
c.text(40, 107, "People and external systems around the OzAgriMate Platform | dashed = proposed extension outside the core prototype", 19, "normal", "start")

# People (match the container view)
PEOPLE = [("Farm Owner", ["Owns farms; controls sharing,", "consent and approvals."]),
          ("Farm Worker", ["Logs observations and", "requests irrigation."]),
          ("Agronomist", ["Reviews granted farms;", "advises or overrides advice."]),
          ("Operations Manager", ["Monitors KPIs across", "authorised farms."]),
          ("Platform Administrator", ["Configures tenants, roles", "and integrations."])]
PW, PH, PY = 420, 170, 150
pxs = [40 + i * 470 for i in range(5)]
for x, (name, desc) in zip(pxs, PEOPLE):
    c.element(x, PY, PW, PH, name, "[Person]", desc, GREY)

# The system
SX, SY, SW, SH = 900, 640, 600, 700
c.rect(SX, SY, SW, SH, "#1f4e79", "#183047", 3)
cx = SX + SW / 2
c.text(cx, SY + 300, "OzAgriMate Platform", 30, "bold", fill="#ffffff")
c.text(cx, SY + 335, "[Software System]", 19, fill="#ffffff")
for i, line in enumerate(["IoT farm monitoring, irrigation", "management, alerts and AI-assisted",
                          "decision support for Australian farms."]):
    c.text(cx, SY + 380 + i * 28, line, 20, fill="#ffffff")

# People use the platform (diagonals to spread points on the system's top edge)
USES = ["Manages farms, access and approvals", "Logs observations; requests irrigation",
        "Reviews data; advises", "Monitors authorised farms", "Administers tenants and integrations"]
tops = [SX + 70 + i * 115 for i in range(5)]
for i, (x, label) in enumerate(zip(pxs, USES)):
    start = (x + PW / 2, PY + PH)
    c.arrow([start, (tops[i], SY)], width=3)
    mx, my = (start[0] + tops[i]) / 2, (start[1] + SY) / 2 + (i % 2) * 46 - 10
    c.label(mx, my, [label, "[Web / Mobile App]"], 16)

# External systems: left column (data in, commands out), right column (exchanges and outputs)
EW, EH = 500, 170
LX, RX = 40, 1860
EY = [640, 820, 1000, 1180]
LEFT = [("IoT Sensors & Farm Machinery", "[External Systems: ISOBUS / ADAPT]",
         ["Field sensors, controllers and", "machinery on each farm."], False),
        ("Bureau of Meteorology API", "[External System]",
         ["Weather forecasts, radar and", "severe-weather warnings."], False),
        ("State Biosecurity Alert Feeds", "[External System]",
         ["Regional pest and disease", "outbreak notices."], False),
        ("Commodity / Market Price Feeds", "[External System]",
         ["Live commodity and agricultural", "market prices."], False)]
RIGHT = [("Legacy FMIS", "[External System]",
          ["Farm management information", "systems holding historical records."], False),
         ("SMS / Push Notification Gateway", "[External System]",
          ["Delivers critical alerts by SMS,", "voice, email and push."], False),
         ("Third-Party Agri-Tech Apps", "[External Systems]",
          ["Consume and publish data via", "OzAgriMate's open API."], False),
         ("Agri-Finance & Insurance Partners", "[External Systems - extension]",
          ["Receive farmer-consented yield", "and compliance data."], True)]
for y, (name, tag, desc, dashed) in zip(EY, LEFT):
    c.element(LX, y, EW, EH, name, tag, desc, BROWN, dashed=dashed)
for y, (name, tag, desc, dashed) in zip(EY, RIGHT):
    c.element(RX, y, EW, EH, name, tag, desc, BROWN, dashed=dashed)

L_EDGE, R_EDGE = LX + EW, RX
gap_mid_l, gap_mid_r = (L_EDGE + SX) / 2, (SX + SW + R_EDGE) / 2


def into_system(y, label, dashed=False):        # left external -> system
    c.arrow([(L_EDGE, y), (SX, y)], dashed=dashed)
    c.label(gap_mid_l, y - 12, label, 16)


def out_of_system_left(y, label):              # system -> left external
    c.arrow([(SX, y), (L_EDGE, y)])
    c.label(gap_mid_l, y - 12, label, 16)


def right(y, label, outward=True, dashed=False):
    pts = [(SX + SW, y), (R_EDGE, y)] if outward else [(R_EDGE, y), (SX + SW, y)]
    c.arrow(pts, dashed=dashed)
    c.label(gap_mid_r, y - 12, label, 16)


# Left: incoming telemetry split from outgoing approved commands
into_system(EY[0] + 55, ["Sends soil, climate and machinery", "telemetry [via farm edge gateway]"])
out_of_system_left(EY[0] + 135, ["Sends approved irrigation schedules", "[authenticated edge channel]"])
into_system(EY[1] + 95, ["Supplies forecasts and warnings", "[HTTPS / JSON]"])
into_system(EY[2] + 95, ["Publishes outbreak notices", "[HTTPS feed]"])
into_system(EY[3] + 95, ["Supplies market prices", "[HTTPS feed]"])
# Right
right(EY[0] + 55, ["Imports historical farm records", "[file / API transfer]"], outward=False)
right(EY[0] + 135, ["Exports consented farm records", "[file / API transfer]"])
right(EY[1] + 95, ["Sends critical alert requests", "[HTTPS]"])
right(EY[2] + 95, ["Read and publish data", "[Open REST API]"], outward=False)
right(EY[3] + 95, ["Shares consented yield data", "[proposed extension]"], dashed=True)

# Legend and notes
y = 1430
c.text(40, y, "Legend", 21, "bold", "start")
items = [("#1f4e79", False, "Software system in scope"), (GREY, False, "Person"),
         (BROWN, False, "External system"), (BROWN, True, "Proposed extension (outside prototype)")]
for i, (fill, dashed, name) in enumerate(items):
    x = 40 + i * 560
    c.rect(x, y + 20, 60, 36, fill, dashed=dashed)
    c.text(x + 75, y + 46, name, 18, "normal", "start")
c.arrow([(40, y + 110), (140, y + 110)]); c.text(155, y + 116, "Interaction; arrow shows direction of the main data flow", 18, "normal", "start")
c.arrow([(900, y + 110), (1000, y + 110)], dashed=True); c.text(1015, y + 116, "Proposed extension interaction", 18, "normal", "start")
c.text(40, y + 175, "Carbon verification, drone micro-dosing and trade execution are bounded extensions from Assignment 2; they are not part of the eight-endpoint prototype.", 18, "italic", "start")
c.text(40, y + 205, "Field equipment connects through the Farm Edge Gateway shown in the container view; ISOBUS, ADAPT, LoRaWAN and NB-IoT are adapted there.", 18, "italic", "start")

c.save(os.path.join(os.path.dirname(__file__), "..", "System_Context"))
