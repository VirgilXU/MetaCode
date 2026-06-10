import unittest
from pathlib import Path

import yaml

from core.combiner import execute_workflow
from core.workflow_fixer import fix_workflow


ROOT = Path(__file__).resolve().parents[1]
BROKEN_WORKFLOW = ROOT / "workflows" / "broken_missing_clean_text.yaml"
FIXED_WORKFLOW = ROOT / "workflows" / "generated" / "broken_missing_clean_text.fixed.yaml"


class Stage4WorkflowFixerTest(unittest.TestCase):
    def setUp(self):
        if FIXED_WORKFLOW.exists():
            FIXED_WORKFLOW.unlink()

    def test_fix_workflow_generates_fixed_yaml(self):
        result = fix_workflow(ROOT, BROKEN_WORKFLOW)

        self.assertEqual(result["status"], "fixed", result)
        self.assertEqual(result["failed_step"], "text.simple_summary")
        self.assertEqual(result["inserted"], "text.clean_text_basic")
        self.assertTrue(FIXED_WORKFLOW.exists())

    def test_fixed_workflow_has_expected_step_order(self):
        fix_workflow(ROOT, BROKEN_WORKFLOW)

        with FIXED_WORKFLOW.open("r", encoding="utf-8") as handle:
            fixed = yaml.safe_load(handle)

        self.assertEqual(
            fixed["steps"],
            [
                "io.read_markdown_file",
                "text.clean_text_basic",
                "text.simple_summary",
            ],
        )
        self.assertEqual(fixed["fixed_from"], "broken_missing_clean_text")
        self.assertEqual(fixed["inserted_steps"], ["text.clean_text_basic"])

    def test_fixed_workflow_runs_successfully(self):
        fix_workflow(ROOT, BROKEN_WORKFLOW)

        result = execute_workflow(ROOT, FIXED_WORKFLOW)

        self.assertEqual(result["status"], "success", result.get("reason"))
        self.assertIn("data", result["context"])
        self.assertIn("summary", result["context"]["data"])

    def test_successful_workflow_does_not_need_fix(self):
        result = fix_workflow(ROOT, ROOT / "workflows" / "note_to_summary.yaml")

        self.assertEqual(result["status"], "not_needed")


if __name__ == "__main__":
    unittest.main()
