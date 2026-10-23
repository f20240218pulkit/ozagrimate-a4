"""Farm Management C4 Component Diagram (Thomas). Run: python3 diagrams/src/farm_management_components.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from drawlib import Canvas, BLUE, GREEN, GREY, BOUNDARY, LINE, INK

c = Canvas(2400, 2040)
c.text(40, 77, "OzAgriMate Farm Management - C4 Component Diagram", 32, "bold", "start")
c.text(40, 107, "Components inside the Farm Management container | solid = implemented module, dashed = proposed component", 19, "normal", "start")

W, H = 540, 170
X1, X2, X3 = 120, 930, 1740

# Neighbouring containers (outside the boundary)
c.element(X1, 150, W, H, "Web App / Mobile App", "[Container: client applications]",
          ["Farm owners create and view farms."], GREY)
c.element(X2, 150, W, H, "API Gateway", "[Container: managed HTTP gateway]",
          ["Routes /api/v1 requests; rate-limits", "and authenticates callers."], GREY)
c.element(X3, 150, W, H, "Identity and Access", "[Container: managed OAuth + grants]",
          ["Issues and verifies access tokens."], GREY)

# Container boundary
c.rect(60, 390, 2280, 960, BOUNDARY, "#9bb0c0")
c.text(80, 425, "Farm Management [Container: backend service] - services/farm_management/", 23, "bold", "start")

R1, R2, R3 = 470, 780, 1090
c.element(X1, R1, W, H, "HTTP Server", "[Component: app.py]",
          ["Hosts local HTTP transport; wires", "controller, service and repository."])
c.element(X2, R1, W, H, "Farm REST Controller", "[Component: api.py]",
          ["Routes POST /farms and GET /farms/{id};", "maps errors to the JSON envelope."])
c.element(X3, R1, W, H, "Identity Adapter", "[Component: security.py]",
          ["Resolves the bearer token to a", "principal (demo fixtures locally)."])
c.element(X1, R2, W, H, "Farm Domain Model / Validator", "[Component: models.py]",
          ["Defines farm types; validates name,", "coordinates and area."])
c.element(X2, R2, W, H, "Farm Application Service", "[Component: service.py]",
          ["Applies owner-only creation and", "farm-scoped retrieval rules."])
c.element(X3, R2, W, H, "Farm Event Publisher (Outbox)", "[Component: proposed - not implemented]",
          ["Publishes versioned farm and grant", "events after each committed change."], BLUE, dashed=True)
c.element(X2, R3, W, H, "Farm Repository", "[Component: repository.py]",
          ["Creates farms; looks them up only", "within the caller's owner scope."])

# Data and messaging containers
c.element(X2, 1430, W, H, "Farm Store", "[Container: managed database]",
          ["Farm records and grants; owned", "by Farm Management only."], GREEN)
c.element(X3, 1430, W, H, "Event Broker", "[Container: managed durable messaging]",
          ["Durable, ordered-per-farm delivery", "with replay for recovery."], GREEN)
c.element(X1, 1430, W, H, "Irrigation and Alerts", "[Container: backend service]",
          ["Keeps its own read-only farm", "access projection (ADR-07)."], GREY)

# Relationships
cx1, cx2, cx3 = X1 + W / 2, X2 + W / 2, X3 + W / 2
c.arrow([(X1 + W, 235), (X2, 235)]);                       c.label((X1 + W + X2) / 2, 222, ["Uses", "[HTTPS/REST]"], anchor="middle")
c.arrow([(cx2, 320), (cx2, 360), (cx1, 360), (cx1, R1)]);   c.label((cx1 + cx2) / 2, 352, "Forwards /farms requests [JSON/HTTP]")
c.arrow([(X1 + W, R1 + 85), (X2, R1 + 85)]);               c.label((X1 + W + X2) / 2, R1 + 72, ["Dispatches", "requests"])
c.arrow([(X2 + W, R1 + 85), (X3, R1 + 85)]);               c.label((X2 + W + X3) / 2, R1 + 72, ["Authenticates", "caller"])
c.arrow([(cx3, R1), (cx3, 320)], dashed=True);              c.label(cx3, 362, "Validates tokens [production]")
c.arrow([(cx2, R1 + H), (cx2, R2)]);                        c.label(cx2, R1 + H + 52, "Invokes create / get")
c.arrow([(X2, R2 + 85), (X1 + W, R2 + 85)]);               c.label((X1 + W + X2) / 2, R2 + 72, ["Validates", "input"])
c.arrow([(X2 + W, R2 + 85), (X3, R2 + 85)], dashed=True);  c.label((X2 + W + X3) / 2, R2 + 72, ["Records change", "[proposed]"])
c.arrow([(cx2, R2 + H), (cx2, R3)]);                        c.label(cx2, R2 + H + 52, "Scoped create / lookup")
c.arrow([(cx2, R3 + H), (cx2, 1430)]);                      c.label(cx2, R3 + H + 62, ["Reads / writes farm records", "[in-memory dict in prototype]"])
c.arrow([(cx3, R2 + H), (cx3, 1430)], dashed=True);         c.label(cx3, 1160, ["Publishes farm/grant", "events [proposed]"])
c.arrow([(cx3, 1600), (cx3, 1650), (cx1, 1650), (cx1, 1600)], dashed=True); c.label((cx1 + cx3) / 2, 1657, "Delivers farm/grant events [proposed]")

# Legend
y = 1760
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
c.text(60, y + 175, "Prototype: one Python process at 127.0.0.1:8001 with demonstration identities; no broker, OAuth provider or database is deployed.", 18, "italic", "start")

c.save(os.path.join(os.path.dirname(__file__), "..", "Farm_Management_Components"))
