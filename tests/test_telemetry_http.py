"""Telemetry endpoints: real local HTTP server, isolated in-memory state per test."""
import http.client
import json
import threading
import unittest
from services.telemetry.app import create_server

BASE = "/farms/farm-001/telemetry"
FIXED_NOW = 1793000000.0  # 2026-10-26T07:33:20Z; makes the future-timestamp rule deterministic


class TelemetryHttpTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(port=0, clock=lambda: FIXED_NOW)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.reading = {"schemaVersion": 1, "readingId": "sm-north-01-20261023T2045Z",
                        "deviceId": "sm-north-01", "paddockId": "north-paddock",
                        "metric": "soilMoisture", "value": 29.7, "unit": "%",
                        "observedAt": "2026-10-23T20:45:00Z"}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, value=None, token="demo-gateway-001", raw=None, media="application/json"):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {"Content-Type": media}
        if token:
            headers["Authorization"] = "Bearer " + token
        body = raw if raw is not None else json.dumps(value).encode() if value is not None else None
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), json.loads(response.read())
        connection.close()
        return result

    def submit(self, reading=None, token="demo-gateway-001", farm="farm-001"):
        return self.request("POST", "/farms/" + farm + "/telemetry", reading or self.reading, token=token)

    def get(self, query="", token="demo-owner-a", farm="farm-001"):
        return self.request("GET", "/farms/" + farm + "/telemetry" + query, token=token)

    # --- POST /farms/{farmId}/telemetry --------------------------------------------
    def test_gateway_submits_accepted_reading_with_exact_contract(self):
        status, _, body = self.submit()
        self.assertEqual(status, 201)
        expected = {k: v for k, v in self.reading.items()}
        self.assertEqual(body, {**expected, "farmId": "farm-001", "receivedAt": "2026-10-26T07:33:20Z",
                                "status": "ACCEPTED", "quarantineReasons": []})
        events = self.server.publisher.pending_events()
        self.assertEqual(len(events), 1)
        self.assertEqual({k: events[0][k] for k in ("type", "farmId", "readingId", "schemaVersion", "partitionKey")},
                         {"type": "ReadingAccepted", "farmId": "farm-001", "readingId": self.reading["readingId"],
                          "schemaVersion": 1, "partitionKey": "farm-001"})

    def test_identical_replay_is_idempotent_and_not_republished(self):
        first = self.submit()
        replay = self.submit()
        self.assertEqual((first[0], replay[0]), (201, 200))
        self.assertEqual(first[2], replay[2])
        self.assertEqual(len(self.server.publisher.pending_events()), 1)

    def test_reused_reading_id_with_different_content_conflicts(self):
        self.submit()
        status, _, body = self.submit({**self.reading, "value": 28.0})
        self.assertEqual((status, body["error"]["code"]), (409, "READING_ID_CONFLICT"))

    def test_spike_is_quarantined_stored_and_not_published(self):
        spike = {**self.reading, "readingId": "sm-north-01-20261023T2045Z-b", "value": 88.0}
        status, _, body = self.submit(spike)
        self.assertEqual(status, 201)
        self.assertEqual((body["status"], body["quarantineReasons"]), ("QUARANTINED", ["SPIKE_DETECTED"]))
        self.assertEqual(self.server.publisher.pending_events(), [])
        listed = self.get("?status=QUARANTINED")[2]
        self.assertEqual([r["readingId"] for r in listed["readings"]], [spike["readingId"]])

    def test_implausible_rainfall_is_quarantined(self):
        rain = {**self.reading, "readingId": "rg-01-1", "deviceId": "rg-01", "metric": "rainfall",
                "unit": "mm", "value": 150}
        body = self.submit(rain)[2]
        self.assertEqual((body["status"], body["quarantineReasons"]), ("QUARANTINED", ["IMPLAUSIBLE_VALUE"]))

    def test_non_gateway_and_foreign_gateway_cannot_submit(self):
        for token in ("demo-owner-a", "demo-worker-a"):
            status, _, body = self.submit(token=token)
            self.assertEqual((status, body["error"]["code"]), (403, "FORBIDDEN"))
        foreign = self.submit(token="demo-gateway-002")
        missing = self.submit(farm="farm-999")
        self.assertEqual((foreign[0], foreign[2]["error"]["code"]), (404, "FARM_NOT_FOUND"))
        self.assertEqual(foreign[2], missing[2])

    def test_schema_validation(self):
        cases = [("value", 100.1), ("value", -0.1), ("value", "29.7"), ("value", True), ("value", None),
                 ("unit", "percent"), ("metric", "humidity"), ("deviceId", "SM North"),
                 ("paddockId", ""), ("readingId", "bad id"), ("observedAt", "2026-10-23 20:45"),
                 ("observedAt", "2026-02-30T20:45:00Z"), ("observedAt", "2026-10-26T07:40:00Z")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                status, _, body = self.submit({**self.reading, field: value})
                self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_ERROR"))
        boundary = {**self.reading, "readingId": "edge-ok", "observedAt": "2026-10-26T07:38:20Z"}
        self.assertEqual(self.submit(boundary)[0], 201)

    def test_caller_cannot_supply_server_fields_and_schema_version_is_checked(self):
        for field, value in [("farmId", "farm-002"), ("status", "ACCEPTED"), ("receivedAt", "2026-10-23T20:45:00Z")]:
            with self.subTest(field=field):
                self.assertEqual(self.submit({**self.reading, field: value})[0], 422)
        for version in (2, "1", None):
            status, _, body = self.submit({**self.reading, "schemaVersion": version})
            self.assertEqual((status, body["error"]["code"]), (422, "UNSUPPORTED_SCHEMA_VERSION"))
        missing = {k: v for k, v in self.reading.items() if k != "unit"}
        self.assertEqual(self.submit(missing)[0], 422)
        for payload in ([], None, "text"):
            self.assertEqual(self.request("POST", BASE, raw=json.dumps(payload).encode())[0], 422)

    # --- GET /farms/{farmId}/telemetry ---------------------------------------------
    def test_owner_lists_seeded_and_new_readings_in_order(self):
        self.submit()
        status, _, body = self.get("?metric=soilMoisture&deviceId=sm-north-01")
        self.assertEqual(status, 200)
        self.assertEqual((body["farmId"], body["count"], body["hasMore"]), ("farm-001", 4, False))
        self.assertEqual([r["value"] for r in body["readings"]], [31.2, 30.8, 30.1, 29.7])
        self.assertTrue(all(r["status"] == "ACCEPTED" for r in body["readings"]))

    def test_filters_window_status_and_limit(self):
        self.assertEqual(self.get()[2]["count"], 4)  # 3 soil moisture + 1 air temperature seeded
        windowed = self.get("?from=2026-10-23T20:10:00Z&to=2026-10-23T20:20:00Z")[2]
        self.assertEqual([r["readingId"] for r in windowed["readings"]], ["sm-north-01-20261023T2015Z"])
        limited = self.get("?limit=2")[2]
        self.assertEqual((limited["count"], limited["hasMore"]), (2, True))
        self.assertEqual(self.get("?metric=airTemperature")[2]["readings"][0]["unit"], "degC")
        self.assertEqual(self.get("?status=ALL&paddockId=south-paddock")[2]["count"], 0)

    def test_granted_worker_reads_but_other_owner_and_gateway_cannot(self):
        self.assertEqual(self.get(token="demo-worker-a")[0], 200)
        denied = self.get(token="demo-owner-b")
        missing = self.get(farm="farm-999")
        self.assertEqual((denied[0], denied[2]["error"]["code"]), (404, "FARM_NOT_FOUND"))
        self.assertEqual(denied[2], missing[2])
        self.assertEqual(self.get(token="demo-worker-a", farm="farm-002")[0], 404)
        status, _, body = self.get(token="demo-gateway-001")
        self.assertEqual((status, body["error"]["code"]), (403, "FORBIDDEN"))
        own = self.get(token="demo-owner-b", farm="farm-002")[2]
        self.assertEqual([r["farmId"] for r in own["readings"]], ["farm-002"])

    def test_invalid_query_parameters(self):
        for query in ("?metric=humidity", "?limit=0", "?limit=501", "?limit=ten", "?status=pending",
                      "?from=yesterday", "?from=2026-10-24T00:00:00Z&to=2026-10-23T00:00:00Z",
                      "?farmId=farm-002", "?metric=rainfall&metric=soilMoisture", "?deviceId=Bad Id"):
            with self.subTest(query=query):
                status, _, body = self.get(query.replace(" ", "%20"))
                self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_ERROR"))

    # --- Shared transport and authentication ---------------------------------------
    def test_missing_and_invalid_authentication_on_both_operations(self):
        for method in ("POST", "GET"):
            for token in (None, "wrong-token"):
                with self.subTest(method=method, token=token):
                    status, headers, _ = self.request(method, BASE, self.reading if method == "POST" else None, token=token)
                    self.assertEqual(status, 401)
                    self.assertEqual(headers["WWW-Authenticate"], "Bearer")

    def test_media_type_json_methods_and_routes(self):
        self.assertEqual(self.request("POST", BASE, self.reading, media="text/plain")[0], 415)
        self.assertEqual(self.request("POST", BASE, raw=b"{")[0], 400)
        self.assertEqual(self.request("POST", BASE, raw=b'{"value":NaN}')[0], 400)
        status, headers, _ = self.request("DELETE", BASE)
        self.assertEqual((status, headers["Allow"]), (405, "GET, POST"))
        self.assertEqual(self.request("GET", "/farms/farm-001/telemetry/x")[0], 404)
        self.assertEqual(self.request("GET", "/farms/FARM-1/telemetry")[0], 404)


if __name__ == "__main__":
    unittest.main()
