import json
import threading
import unittest
import urllib.request
from pathlib import Path

from core.monitoring_api import create_handler
from core.monitoring_store import export_monitoring_data
from http.server import ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
DOCS = ROOT / "docs"


class Stage12RepairLoopTest(unittest.TestCase):
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

    def test_status_endpoint_reports_stage12_api(self):
        payload = self.get_json("/api/status")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["version"], "stage12")
        self.assertGreaterEqual(payload["current_stage"], 12)
        self.assertIn("repair_success_rate", payload["summary"])

    def test_monitoring_bundle_contains_repair_metrics(self):
        payload = self.get_json("/api/monitoring")

        self.assertIn("repairs", payload)
        self.assertIn("summary", payload["repairs"])
        self.assertIn("/api/repairs/summary", payload["api"]["endpoints"])
        self.assertEqual(payload["diagnostics"]["summary"]["repair_success_rate_status"], "computed")

    def test_repair_endpoints_are_readable(self):
        summary = self.get_json("/api/repairs/summary")
        by_strategy = self.get_json("/api/repairs/by-strategy")
        by_workflow = self.get_json("/api/repairs/by-workflow")
        recent = self.get_json("/api/repairs/recent")

        self.assertGreater(summary["attempt_count"], 0)
        self.assertEqual(summary["attempt_count"], summary["success_count"] + summary["failed_count"])
        self.assertGreaterEqual(summary["repair_success_rate"], 0)
        self.assertTrue(any(row["strategy"] == "fixed" for row in by_strategy))
        self.assertTrue(any(row["strategy"] == "planned" for row in by_strategy))
        self.assertTrue(by_workflow)
        self.assertTrue(recent)

    def test_repair_rows_are_sorted_by_attempt_count(self):
        by_workflow = self.get_json("/api/repairs/by-workflow")

        self.assertEqual(
            [row["attempt_count"] for row in by_workflow],
            sorted([row["attempt_count"] for row in by_workflow], reverse=True),
        )

    def test_dashboard_contains_repair_loop_section(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")
        css = (DASHBOARD / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="repairs"', html)
        self.assertIn("repairMetricGrid", html)
        self.assertIn("repairLatest", html)
        self.assertIn("buildRepairMetrics", app)
        self.assertIn("renderRepairs", app)
        self.assertIn(".repair-layout", css)

    def test_stage12_report_and_project_record_exist(self):
        report = DOCS / "Stage 12 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十二阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 12", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
