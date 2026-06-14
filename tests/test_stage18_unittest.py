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


class Stage18CapabilityQualityTest(unittest.TestCase):
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

    def test_capability_quality_export_contains_scores(self):
        payload = json.loads((EXPORTS / "capability_quality.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["summary"]["metacode_count"], 15)
        self.assertGreater(payload["summary"]["scored_count"], 0)
        self.assertGreater(payload["summary"]["repair_contributor_count"], 0)
        self.assertIn("top_metacode", payload["summary"])
        self.assertEqual(len(payload["records"]), payload["summary"]["metacode_count"])
        self.assertGreaterEqual(payload["records"][0]["quality_score"], payload["records"][-1]["quality_score"])

    def test_capability_quality_api_endpoints_are_readable(self):
        monitoring = self.get_json("/api/monitoring")
        summary = self.get_json("/api/capability-quality/summary")
        records = self.get_json("/api/capability-quality")

        self.assertIn("capabilityQuality", monitoring)
        self.assertIn("/api/capability-quality", monitoring["api"]["endpoints"])
        self.assertEqual(summary["metacode_count"], len(records))
        self.assertGreater(summary["scored_count"], 0)

    def test_dashboard_contains_capability_quality_section(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="quality"', html)
        self.assertIn("qualityMetricGrid", html)
        self.assertIn("qualityList", html)
        self.assertIn("capability_quality.json", app)
        self.assertIn("renderCapabilityQuality", app)

    def test_stage18_report_and_project_record_exist(self):
        report = DOCS / "Stage 18 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十八阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 18", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
