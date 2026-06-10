import json
import sqlite3
import unittest
from pathlib import Path

from core.combiner import execute_workflow
from core.monitoring_store import export_monitoring_data


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "monitoring" / "exports"
DB_PATH = ROOT / "monitoring" / "metacode_monitor.db"


class Stage7MonitoringExportTest(unittest.TestCase):
    def test_execute_workflow_adds_run_id(self):
        result = execute_workflow(ROOT, ROOT / "workflows" / "note_to_summary.yaml")

        self.assertEqual(result["status"], "success")
        self.assertIn("run_id", result)
        self.assertIn("started_at", result)
        self.assertIn("ended_at", result)

    def test_export_monitoring_data_writes_json_exports(self):
        payload = export_monitoring_data(ROOT)

        self.assertTrue((EXPORTS / "dashboard_summary.json").exists())
        self.assertTrue((EXPORTS / "runs.json").exists())
        self.assertTrue((EXPORTS / "failures.json").exists())
        self.assertTrue((EXPORTS / "stages.json").exists())
        self.assertTrue((EXPORTS / "workflow_graph.json").exists())
        self.assertTrue((EXPORTS / "capability_graph.json").exists())
        self.assertTrue((EXPORTS / "reuse_summary.json").exists())
        self.assertEqual(payload["dashboard_summary"]["metacode_count"], 15)
        self.assertEqual(payload["dashboard_summary"]["stable_workflow_count"], 10)

    def test_dashboard_summary_is_frontend_readable(self):
        export_monitoring_data(ROOT)

        with (EXPORTS / "dashboard_summary.json").open("r", encoding="utf-8") as handle:
            summary = json.load(handle)

        self.assertGreaterEqual(summary["current_stage"], 6)
        self.assertEqual(summary["unresolved_field_count"], 0)
        self.assertGreaterEqual(summary["run_count"], 1)

    def test_sqlite_database_contains_monitoring_tables(self):
        export_monitoring_data(ROOT)

        self.assertTrue(DB_PATH.exists())
        conn = sqlite3.connect(DB_PATH)
        try:
            run_count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            workflow_count = conn.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
            stage_count = conn.execute("SELECT COUNT(*) FROM stages").fetchone()[0]
            metacode_count = conn.execute("SELECT COUNT(*) FROM metacodes").fetchone()[0]
            edge_count = conn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
        finally:
            conn.close()

        self.assertGreaterEqual(run_count, 1)
        self.assertGreaterEqual(workflow_count, 12)
        self.assertGreaterEqual(stage_count, 5)
        self.assertEqual(metacode_count, 15)
        self.assertGreaterEqual(edge_count, 10)

    def test_stage_json_exports_exist(self):
        export_monitoring_data(ROOT)

        self.assertTrue((ROOT / "monitoring" / "stages" / "stage_6.json").exists())


if __name__ == "__main__":
    unittest.main()
