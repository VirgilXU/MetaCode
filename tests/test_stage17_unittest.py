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
REVIEWS = ROOT / "reviews"


class Stage17GeneratedWorkflowReviewTest(unittest.TestCase):
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

    def test_generated_workflow_review_source_exists(self):
        source = REVIEWS / "generated_workflow_reviews.json"
        payload = json.loads(source.read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(payload["reviews"]), 1)
        review = payload["reviews"][0]
        self.assertEqual(review["review_status"], "accepted")
        self.assertTrue(review["promotion_ready"])
        self.assertIn("generated_workflow_id", review)

    def test_generated_workflow_review_export_contains_summary_and_records(self):
        payload = json.loads((EXPORTS / "generated_workflow_reviews.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(payload["summary"]["generated_workflow_count"], 1)
        self.assertGreaterEqual(payload["summary"]["reviewed_count"], 1)
        self.assertGreaterEqual(payload["summary"]["promotion_ready_count"], 1)
        self.assertEqual(payload["summary"]["generated_workflow_count"], len(payload["records"]))

    def test_generated_workflow_review_api_endpoints_are_readable(self):
        monitoring = self.get_json("/api/monitoring")
        summary = self.get_json("/api/generated-workflow-reviews/summary")
        records = self.get_json("/api/generated-workflow-reviews")

        self.assertIn("generatedReviews", monitoring)
        self.assertIn("/api/generated-workflow-reviews", monitoring["api"]["endpoints"])
        self.assertGreaterEqual(summary["generated_workflow_count"], 1)
        self.assertEqual(summary["generated_workflow_count"], len(records))

    def test_dashboard_contains_generated_workflow_review_section(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="reviews"', html)
        self.assertIn("reviewMetricGrid", html)
        self.assertIn("reviewWorkflowList", html)
        self.assertIn("generated_workflow_reviews.json", app)
        self.assertIn("renderGeneratedReviews", app)

    def test_stage17_report_and_project_record_exist(self):
        report = DOCS / "Stage 17 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十七阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 17", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
