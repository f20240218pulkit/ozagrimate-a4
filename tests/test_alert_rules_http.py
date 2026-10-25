"""Alert-rule endpoints on the Irrigation and Alerts service: real local HTTP server."""
import http.client
import json
import threading
import unittest
from services.irrigation_alerts.app import create_server

BASE = "/farms/farm-001/alert-rules"


class AlertRuleHttpTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        # sensorId matches the telemetry reading's deviceId; units follow the telemetry catalogue.
        self.rule = {"name": "Dry north paddock", "sensorId": "sm-north-01", "metric": "soilMoisture",
                     "operator": "<", "threshold": 20, "unit": "%", "severity": "critical",
                     "reminderMinutes": 30}

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
        data = response.read()
        result = response.status, dict(response.getheaders()), json.loads(data) if data else None
        connection.close()
        return result

    def create(self, token="demo-owner-a", farm="farm-001"):
        return self.request("POST", "/farms/" + farm + "/alert-rules", self.rule, token=token)

    # --- POST /farms/{farmId}/alert-rules ---------------------------------------------
    def test_owner_creates_rule_with_exact_contract(self):
        status, headers, body = self.create()
        self.assertEqual(status, 201)
        self.assertEqual(body, {**self.rule, "ruleId": "rule-001", "farmId": "farm-001"})
        self.assertEqual(headers["Location"], BASE + "/rule-001")

    def test_text_fields_are_trimmed_and_reminder_may_be_null(self):
        self.rule.update(name="  Dry soil  ", reminderMinutes=None)
        status, _, body = self.create()
        self.assertEqual((status, body["name"], body["reminderMinutes"]), (201, "Dry soil", None))

    def test_worker_cannot_manage_rules(self):
        status, _, body = self.create(token="demo-worker-a")
        self.assertEqual((status, body["error"]["code"]), (403, "FORBIDDEN"))

    def test_cross_owner_and_missing_farm_are_indistinguishable(self):
        denied = self.create(token="demo-owner-b")
        missing = self.create(farm="farm-999")
        self.assertEqual(denied[0], 404)
        self.assertEqual(denied[2], missing[2])
        self.assertEqual(denied[2]["error"]["code"], "FARM_NOT_FOUND")

    def test_stale_farm_access_rejects_rule_changes(self):
        status, headers, body = self.create(farm="farm-003")
        self.assertEqual((status, body["error"]["code"]), (503, "FARM_ACCESS_STALE"))
        self.assertEqual(headers["Retry-After"], "5")

    def test_validation(self):
        cases = [("operator", ">="), ("severity", "info"), ("threshold", "20"), ("threshold", True),
                 ("reminderMinutes", 0), ("reminderMinutes", 10081), ("reminderMinutes", 2.5),
                 ("name", " "), ("unit", "x" * 121), ("ruleId", "rule-777")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                status, _, body = self.request("POST", BASE, {**self.rule, field: value})
                self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_ERROR"))
        missing = {k: v for k, v in self.rule.items() if k != "unit"}
        self.assertEqual(self.request("POST", BASE, missing)[0], 422)

    # --- DELETE /farms/{farmId}/alert-rules/{ruleId} -----------------------------------
    def test_delete_rule_then_delete_again(self):
        rule_id = self.create()[2]["ruleId"]
        status, headers, body = self.request("DELETE", BASE + "/" + rule_id)
        self.assertEqual((status, body), (204, None))
        self.assertNotIn("Content-Type", headers)
        status, _, body = self.request("DELETE", BASE + "/" + rule_id)
        self.assertEqual((status, body["error"]["code"]), (404, "RULE_NOT_FOUND"))

    def test_rule_cannot_be_deleted_through_another_farm(self):
        rule_id = self.create()[2]["ruleId"]
        status, _, body = self.request("DELETE", "/farms/farm-002/alert-rules/" + rule_id, token="demo-owner-b")
        self.assertEqual((status, body["error"]["code"]), (404, "RULE_NOT_FOUND"))
        self.assertEqual(self.request("DELETE", BASE + "/" + rule_id)[0], 204)

    def test_worker_and_other_owner_cannot_delete(self):
        rule_id = self.create()[2]["ruleId"]
        self.assertEqual(self.request("DELETE", BASE + "/" + rule_id, token="demo-worker-a")[0], 403)
        self.assertEqual(self.request("DELETE", BASE + "/" + rule_id, token="demo-owner-b")[0], 404)

    # --- Shared transport and authentication -------------------------------------------
    def test_authentication_media_type_and_methods(self):
        for method, path in [("POST", BASE), ("DELETE", BASE + "/rule-001")]:
            status, headers, _ = self.request(method, path, self.rule, token=None)
            self.assertEqual((status, headers["WWW-Authenticate"]), (401, "Bearer"))
        self.assertEqual(self.request("POST", BASE, self.rule, media="text/plain")[0], 415)
        self.assertEqual(self.request("POST", BASE, raw=b"{")[0], 400)
        status, headers, _ = self.request("GET", BASE)
        self.assertEqual((status, headers["Allow"]), (405, "POST"))
        status, headers, _ = self.request("PUT", BASE + "/rule-001", self.rule)
        self.assertEqual((status, headers["Allow"]), (405, "DELETE"))

    # --- Metric / unit catalogue (mirrors Telemetry's reading contract) -----------------
    def test_unsupported_metric_is_rejected(self):
        for metric in ("humidity", "soilmoisture", ""):
            with self.subTest(metric=metric):
                status, _, body = self.request("POST", BASE, {**self.rule, "metric": metric})
                self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_ERROR"))

    def test_wrong_unit_for_metric_is_rejected(self):
        cases = [("soilMoisture", "percent"), ("soilMoisture", "degC"), ("soilTemperature", "C"),
                 ("airTemperature", "celsius"), ("rainfall", "%"), ("rainfall", "MM")]
        for metric, unit in cases:
            with self.subTest(metric=metric, unit=unit):
                status, _, body = self.request("POST", BASE, {**self.rule, "metric": metric, "unit": unit})
                self.assertEqual((status, body["error"]["code"]), (422, "VALIDATION_ERROR"))

    def test_every_catalogue_pair_is_accepted_after_trimming(self):
        for metric, unit in [("soilMoisture", "%"), ("soilTemperature", "degC"),
                             ("airTemperature", "degC"), ("rainfall", "mm")]:
            with self.subTest(metric=metric):
                status, _, body = self.request("POST", BASE, {**self.rule, "metric": " " + metric + " ",
                                                              "unit": " " + unit + " "})
                self.assertEqual((status, body["metric"], body["unit"]), (201, metric, unit))

    # --- Rule evaluation with % (Bradley's evaluate(); not exposed over HTTP) ----------
    def evaluator(self):
        from services.irrigation_alerts.alert_rule_service import AlertRuleService
        from services.irrigation_alerts.farm_projection import FarmAccessProjection
        from services.irrigation_alerts.farm_events import FixtureFarmEventSource
        from services.irrigation_alerts.security import Principal
        clock = lambda: 5000.0
        projection = FarmAccessProjection()
        alerts = AlertRuleService(projection, FixtureFarmEventSource(projection, clock), clock)
        rule = alerts.create(Principal("owner-a", "owner"), "farm-001", self.rule)
        return alerts, rule

    def test_valid_percent_rule_alerts_on_matching_low_reading(self):
        alerts, rule = self.evaluator()
        emitted = alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 12.5, "%", now=0)
        self.assertEqual([(n["ruleId"], n["kind"], n["value"]) for n in emitted], [(rule["ruleId"], "triggered", 12.5)])
        # A reading above the threshold, another device, or another unit does not trigger it.
        self.assertEqual(alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 25, "%", now=10), [])
        self.assertEqual(alerts.evaluate("farm-001", "sm-south-02", "soilMoisture", 5, "%", now=20), [])
        self.assertEqual(alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 5, "percent", now=30), [])

    def test_duplicate_suppression_and_critical_reminder_with_percent(self):
        alerts, _ = self.evaluator()
        first = alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 12, "%", now=0)
        duplicate = alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 11, "%", now=60)
        reminder = alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 10, "%", now=1800)
        alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 35, "%", now=1900)        # resolves incident
        again = alerts.evaluate("farm-001", "sm-north-01", "soilMoisture", 15, "%", now=2000)
        self.assertEqual(duplicate, [])
        self.assertEqual([n["kind"] for n in first + reminder + again], ["triggered", "reminder", "triggered"])

if __name__ == "__main__":
    unittest.main()
