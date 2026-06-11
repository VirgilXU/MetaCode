import json
import threading
import unittest
import urllib.parse
import urllib.request
from pathlib import Path

from core.monitoring_api import create_handler
from core.monitoring_store import export_monitoring_data
from http.server import ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
DOCS = ROOT / "docs"


class Stage10ApiServerTest(unittest.TestCase):
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

    def test_status_endpoint_reports_stage10(self):
        payload = self.get_json("/api/status")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["version"], "stage10")
        self.assertGreaterEqual(payload["current_stage"], 10)
        self.assertIn("summary", payload)

    def test_monitoring_bundle_contains_dashboard_sources(self):
        payload = self.get_json("/api/monitoring")

        for key in ("summary", "runs", "failures", "stages", "workflows", "reuse", "graph", "graphSummary"):
            self.assertIn(key, payload)
        self.assertEqual(payload["api"]["mode"], "api")
        self.assertIn("/api/runs", payload["api"]["endpoints"])

    def test_runs_endpoint_supports_filters(self):
        query = urllib.parse.urlencode({"limit": 3, "status": "success"})
        runs = self.get_json(f"/api/runs?{query}")

        self.assertLessEqual(len(runs), 3)
        self.assertTrue(all(run["status"] == "success" for run in runs))

    def test_failures_and_reports_endpoints_are_readable(self):
        failures = self.get_json("/api/failures?limit=2")
        reports = self.get_json("/api/reports")

        self.assertLessEqual(len(failures), 2)
        self.assertTrue(any(report["stage_id"] == 10 for report in reports))

    def test_dashboard_prefers_api_with_static_fallback(self):
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")

        self.assertIn("/api/monitoring", app)
        self.assertIn("../monitoring/exports", app)
        self.assertIn("startAutoRefresh", app)
        self.assertIn("renderApiStatus", app)
        self.assertIn('id="api"', html)
        self.assertIn('id="autoRefreshToggle"', html)

    def test_stage10_report_exists(self):
        report = DOCS / "Stage 10 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 10", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
