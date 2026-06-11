import json
import unittest
from pathlib import Path

from core.monitoring_store import export_monitoring_data


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"
EXPORTS = ROOT / "monitoring" / "exports"
DOCS = ROOT / "docs"


class Stage9ObservatoryMvpTest(unittest.TestCase):
    def test_dashboard_has_monitoring_mvp_sections(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")

        for section_id in (
            "overview",
            "stages",
            "workflows",
            "failures",
            "graph",
            "comparison",
            "reports",
            "extensions",
        ):
            self.assertIn(f'id="{section_id}"', html)

    def test_dashboard_app_renders_stage9_modules(self):
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")

        self.assertIn("renderStageGates", app)
        self.assertIn("renderComparison", app)
        self.assertIn("renderReports", app)
        self.assertIn("renderExtensions", app)
        self.assertIn("comparisonItems", app)
        self.assertIn("extensionItems", app)

    def test_export_summary_contains_stage9_monitoring_metrics(self):
        export_monitoring_data(ROOT)

        with (EXPORTS / "dashboard_summary.json").open("r", encoding="utf-8") as handle:
            summary = json.load(handle)

        for key in (
            "stage_report_count",
            "stage_range",
            "stable_workflow_file_count",
            "generated_workflow_count",
            "intentional_failure_workflow_count",
            "success_rate",
            "last_exported_at",
        ):
            self.assertIn(key, summary)

        self.assertGreaterEqual(summary["current_stage"], 9)
        self.assertGreaterEqual(summary["stage_report_count"], 8)
        self.assertGreaterEqual(summary["generated_workflow_count"], 1)
        self.assertEqual(summary["unresolved_field_count"], 0)

    def test_stage9_report_and_project_record_exist(self):
        report = DOCS / "Stage 9 验证报告.md"
        record = DOCS / "项目进度记录.md"

        self.assertTrue(report.exists())
        self.assertTrue(record.exists())
        self.assertIn("第九阶段", report.read_text(encoding="utf-8"))
        self.assertIn("Stage 9", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
