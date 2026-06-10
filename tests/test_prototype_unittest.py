import unittest
from pathlib import Path

from core.combiner import execute_workflow
from core.context import create_context, has_path, write_path
from core.registry import build_registry


ROOT = Path(__file__).resolve().parents[1]


class PrototypeTest(unittest.TestCase):
    def test_context_path_helpers(self):
        context = create_context({"file_path": "examples/sample_note.md"})
        self.assertTrue(has_path(context, "inputs.file_path"))
        write_path(context, "data.raw_text", "hello")
        self.assertTrue(has_path(context, "data.raw_text"))

    def test_registry_builds_with_expected_metacodes(self):
        registry = build_registry(ROOT)
        self.assertIn("io.read_markdown_file", registry)
        self.assertIn("text.clean_text_basic", registry)
        self.assertIn("io.write_markdown", registry)
        self.assertGreaterEqual(len(registry), 7)

    def test_note_to_summary_workflow_succeeds(self):
        result = execute_workflow(ROOT, ROOT / "workflows" / "note_to_summary.yaml")
        self.assertEqual(result["status"], "success")
        self.assertTrue(has_path(result["context"], "data.summary"))
        output_file = Path(result["context"]["artifacts"]["output_file"])
        self.assertTrue(output_file.exists())

    def test_note_health_report_workflow_succeeds(self):
        result = execute_workflow(ROOT, ROOT / "workflows" / "note_health_report.yaml")
        self.assertEqual(result["status"], "success")
        self.assertTrue(has_path(result["context"], "data.text_stats"))
        self.assertGreaterEqual(result["context"]["data"]["text_stats"]["headings"], 3)

    def test_broken_workflow_reports_missing_clean_text(self):
        result = execute_workflow(ROOT, ROOT / "workflows" / "broken_missing_clean_text.yaml")
        self.assertEqual(result["status"], "failed")
        self.assertIn("data.clean_text", result["reason"])
        self.assertIn("text.simple_summary", result["reason"])


if __name__ == "__main__":
    unittest.main()
