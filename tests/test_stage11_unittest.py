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


class Stage11DiagnosticsWorkbenchTest(unittest.TestCase):
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

    def test_status_endpoint_reports_stage11_api(self):
        payload = self.get_json("/api/status")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["version"], "stage11")
        self.assertGreaterEqual(payload["current_stage"], 11)

    def test_monitoring_bundle_contains_diagnostics(self):
        payload = self.get_json("/api/monitoring")

        self.assertIn("diagnostics", payload)
        self.assertIn("summary", payload["diagnostics"])
        self.assertIn("/api/diagnostics/summary", payload["api"]["endpoints"])
        self.assertIn("/api/diagnostics/by-field", payload["api"]["endpoints"])

    def test_diagnostics_endpoints_are_readable(self):
        summary = self.get_json("/api/diagnostics/summary")
        by_field = self.get_json("/api/diagnostics/by-field")
        by_workflow = self.get_json("/api/diagnostics/by-workflow")
        by_metacode = self.get_json("/api/diagnostics/by-metacode")

        self.assertGreater(summary["failure_count"], 0)
        self.assertGreaterEqual(summary["unique_missing_field_count"], 1)
        self.assertGreaterEqual(summary["suggestion_count"], summary["ready_suggestion_count"])
        self.assertTrue(by_field)
        self.assertTrue(by_workflow)
        self.assertTrue(by_metacode)
        self.assertIn("field", by_field[0])
        self.assertIn("workflow_id", by_workflow[0])
        self.assertIn("metacode_id", by_metacode[0])

    def test_diagnostics_rows_are_sorted_by_frequency(self):
        by_field = self.get_json("/api/diagnostics/by-field")
        by_workflow = self.get_json("/api/diagnostics/by-workflow")

        self.assertEqual(
            [row["failure_count"] for row in by_field],
            sorted([row["failure_count"] for row in by_field], reverse=True),
        )
        self.assertEqual(
            [row["failure_count"] for row in by_workflow],
            sorted([row["failure_count"] for row in by_workflow], reverse=True),
        )

    def test_dashboard_contains_diagnostics_workbench(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")
        css = (DASHBOARD / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="diagnostics"', html)
        self.assertIn("diagnosticMetricGrid", html)
        self.assertIn("renderDiagnostics", app)
        self.assertIn("buildDiagnostics", app)
        self.assertIn(".diagnostic-layout", css)

    def test_stage11_report_and_project_record_exist(self):
        report = DOCS / "Stage 11 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十一阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 11", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
