import json
import sqlite3
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
EXPORTS = ROOT / "monitoring" / "exports"
DB_PATH = ROOT / "monitoring" / "metacode_monitor.db"


class Stage13RepairEventsTest(unittest.TestCase):
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

    def test_status_endpoint_reports_stage13_api(self):
        payload = self.get_json("/api/status")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["version"], "stage13")
        self.assertGreaterEqual(payload["current_stage"], 13)
        self.assertIn("repair_event_count", payload["summary"])

    def test_monitoring_bundle_contains_repair_events(self):
        payload = self.get_json("/api/monitoring")

        self.assertIn("repairEvents", payload)
        self.assertIn("summary", payload["repairEvents"])
        self.assertIn("events", payload["repairEvents"])
        self.assertIn("/api/repair-events/summary", payload["api"]["endpoints"])
        self.assertIn("/api/repair-events/recent", payload["api"]["endpoints"])

    def test_repair_event_endpoints_are_readable(self):
        summary = self.get_json("/api/repair-events/summary")
        events = self.get_json("/api/repair-events?limit=3")
        by_strategy = self.get_json("/api/repair-events/by-strategy")
        by_workflow = self.get_json("/api/repair-events/by-workflow")
        recent = self.get_json("/api/repair-events/recent")

        self.assertGreater(summary["event_count"], 0)
        self.assertEqual(summary["event_count"], summary["closed_success_count"] + summary["closed_failed_count"])
        self.assertEqual(summary["event_count"], summary["linked_event_count"] + summary["unlinked_event_count"])
        self.assertLessEqual(len(events), 3)
        self.assertTrue(by_strategy)
        self.assertTrue(by_workflow)
        self.assertTrue(recent)

    def test_repair_event_has_full_chain_fields(self):
        events = self.get_json("/api/repair-events?limit=1")
        event = events[0]

        self.assertIn("repair_id", event)
        self.assertEqual(event["failure_link_status"], "linked")
        self.assertEqual(event["event_status"], "closed_success")
        self.assertTrue(event["failure_run_id"])
        self.assertTrue(event["verification_run_id"])
        self.assertTrue(event["generated_workflow_id"])
        self.assertTrue(event["suggested_metacodes"])
        self.assertIn("failure", event)

    def test_repair_event_rows_are_sorted_by_count(self):
        by_workflow = self.get_json("/api/repair-events/by-workflow")

        self.assertEqual(
            [row["event_count"] for row in by_workflow],
            sorted([row["event_count"] for row in by_workflow], reverse=True),
        )

    def test_repair_events_export_and_sqlite_table_exist(self):
        export_path = EXPORTS / "repair_events.json"
        self.assertTrue(export_path.exists())
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        self.assertGreater(payload["summary"]["event_count"], 0)

        with sqlite3.connect(DB_PATH) as conn:
            table_count = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='repair_events'"
            ).fetchone()[0]
            event_count = conn.execute("SELECT count(*) FROM repair_events").fetchone()[0]

        self.assertEqual(table_count, 1)
        self.assertEqual(event_count, payload["summary"]["event_count"])

    def test_dashboard_contains_repair_event_chain_section(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")
        css = (DASHBOARD / "styles.css").read_text(encoding="utf-8")

        self.assertIn('id="repair-events"', html)
        self.assertIn("repairEventMetricGrid", html)
        self.assertIn("repairEventLatest", html)
        self.assertIn("buildRepairEvents", app)
        self.assertIn("renderRepairEvents", app)
        self.assertIn(".event-layout", css)
        self.assertIn(".event-chain", css)

    def test_stage13_report_and_project_record_exist(self):
        report = DOCS / "Stage 13 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertIn("第十三阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 13", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
