import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard"


class Stage8DashboardTest(unittest.TestCase):
    def test_dashboard_files_exist(self):
        self.assertTrue((DASHBOARD / "index.html").exists())
        self.assertTrue((DASHBOARD / "styles.css").exists())
        self.assertTrue((DASHBOARD / "app.js").exists())

    def test_dashboard_has_required_sections(self):
        html = (DASHBOARD / "index.html").read_text(encoding="utf-8")

        for section_id in ("overview", "workflows", "failures", "graph", "stages"):
            self.assertIn(f'id="{section_id}"', html)

    def test_dashboard_app_references_monitoring_exports(self):
        app = (DASHBOARD / "app.js").read_text(encoding="utf-8")

        self.assertIn("../monitoring/exports", app)
        self.assertIn("dashboard_summary.json", app)
        self.assertIn("workflow_graph.json", app)
        self.assertIn("capability_graph_summary.json", app)

    def test_dashboard_styles_include_responsive_layout(self):
        css = (DASHBOARD / "styles.css").read_text(encoding="utf-8")

        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn(".metric-grid", css)
        self.assertIn(".mini-graph", css)


if __name__ == "__main__":
    unittest.main()
