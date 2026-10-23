"""Integration tests use a real local HTTP server and isolated in-memory state."""
import http.client
import json
import threading
import unittest
from services.farm_management.app import create_server


class FarmHttpTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.payload = {"name": "Riverbend Farm", "latitude": -36.36, "longitude": 145.4, "areaHectares": 125.5}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, value=None, token="demo-owner-a", raw=None, media="application/json"):
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

    def create(self):
        return self.request("POST", "/farms", self.payload)

    def test_create_then_retrieve_exact_contract(self):
        status, headers, farm = self.create()
        self.assertEqual(status, 201)
        self.assertEqual(farm, {"id": "farm-001", **self.payload})
        self.assertEqual(headers["Location"], "/farms/farm-001")
        self.assertEqual(self.request("GET", headers["Location"])[2], farm)

    def test_cross_owner_access_is_denied_without_disclosure(self):
        self.create()
        denied = self.request("GET", "/farms/farm-001", token="demo-owner-b")
        missing = self.request("GET", "/farms/farm-999", token="demo-owner-b")
        self.assertEqual(denied[0], 404)
        self.assertEqual(denied[2], missing[2])

    def test_owner_assignment_cannot_be_supplied_by_caller(self):
        self.payload["ownerUserId"] = "owner-b"
        self.assertEqual(self.create()[0], 422)

    def test_worker_cannot_create(self):
        self.assertEqual(self.request("POST", "/farms", self.payload, token="demo-worker-a")[0], 403)

    def test_missing_and_invalid_authentication_on_both_endpoints(self):
        for method, path, value in [("POST", "/farms", self.payload), ("GET", "/farms/farm-001", None)]:
            for token in (None, "wrong-token"):
                with self.subTest(method=method, token=token):
                    status, headers, _ = self.request(method, path, value, token=token)
                    self.assertEqual(status, 401)
                    self.assertEqual(headers["WWW-Authenticate"], "Bearer")

    def test_validation_boundaries_and_types(self):
        for field, value in [("name", " "), ("name", "a"*121), ("latitude", 91), ("longitude", -181),
                             ("areaHectares", 0), ("areaHectares", -1), ("areaHectares", True),
                             ("areaHectares", "125.5"), ("latitude", None)]:
            with self.subTest(field=field, value=value):
                payload = {**self.payload, field: value}
                self.assertEqual(self.request("POST", "/farms", payload)[0], 422)
        self.assertEqual(self.request("POST", "/farms", {**self.payload, "latitude": -90, "longitude": 180})[0], 201)

    def test_invalid_json_and_nonstandard_numbers(self):
        for body in [b"{", b"\xff", b'{"areaHectares":NaN}', b'{"areaHectares":Infinity}']:
            self.assertEqual(self.request("POST", "/farms", raw=body)[0], 400)
        self.assertEqual(self.request("POST", "/farms", {**self.payload, "areaHectares": 1e309})[0], 400)
        self.assertEqual(self.request("POST", "/farms", raw=b'{"name":"X","latitude":0,"longitude":0,"areaHectares":1e999}')[0], 422)

    def test_missing_unknown_and_nonobject_fields(self):
        for payload in [{}, [], None, {**self.payload, "extra": 1}]:
            self.assertEqual(self.request("POST", "/farms", raw=json.dumps(payload).encode())[0], 422)

    def test_content_type_body_limit_and_method(self):
        self.assertEqual(self.request("POST", "/farms", self.payload, media="text/plain")[0], 415)
        self.assertEqual(self.request("POST", "/farms", raw=b" "*65537)[0], 413)
        status, headers, _ = self.request("DELETE", "/farms/farm-001")
        self.assertEqual(status, 405)
        self.assertEqual(headers["Allow"], "GET")

    def test_unique_identifiers_and_trimmed_name(self):
        first = self.create()[2]
        self.payload["name"] = "  Riverbend Farm  "
        second = self.create()[2]
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(second["name"], "Riverbend Farm")


if __name__ == "__main__":
    unittest.main()
