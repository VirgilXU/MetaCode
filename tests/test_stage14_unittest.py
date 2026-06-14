import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from core.monitoring_api import create_handler
from core.monitoring_store import export_monitoring_data


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
DOCS = ROOT / "docs"
EXPORTS = ROOT / "monitoring" / "exports"


class Stage14RepairApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        export_monitoring_data(ROOT)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(ROOT))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def get_json(self, path):
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=10) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def post_json(self, path, payload):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_status_endpoint_reports_stage14_or_newer_api(self):
        payload = self.get_json("/api/status")
        monitoring = self.get_json("/api/monitoring")

        self.assertEqual(payload["status"], "ok")
        self.assertIn(payload["version"], {"stage14", "stage16", "stage17", "stage18"})
        self.assertGreaterEqual(payload["current_stage"], 14)
        self.assertIn("POST /api/repair/fix-workflow", monitoring["api"]["endpoints"])
        self.assertIn("POST /api/repair/plan-workflow", monitoring["api"]["endpoints"])

    def test_fix_workflow_endpoint_writes_explicit_repair_event(self):
        payload = self.post_json(
            "/api/repair/fix-workflow",
            {"workflow_path": "workflows/broken_missing_clean_text.yaml"},
        )

        self.assertEqual(payload["status"], "repair_triggered")
        self.assertEqual(payload["strategy"], "fixed")
        self.assertTrue(payload["repair_id"].startswith("repair-action-"))
        self.assertEqual(payload["result"]["repair_id"], payload["repair_id"])
        self.assertEqual(payload["result"]["status"], "fixed")

        event = payload["repair_event"]
        self.assertIsNotNone(event)
        self.assertEqual(event["repair_id"], payload["repair_id"])
        self.assertEqual(event["failure_link_status"], "linked")
        self.assertEqual(event["strategy"], "fixed")
        self.assertEqual(event["event_status"], "closed_success")
        self.assertEqual(event["generated_workflow_id"], "broken_missing_clean_text_fixed")
        self.assertTrue(event["failure_run_id"])
        self.assertTrue(event["verification_run_id"])

    def test_plan_workflow_endpoint_writes_explicit_repair_event(self):
        payload = self.post_json(
            "/api/repair/plan-workflow",
            {"workflow_path": "workflows/broken_missing_summary_chain.yaml"},
        )

        self.assertEqual(payload["status"], "repair_triggered")
        self.assertEqual(payload["strategy"], "planned")
        self.assertEqual(payload["result"]["repair_id"], payload["repair_id"])
        self.assertEqual(payload["result"]["status"], "planned")

        event = payload["repair_event"]
        self.assertIsNotNone(event)
        self.assertEqual(event["repair_id"], payload["repair_id"])
        self.assertEqual(event["failure_link_status"], "linked")
        self.assertEqual(event["strategy"], "planned")
        self.assertEqual(event["event_status"], "closed_success")
        self.assertEqual(event["generated_workflow_id"], "broken_missing_summary_chain_planned")
        self.assertGreaterEqual(len(event["inserted_steps"]), 2)

    def test_repair_events_export_contains_explicit_action_ids(self):
        payload = self.post_json(
            "/api/repair/fix-workflow",
            {"workflow_path": "workflows/broken_missing_clean_text.yaml"},
        )
        export_payload = json.loads((EXPORTS / "repair_events.json").read_text(encoding="utf-8"))
        event_ids = {event["repair_id"] for event in export_payload["events"]}

        self.assertIn(payload["repair_id"], event_ids)

    def test_dashboard_contains_repair_action_and_detail_ui(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")
        css = (DASHBOARD / "styles.css").read_text(encoding="utf-8")

        self.assertIn("repairWorkflowSelect", html)
        self.assertIn("fixWorkflowBtn", html)
        self.assertIn("planWorkflowBtn", html)
        self.assertIn("repairEventDetail", html)
        self.assertIn("triggerRepair", app)
        self.assertIn("postJson", app)
        self.assertIn("renderRepairEventDetail", app)
        self.assertIn(".repair-action-panel", css)
        self.assertIn(".event-detail-button", css)

    def test_stage14_report_and_project_record_exist(self):
        report = DOCS / "Stage 14 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十四阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 14", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
