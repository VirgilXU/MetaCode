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
EXPERIMENTS = ROOT / "experiments"


class Stage16ComparisonExperimentTest(unittest.TestCase):
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

    def test_comparison_records_source_exists(self):
        source = EXPERIMENTS / "comparison_records.json"
        payload = json.loads(source.read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(payload["records"]), 2)
        self.assertIn("metacode", payload["records"][0])
        self.assertIn("traditional_ai", payload["records"][0])
        self.assertIn("result", payload["records"][0])

    def test_comparison_export_contains_summary_and_records(self):
        export_path = EXPORTS / "comparison_experiments.json"
        payload = json.loads(export_path.read_text(encoding="utf-8"))

        self.assertGreaterEqual(payload["summary"]["experiment_count"], 2)
        self.assertGreaterEqual(payload["summary"]["metacode_win_count"], 1)
        self.assertGreater(payload["summary"]["total_time_saved_minutes"], 0)
        self.assertEqual(payload["summary"]["experiment_count"], len(payload["records"]))

    def test_comparison_api_endpoints_are_readable(self):
        monitoring = self.get_json("/api/monitoring")
        summary = self.get_json("/api/comparison-experiments/summary")
        records = self.get_json("/api/comparison-experiments")

        self.assertIn("comparison", monitoring)
        self.assertIn("/api/comparison-experiments", monitoring["api"]["endpoints"])
        self.assertGreaterEqual(summary["experiment_count"], 2)
        self.assertEqual(summary["experiment_count"], len(records))

    def test_dashboard_contains_comparison_recorder_ui(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")

        self.assertIn("对比实验", html)
        self.assertIn("comparison_experiments.json", app)
        self.assertIn("state.data.comparison", app)
        self.assertIn("实验摘要", app)

    def test_stage16_report_and_project_record_exist(self):
        report = DOCS / "Stage 16 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十六阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 16", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
