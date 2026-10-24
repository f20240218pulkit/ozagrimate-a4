"""Telemetry C4 Component Diagram (Aditya). Run: python3 diagrams/src/telemetry_components.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from drawlib import Canvas, BLUE, GREEN, GREY, BOUNDARY


class BigCanvas(Canvas):
    """Larger type than the shared default so the figure stays readable when printed."""
    def element(self, x, y, w, h, title, tag, desc, fill=BLUE, dashed=False):
        self.rect(x, y, w, h, fill, dashed=dashed)
        cx = x + w / 2
        self.text(cx, y + 40, title, 27, "bold")
        self.text(cx, y + 70, tag, 20)
        for i, line in enumerate(desc):
            self.text(cx, y + 104 + i * 29, line, 22)

    def label(self, x, y, lines, size=21, weight="normal", anchor="middle", bg="white"):
        super().label(x, y, lines, size, weight, anchor, bg)

c = BigCanvas(2400, 2230)
c.text(40, 77, "OzAgriMate Telemetry - C4 Component Diagram", 32, "bold", "start")
c.text(40, 107, "Components inside the Telemetry container | solid = implemented module, dashed = proposed / production-only interaction", 19, "normal", "start")

W, H = 600, 175
X1, X2, X3 = 100, 900, 1700
cx1, cx2, cx3 = X1 + W / 2, X2 + W / 2, X3 + W / 2

# Neighbouring containers (outside the boundary)
c.element(X1, 150, W, H, "Farm Edge Gateway", "[Container: edge software]",
          ["Normalises equipment data to the", "v1 reading contract; buffers 72 h."], GREY)
c.element(X2, 150, W, H, "API Gateway", "[Container: managed HTTP gateway]",
          ["Routes /api/v1 reads from Web and", "Mobile Apps; authenticates users."], GREY)
c.element(X3, 150, W, H, "Identity and Access", "[Container: managed OAuth identity]",
          ["Issues user and gateway machine", "credentials; verifies tokens."], GREY)

# Container boundary
R1, R2, R3, R4 = 470, 780, 1090, 1400
c.rect(60, 390, 2280, R4 + H + 60 - 390, BOUNDARY, "#9bb0c0")
c.text(80, 425, "Telemetry [Container: backend service] - services/telemetry/", 23, "bold", "start")

c.element(X1, R1, W, H, "HTTP Server", "[Component: app.py]",
          ["Hosts local HTTP transport; wires", "all Telemetry components (port 8002)."])
c.element(X2, R1, W, H, "Telemetry REST Controller", "[Component: api.py]",
          ["Routes POST and GET telemetry;", "maps errors to the JSON envelope."])
c.element(X3, R1, W, H, "Identity Adapter", "[Component: security.py]",
          ["Resolves bearer token to a user or", "gateway principal (demo fixtures)."])
c.element(X1, R2, W, H, "Telemetry Ingestion Service", "[Component: ingestion_service.py]",
          ["Validates, de-duplicates, classifies,", "stores, then publishes a reading."])
c.element(X2, R2, W, H, "Farm Access Read Model", "[Component: farm_access.py]",
          ["Local copy of farms, grants and", "registered gateways; no Farm Store reads."])
c.element(X3, R2, W, H, "Telemetry Query Service", "[Component: query_service.py]",
          ["Farm-scoped filtered reads, capped", "at 500 readings per request."])
c.element(X1, R3, W, H, "Reading Model / Validator", "[Component: models.py]",
          ["Schema v1 contract: metric units,", "ranges and UTC timestamps."])
c.element(X2, R3, W, H, "Anomaly Detector", "[Component: anomaly_detector.py]",
          ["Quarantines spikes and implausible", "values with reason codes (ASR5)."])
c.element(X1, R4, W, H, "Accepted Reading Publisher", "[Component: event_publisher.py]",
          ["Outbox of ReadingAccepted events,", "partitioned by farmId."])
c.element(X2, R4, W, H, "Telemetry Repository", "[Component: repository.py]",
          ["Per-farm partitions keyed by", "readingId; bounded range queries."])

# Data, messaging and consuming containers
B = R4 + H + 130
c.element(X1, B, W, H, "Event Broker", "[Container: managed durable messaging]",
          ["Buffers accepted readings; supports", "replay and retry."], GREEN)
c.element(X2, B, W, H, "Telemetry Store", "[Container: managed time-series data]",
          ["Accepted and quarantined readings,", "partitioned by farm and time."], GREEN)
HW = (W - 30) // 2
c.element(1575, B, 370, H, "Irrigation and Alerts", "[Container: backend]",
          ["Evaluates alert rules", "on accepted readings."], GREY)
c.element(1960, B, 380, H, "AI Recommendation", "[Container: inference]",
          ["Uses accepted readings", "as advice inputs."], GREY)

# Relationships - inbound
c.arrow([(cx1 - 120, 320), (cx1 - 120, R1)]);             c.label(cx1 - 110, 360, ["Submits readings", "[JSON/HTTPS]"], anchor="start")
c.arrow([(cx2, 320), (cx2, 360), (cx1 + 150, 360), (cx1 + 150, R1)]); c.label((cx1 + cx2) / 2 + 150, 352, "Forwards reads [JSON/HTTP]")
c.arrow([(X1 + W, R1 + 85), (X2, R1 + 85)]);             c.label((X1 + W + X2) / 2, R1 + 72, ["Dispatches", "requests"])
c.arrow([(X2 + W, R1 + 85), (X3, R1 + 85)]);             c.label((X2 + W + X3) / 2, R1 + 72, ["Authenticates", "caller"])
c.arrow([(cx3, R1), (cx3, 320)], dashed=True);            c.label(cx3, 362, "Validates tokens [production]")
# Controller -> use-case services
T = R1 + H + 45
c.arrow([(cx2, R1 + H), (cx2, T), (cx1, T), (cx1, R2)]);  c.label((cx1 + cx2) / 2, T - 10, "submit(reading)")
c.arrow([(cx2, T), (cx3, T), (cx3, R2)]);                 c.label((cx2 + cx3) / 2, T - 10, "list(filters)")
# Authorisation against the read model
c.arrow([(X1 + W, R2 + 45), (X2, R2 + 45)]);             c.label((X1 + W + X2) / 2, R2 + 32, ["Gateway", "registered?"])
c.arrow([(X3, R2 + 45), (X2 + W, R2 + 45)]);             c.label((X2 + W + X3) / 2, R2 + 32, ["Owner or", "granted worker?"])
# Ingestion pipeline
c.arrow([(cx1, R2 + H), (cx1, R3)]);                      c.label(cx1, R2 + H + 50, "Parses and validates")
c.arrow([(X1 + W, R2 + 115), (820, R2 + 115), (820, R3 + 85), (X2, R3 + 85)]); c.label(875, R3 + 72, ["Classifies"], anchor="middle")
c.arrow([(X1 + W, R2 + 150), (770, R2 + 150), (770, R4 + 60), (X2, R4 + 60)]); c.label(850, R4 + 47, ["Stores /", "replay check"], anchor="middle")
c.arrow([(X1, R2 + 130), (90, R2 + 130), (90, R4 + 85), (X1, R4 + 85)]); c.label(98, R3 + 230, ["Publishes", "if ACCEPTED"], anchor="start")
c.arrow([(cx2, R3 + H), (cx2, R4)]);                      c.label(cx2, R3 + H + 48, "Reads last accepted value")
c.arrow([(X3, R2 + 145), (1605, R2 + 145), (1605, R4 + 85), (X2 + W, R4 + 85)]); c.label(1610, R3 + 85, ["Bounded", "range query"], anchor="start")
# Outbound to data and messaging
c.arrow([(cx1, R4 + H), (cx1, B)], dashed=True);          c.label(cx1, R4 + H + 95, "Relays events [proposed; in-memory outbox now]")
c.arrow([(cx2, R4 + H), (cx2, B)]);                       c.label(cx2, R4 + H + 95, "Reads / writes [in-memory dict in prototype]")
IA, AI = 1575 + 185, 1960 + 190
c.arrow([(cx1, B + H), (cx1, B + H + 50), (AI, B + H + 50), (AI, B + H)], dashed=True)
c.arrow([(IA, B + H + 50), (IA, B + H)], dashed=True)
c.label(cx2, B + H + 58, "Delivers ReadingAccepted events, partitioned by farmId [proposed]")

# Legend
y = B + H + 120
c.text(60, y, "Legend", 21, "bold", "start")
for i, (fill, name) in enumerate([(BLUE, "Implemented component (Python module)"),
                                  (GREY, "Other container"),
                                  (GREEN, "Data store or messaging container")]):
    x = 60 + i * 640
    c.rect(x, y + 20, 60, 36, fill)
    c.text(x + 75, y + 46, name, 21, "normal", "start")
c.arrow([(1980, y + 38), (2080, y + 38)], dashed=True); c.text(2090, y + 44, "Proposed", 21, "normal", "start")
c.text(60, y + 115, "Prototype: one Python process at 127.0.0.1:8002 with demonstration identities; no broker, OAuth provider or time-series database is deployed.", 21, "italic", "start")

c.img = c.img.crop((0, 0, 2400, int(y + 140)))
c.svg[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="{int(y + 140)}" viewBox="0 0 2400 {int(y + 140)}">'
c.save(os.path.join(os.path.dirname(__file__), "..", "Telemetry_Components"))
