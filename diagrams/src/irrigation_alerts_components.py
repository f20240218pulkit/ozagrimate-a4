"""Irrigation and Alerts C4 Component Diagram (Bradley's view, redrawn to match the code).
Run: python3 diagrams/src/irrigation_alerts_components.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from drawlib import Canvas, BLUE, GREEN, GREY, BROWN, BOUNDARY

c = Canvas(2400, 2240)
c.text(40, 77, "OzAgriMate Irrigation and Alerts - C4 Component Diagram", 32, "bold", "start")
c.text(40, 107, "Components inside the Irrigation and Alerts container | solid = implemented module, dashed = proposed component", 19, "normal", "start")

W, H = 540, 170
X1, X2, X3 = 120, 930, 1740
cx1, cx2, cx3 = X1 + W / 2, X2 + W / 2, X3 + W / 2

# Neighbouring containers above the boundary
c.element(X1, 150, W, H, "Web App / Mobile App", "[Container: client applications]",
          ["Workers request irrigation; owners", "manage alert rules."], GREY)
c.element(X2, 150, W, H, "API Gateway", "[Container: managed HTTP gateway]",
          ["Routes /api/v1 requests; rate-limits", "and authenticates callers."], GREY)
c.element(X3, 150, W, H, "Identity and Access", "[Container: managed OAuth identity]",
          ["Issues and verifies access tokens."], GREY)

# Container boundary
c.rect(60, 390, 2280, 1270, BOUNDARY, "#9bb0c0")
c.text(115, 425, "Irrigation and Alerts [Container: backend service] - services/irrigation_alerts/ (port 8003)", 23, "bold", "start")

R1, R2, R3, R4 = 470, 780, 1090, 1400
c.element(X1, R1, W, H, "HTTP Server", "[Component: app.py]",
          ["Hosts local HTTP transport; wires", "controller, services and projection."])
c.element(X2, R1, W, H, "REST Controller", "[Component: api.py]",
          ["Routes irrigation-request and alert-", "rule endpoints; maps JSON errors."])
c.element(X3, R1, W, H, "Identity Adapter", "[Component: security.py]",
          ["Resolves the bearer token to a", "principal (demo fixtures locally)."])
c.element(X1, R2, W, H, "Irrigation Application Service", "[Component: irrigation_service.py]",
          ["Creates PENDING requests; replaces", "details only while PENDING."])
c.element(X2, R2, W, H, "Domain Model / Validator", "[Component: models.py]",
          ["Irrigation types and ADR-03 safe", "limits: 1-240 min, 0.5-50 mm."])
c.element(X3, R2, W, H, "Alert Rule Application Service", "[Component: alert_rule_service.py]",
          ["Owner-only rules (metric/unit checked);", "evaluates accepted readings."])
c.element(X1, R3, W, H, "Repository", "[Component: repository.py]",
          ["Stores irrigation requests in", "memory; scoped lookup by farm."])
c.element(X2, R3, W, H, "Farm Access Projection", "[Component: farm_projection.py]",
          ["Read-only farms and grants; ordered", "events, 60 s freshness (ADR-07)."])
c.element(X3, R3, W, H, "Alert Notification Publisher", "[Component: proposed - not implemented]",
          ["Raises and repeats alerts when", "accepted readings breach a rule."], BLUE, dashed=True)
c.element(X2, R4, W, H, "Farm Event Consumer", "[Component: farm_events.py - proposed]",
          ["Applies farm/grant events; local", "fixture source in the prototype."], BLUE, dashed=True)

# Data, messaging and external systems below the boundary
BY = 1740
c.element(X1, BY, W, H, "Operations Store", "[Container: managed database]",
          ["Service-owned requests, schedules,", "rules and farm/grant projection."], GREEN)
c.element(X2, BY, W, H, "Event Broker", "[Container: managed durable messaging]",
          ["Delivers farm/grant and accepted-", "reading events with replay."], GREEN)
c.element(X3, BY, W, H, "Notification Provider", "[External System]",
          ["Delivers SMS, voice, email or", "push alerts to farm users."], BROWN)

# Relationships: top
c.arrow([(X1 + W, 235), (X2, 235)]);                         c.label((X1 + W + X2) / 2, 222, ["Uses", "[HTTPS/REST]"])
c.arrow([(cx2, 320), (cx2, 360), (90, 360), (90, R1 + 40), (X1, R1 + 40)]); c.label((cx1 + cx2) / 2, 352, "Forwards irrigation and alert requests [JSON/HTTP]")
c.arrow([(cx3, R1), (cx3, 320)], dashed=True);                c.label(cx3, 362, "Validates tokens [production]")
# Inside: row 1
c.arrow([(X1 + W, R1 + 85), (X2, R1 + 85)]);                 c.label((X1 + W + X2) / 2, R1 + 72, ["Dispatches", "requests"])
c.arrow([(X2 + W, R1 + 85), (X3, R1 + 85)]);                 c.label((X2 + W + X3) / 2, R1 + 72, ["Authenticates", "caller"])
# Controller to the two application services
c.arrow([(cx2 - 120, R1 + H), (cx2 - 120, R1 + H + 45), (cx1, R1 + H + 45), (cx1, R2)])
c.label((cx1 + cx2 - 120) / 2, R1 + H + 38, "Irrigation create / replace")
c.arrow([(cx2 + 120, R1 + H), (cx2 + 120, R1 + H + 45), (cx3, R1 + H + 45), (cx3, R2)])
c.label((cx3 + cx2 + 120) / 2, R1 + H + 38, "Alert-rule create / delete")
# Row 2
c.arrow([(X1 + W, R2 + 85), (X2, R2 + 85)]);                 c.label((X1 + W + X2) / 2, R2 + 72, ["Validates", "input"])
# Services down
c.arrow([(cx1, R2 + H), (cx1, R3)]);                          c.label(cx1, R2 + H + 62, "Stores / loads requests")
c.arrow([(X1 + W, R2 + 145), (X1 + W + 70, R2 + 145), (X1 + W + 70, R3 + 85), (X2, R3 + 85)])
c.label((X1 + W + X2) / 2 + 35, R3 + 72, ["Checks farm", "access"])
c.arrow([(X3, R2 + 145), (X3 - 70, R2 + 145), (X3 - 70, R3 + 85), (X2 + W, R3 + 85)])
c.label((X2 + W + X3) / 2 - 35, R3 + 72, ["Checks owner", "access"])
c.arrow([(cx3 + 120, R2 + H), (cx3 + 120, R3)], dashed=True); c.label(cx3 + 120, R2 + H + 62, ["Requests notification", "[proposed]"])
# Accepted readings reach alert evaluation only through the Event Broker (no direct sensor ingestion)
c.arrow([(X2 + W, BY + 60), (X3 - 35, BY + 60), (X3 - 35, R3 - 45), (cx3 - 150, R3 - 45), (cx3 - 150, R2 + H)], dashed=True)
c.label(X3 - 35, BY - 230, ["Delivers accepted", "readings [proposed]"])
# Projection fed by consumer
c.arrow([(cx2, R4), (cx2, R3 + H)], dashed=True);              c.label(cx2, R3 + H + 62, "Applies events and snapshots")
# Down to stores / broker / provider
c.arrow([(cx1, R3 + H), (cx1, BY)]);                           c.label(cx1, R3 + H + 260, ["Reads / writes", "[in-memory dict in prototype]"])
c.arrow([(cx2, BY), (cx2, R4 + H)], dashed=True);              c.label(cx2, R4 + H + 45, "Delivers farm/grant events [proposed]")
c.arrow([(cx3, R3 + H), (cx3, BY)], dashed=True);              c.label(cx3, R3 + H + 260, ["Sends alerts", "[proposed; HTTPS]"])

# Legend
y = 2000
c.text(60, y, "Legend", 21, "bold", "start")
for i, (fill, dashed, name) in enumerate([(BLUE, False, "Implemented component (Python module)"),
                                          (BLUE, True, "Proposed component - not in the prototype"),
                                          (GREY, False, "Other container"),
                                          (GREEN, False, "Data store or messaging container")]):
    x = 60 + i * 570
    c.rect(x, y + 20, 60, 36, fill, dashed=dashed)
    c.text(x + 75, y + 46, name, 18, "normal", "start")
c.arrow([(60, y + 110), (160, y + 110)]); c.text(175, y + 116, "Implemented call", 18, "normal", "start")
c.arrow([(630, y + 110), (730, y + 110)], dashed=True); c.text(745, y + 116, "Proposed / production-only interaction", 18, "normal", "start")
c.rect(1200, y + 92, 60, 36, BROWN); c.text(1275, y + 116, "External system", 18, "normal", "start")
c.text(60, y + 175, "Prototype: one Python process at 127.0.0.1:8003 with demonstration identities; no broker, OAuth provider, database or notification provider is deployed.", 18, "italic", "start")

c.save(os.path.join(os.path.dirname(__file__), "..", "Irrigation_Alerts_Components"))
