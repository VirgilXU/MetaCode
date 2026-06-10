import unittest
from pathlib import Path

import yaml

from core.combiner import execute_workflow
from core.context import create_context
from core.path_planner import plan_missing_fields, plan_workflow_fix
from core.registry import build_registry


ROOT = Path(__file__).resolve().parents[1]
BROKEN_CHAIN = ROOT / "workflows" / "broken_missing_summary_chain.yaml"
PLANNED_CHAIN = ROOT / "workflows" / "generated" / "broken_missing_summary_chain.planned.yaml"


class Stage5PathPlannerTest(unittest.TestCase):
    def setUp(self):
        if PLANNED_CHAIN.exists():
            PLANNED_CHAIN.unlink()

    def test_path_planner_finds_two_step_chain(self):
        registry = build_registry(ROOT)
        context = create_context({"file_path": "examples/sample_note.md"})

        result = plan_missing_fields(
            registry,
            context,
            ["data.clean_text"],
            blocked_ids={"text.simple_summary"},
        )

        self.assertEqual(result["status"], "planned", result)
        self.assertEqual(result["plan"], ["io.read_markdown_file", "text.clean_text_basic"])

    def test_plan_workflow_fix_generates_planned_yaml(self):
        result = plan_workflow_fix(ROOT, BROKEN_CHAIN)

        self.assertEqual(result["status"], "planned", result)
        self.assertEqual(result["failed_step"], "text.simple_summary")
        self.assertEqual(result["inserted"], ["io.read_markdown_file", "text.clean_text_basic"])
        self.assertTrue(PLANNED_CHAIN.exists())

    def test_planned_workflow_has_expected_step_order(self):
        plan_workflow_fix(ROOT, BROKEN_CHAIN)

        with PLANNED_CHAIN.open("r", encoding="utf-8") as handle:
            planned = yaml.safe_load(handle)

        self.assertEqual(
            planned["steps"],
            [
                "io.read_markdown_file",
                "text.clean_text_basic",
                "text.simple_summary",
                "io.write_markdown",
            ],
        )
        self.assertEqual(planned["planned_from"], "broken_missing_summary_chain")
        self.assertEqual(planned["inserted_steps"], ["io.read_markdown_file", "text.clean_text_basic"])

    def test_planned_workflow_runs_successfully(self):
        plan_workflow_fix(ROOT, BROKEN_CHAIN)

        result = execute_workflow(ROOT, PLANNED_CHAIN)

        self.assertEqual(result["status"], "success", result.get("reason"))
        self.assertIn("summary", result["context"]["data"])
        self.assertTrue(Path(result["context"]["artifacts"]["output_file"]).exists())

    def test_path_planner_reports_unresolved_field(self):
        registry = build_registry(ROOT)
        context = create_context({})

        result = plan_missing_fields(registry, context, ["data.nonexistent"])

        self.assertEqual(result["status"], "not_planned")
        self.assertEqual(result["unresolved"], ["data.nonexistent"])


if __name__ == "__main__":
    unittest.main()
