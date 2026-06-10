import unittest
from pathlib import Path

from analyze_reuse import analyze
from core.combiner import execute_workflow
from core.registry import build_registry


ROOT = Path(__file__).resolve().parents[1]
BROKEN = {
    "broken_missing_clean_text.yaml",
    "broken_missing_summary_chain.yaml",
}


class Stage2Test(unittest.TestCase):
    def test_registry_has_15_metacodes(self):
        registry = build_registry(ROOT)
        self.assertEqual(len(registry), 15)

    def test_all_success_workflows_run(self):
        workflow_paths = [
            path for path in sorted((ROOT / "workflows").glob("*.yaml")) if path.name not in BROKEN
        ]
        self.assertEqual(len(workflow_paths), 10)
        for workflow_path in workflow_paths:
            with self.subTest(workflow=workflow_path.name):
                result = execute_workflow(ROOT, workflow_path)
                self.assertEqual(result["status"], "success", result.get("reason"))

    def test_intentional_failure_still_fails_with_gap(self):
        result = execute_workflow(ROOT, ROOT / "workflows" / "broken_missing_clean_text.yaml")
        self.assertEqual(result["status"], "failed")
        self.assertIn("data.clean_text", result["reason"])

    def test_reuse_metrics_show_actual_reuse(self):
        result = analyze(ROOT)
        self.assertEqual(result["workflow_count"], 10)
        self.assertGreaterEqual(result["reused_metacode_count"], 8)
        self.assertGreaterEqual(result["usage"]["io.read_markdown_file"], 6)
        self.assertGreaterEqual(result["usage"]["io.read_json_file"], 4)


if __name__ == "__main__":
    unittest.main()
