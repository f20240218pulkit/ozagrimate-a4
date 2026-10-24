"""Irrigation request endpoints: real local HTTP server, isolated in-memory state."""
import http.client
import json
import threading
import unittest
from services.irrigation_alerts.app import create_server

BASE = "/farms/farm-001/irrigation-requests"
APPROVED = BASE + "/irr-001"


class IrrigationHttpTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.payload = {"paddockId": "north-paddock", "scheduledStart": "2026-11-02T19:00:00Z",
                        "durationMinutes": 90, "waterDepthMm": 18.5, "notes": "Pre-heatwave watering"}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, value=None, token="demo-worker-a", raw=None, media="application/json"):
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

    def create(self, token="demo-worker-a"):
        return self.request("POST", BASE, self.payload, token=token)

    # --- POST /farms/{farmId}/irrigation-requests -------------------------------------
    def test_worker_creates_pending_request_with_exact_contract(self):
        status, headers, body = self.create()
        self.assertEqual(status, 201)
        self.assertEqual(body, {"id": "irr-002", "farmId": "farm-001", **self.payload,
                                "status": "PENDING", "requestedBy": "worker-a", "version": 1})
        self.assertEqual(headers["Location"], BASE + "/irr-002")

    def test_owner_can_create_and_notes_are_optional(self):
        del self.payload["notes"]
        status, _, body = self.create(token="demo-owner-a")
        self.assertEqual(status, 201)
        self.assertEqual((body["notes"], body["requestedBy"]), ("", "owner-a"))

    def test_cross_owner_and_missing_farm_are_indistinguishable(self):
        denied = self.create(token="demo-owner-b")
        missing = self.request("POST", "/farms/farm-999/irrigation-requests", self.payload)
        self.assertEqual(denied[0], 404)
        self.assertEqual(denied[2], missing[2])
        self.assertEqual(denied[2]["error"]["code"], "FARM_NOT_FOUND")

    def test_worker_without_grant_is_denied(self):
        status, _, body = self.request("POST", "/farms/farm-002/irrigation-requests", self.payload)
        self.assertEqual((status, body["error"]["code"]), (404, "FARM_NOT_FOUND"))

    def test_stale_farm_access_rejects_mutations(self):
        status, headers, body = self.request("POST", "/farms/farm-003/irrigation-requests", self.payload,
                                             token="demo-owner-a")
        self.assertEqual((status, body["error"]["code"]), (503, "FARM_ACCESS_STALE"))
        self.assertEqual(headers["Retry-After"], "5")

    def test_caller_cannot_supply_status_owner_or_identity(self):
        for field, value in [("status", "APPROVED"), ("requestedBy", "owner-b"), ("id", "irr-777"),
                             ("ownerUserId", "owner-b")]:
            with self.subTest(field=field):
                self.assertEqual(self.request("POST", BASE, {**self.payload, field: value})[0], 422)

    def test_safe_limits_and_types(self):
        cases = [("durationMinutes", 0), ("durationMinutes", 241), ("durationMinutes", 30.5),
                 ("durationMinutes", True), ("durationMinutes", "90"), ("waterDepthMm", 0.4),
                 ("waterDepthMm", 50.1), ("waterDepthMm", None), ("paddockId", ""),
                 ("paddockId", "North Paddock"), ("scheduledStart", "2026-11-02 19:00"),
                 ("scheduledStart", "2026-02-30T19:00:00Z"), ("notes", "x" * 501)]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                status, _, body = self.request("POST", BASE, {**self.payload, field: value})
                self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_ERROR"))
        for duration, depth in [(1, 0.5), (240, 50)]:
            body = {**self.payload, "durationMinutes": duration, "waterDepthMm": depth}
            self.assertEqual(self.request("POST", BASE, body)[0], 201)

    def test_missing_fields_and_non_objects(self):
        for payload in [{}, [], None, {k: v for k, v in self.payload.items() if k != "waterDepthMm"}]:
            self.assertEqual(self.request("POST", BASE, raw=json.dumps(payload).encode())[0], 422)

    # --- PUT /farms/{farmId}/irrigation-requests/{requestId} --------------------------
    def test_replace_pending_request(self):
        created = self.create()[2]
        replacement = {"paddockId": "south-paddock", "scheduledStart": "2026-11-03T18:30:00Z",
                       "durationMinutes": 60, "waterDepthMm": 12}
        status, _, body = self.request("PUT", BASE + "/" + created["id"], replacement)
        self.assertEqual(status, 200)
        self.assertEqual(body, {"id": created["id"], "farmId": "farm-001", **replacement, "notes": "",
                                "status": "PENDING", "requestedBy": "worker-a", "version": 2})

    def test_replace_is_full_replacement_not_patch(self):
        created = self.create()[2]
        status, _, body = self.request("PUT", BASE + "/" + created["id"], {"durationMinutes": 30})
        self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_ERROR"))

    def test_approved_request_cannot_be_replaced(self):
        status, _, body = self.request("PUT", APPROVED, self.payload, token="demo-owner-a")
        self.assertEqual((status, body["error"]["code"]), (409, "REQUEST_NOT_EDITABLE"))

    def test_missing_request_and_request_on_another_farm(self):
        status, _, body = self.request("PUT", BASE + "/irr-999", self.payload)
        self.assertEqual((status, body["error"]["code"]), (404, "IRRIGATION_REQUEST_NOT_FOUND"))
        cross = self.request("PUT", "/farms/farm-002/irrigation-requests/irr-001", self.payload,
                             token="demo-owner-b")
        self.assertEqual((cross[0], cross[2]["error"]["code"]), (404, "IRRIGATION_REQUEST_NOT_FOUND"))

    def test_cross_owner_replace_is_denied(self):
        created = self.create()[2]
        status, _, body = self.request("PUT", BASE + "/" + created["id"], self.payload, token="demo-owner-b")
        self.assertEqual((status, body["error"]["code"]), (404, "FARM_NOT_FOUND"))

    # --- Shared transport and authentication -----------------------------------------
    def test_missing_and_invalid_authentication_on_both_endpoints(self):
        for method, path in [("POST", BASE), ("PUT", APPROVED)]:
            for token in (None, "wrong-token"):
                with self.subTest(method=method, token=token):
                    status, headers, _ = self.request(method, path, self.payload, token=token)
                    self.assertEqual(status, 401)
                    self.assertEqual(headers["WWW-Authenticate"], "Bearer")

    def test_media_type_json_methods_and_routes(self):
        self.assertEqual(self.request("POST", BASE, self.payload, media="text/plain")[0], 415)
        self.assertEqual(self.request("POST", BASE, raw=b"{")[0], 400)
        self.assertEqual(self.request("POST", BASE, raw=b'{"waterDepthMm":NaN}')[0], 400)
        status, headers, _ = self.request("GET", BASE)
        self.assertEqual((status, headers["Allow"]), (405, "POST"))
        status, headers, _ = self.request("DELETE", APPROVED)
        self.assertEqual((status, headers["Allow"]), (405, "PUT"))
        self.assertEqual(self.request("POST", "/farms/farm-001/irrigation")[0], 404)


if __name__ == "__main__":
    unittest.main()
