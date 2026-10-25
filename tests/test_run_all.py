"""Integration smoke test: all three services start together and answer on their own ports."""
import http.client
import json
import unittest
import run_all


class RunAllTests(unittest.TestCase):
    def test_all_services_start_side_by_side(self):
        running = run_all.start_all(ports=[0, 0, 0])
        try:
            ports = {name: server.server_address[1] for name, server, _ in running}
            checks = [("Farm Management", "POST", "/farms", {"name": "Riverbend Farm", "latitude": -36.36,
                                                             "longitude": 145.4, "areaHectares": 125.5},
                       "demo-owner-a", 201),
                      ("Telemetry", "GET", "/farms/farm-001/telemetry", None, "demo-owner-a", 200),
                      ("Irrigation and Alerts", "POST", "/farms/farm-001/irrigation-requests",
                       {"paddockId": "north-paddock", "scheduledStart": "2026-11-02T19:00:00Z",
                        "durationMinutes": 90, "waterDepthMm": 18.5}, "demo-owner-a", 201),
                      ("Irrigation and Alerts", "POST", "/farms/farm-001/alert-rules",
                       {"name": "Dry soil", "sensorId": "sm-north-01", "metric": "soilMoisture",
                        "operator": "<", "threshold": 20, "unit": "%", "severity": "warning",
                        "reminderMinutes": None}, "demo-owner-a", 201)]
            for name, method, path, body, token, expected in checks:
                with self.subTest(service=name):
                    connection = http.client.HTTPConnection("127.0.0.1", ports[name], timeout=5)
                    connection.request(method, path, body=json.dumps(body).encode() if body else None,
                                       headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
                    response = connection.getresponse()
                    response.read()
                    connection.close()
                    self.assertEqual(response.status, expected)
        finally:
            for _, server, _ in running:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
