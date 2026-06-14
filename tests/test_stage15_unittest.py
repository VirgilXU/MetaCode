import shutil
import tempfile
import unittest
from pathlib import Path

from core.monitoring_store import build_repair_events
from core.path_planner import plan_workflow_fix
from core.workflow_fixer import fix_workflow


ROOT = Path(__file__).resolve().parents[1]


def copy_isolated_project_root() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    isolated_root = Path(temp_dir.name)
    for folder in ("metacodes", "workflows", "examples"):
        shutil.copytree(ROOT / folder, isolated_root / folder)
    shutil.rmtree(isolated_root / "workflows" / "generated", ignore_errors=True)
    (isolated_root / "logs").mkdir(parents=True, exist_ok=True)
    return temp_dir


class Stage15IsolatedRepairEventTest(unittest.TestCase):
    def test_explicit_repair_id_binds_failure_and_verification_without_file_writes(self):
        runs = [
            {
                "run_id": "failure-1",
                "workflow_id": "broken_missing_clean_text",
                "status": "failed",
                "ended_at": "2026-06-12T10:00:00+08:00",
                "failed_step": "text.simple_summary",
                "missing_fields": ["text.cleaned"],
                "suggestions": [{"metacode_id": "text.clean_text_basic", "ready": True}],
                "repair_id": "repair-action-explicit",
                "repair_strategy": "fixed",
                "repair_source_workflow_id": "broken_missing_clean_text",
            },
            {
                "run_id": "verification-1",
                "workflow_id": "broken_missing_clean_text_fixed",
                "status": "success",
                "ended_at": "2026-06-12T10:00:01+08:00",
                "duration_ms": 12.5,
                "repair_id": "repair-action-explicit",
                "repair_strategy": "fixed",
                "repair_source_workflow_id": "broken_missing_clean_text",
            },
        ]
        workflows = [
            {
                "workflow_id": "broken_missing_clean_text_fixed",
                "status_type": "generated_fixed",
                "generated_from": "broken_missing_clean_text",
                "workflow_path": "workflows/generated/broken_missing_clean_text.fixed.yaml",
                "inserted_steps": ["text.clean_text_basic"],
            }
        ]

        repair_events = build_repair_events(runs, workflows)
        event = repair_events["events"][0]

        self.assertEqual(repair_events["summary"]["event_count"], 1)
        self.assertEqual(event["repair_id"], "repair-action-explicit")
        self.assertEqual(event["failure_run_id"], "failure-1")
        self.assertEqual(event["verification_run_id"], "verification-1")
        self.assertEqual(event["failure_link_status"], "linked")
        self.assertEqual(event["event_status"], "closed_success")

    def test_legacy_repair_event_inference_still_works_without_explicit_repair_id(self):
        runs = [
            {
                "run_id": "legacy-failure",
                "workflow_id": "broken_missing_summary_chain",
                "status": "failed",
                "ended_at": "2026-06-12T10:01:00+08:00",
                "failed_step": "text.simple_summary",
                "missing_fields": ["text.raw"],
                "suggestions": [{"metacode_id": "io.read_markdown_file", "ready": True}],
            },
            {
                "run_id": "legacy-verification",
                "workflow_id": "broken_missing_summary_chain_planned",
                "status": "success",
                "ended_at": "2026-06-12T10:01:01+08:00",
                "duration_ms": 22.0,
            },
        ]
        workflows = [
            {
                "workflow_id": "broken_missing_summary_chain_planned",
                "status_type": "generated_planned",
                "generated_from": "broken_missing_summary_chain",
                "workflow_path": "workflows/generated/broken_missing_summary_chain.planned.yaml",
                "inserted_steps": ["io.read_markdown_file", "text.clean_text_basic"],
            }
        ]

        repair_events = build_repair_events(runs, workflows)
        event = repair_events["events"][0]

        self.assertEqual(event["repair_id"], "repair-legacy-verification")
        self.assertEqual(event["failure_run_id"], "legacy-failure")
        self.assertEqual(event["strategy"], "planned")
        self.assertEqual(event["failure_link_status"], "linked")

    def test_fix_workflow_side_effects_stay_inside_isolated_project_root(self):
        run_log_size = (ROOT / "logs" / "run_log.jsonl").stat().st_size
        failure_log_size = (ROOT / "logs" / "failure_log.jsonl").stat().st_size

        with copy_isolated_project_root() as temp_root_name:
            temp_root = Path(temp_root_name)
            result = fix_workflow(
                temp_root,
                temp_root / "workflows" / "broken_missing_clean_text.yaml",
                repair_id="repair-action-isolated-fixed",
            )

            self.assertEqual(result["status"], "fixed")
            self.assertTrue((temp_root / "workflows" / "generated" / "broken_missing_clean_text.fixed.yaml").exists())
            self.assertTrue((temp_root / "logs" / "run_log.jsonl").exists())
            self.assertTrue((temp_root / "logs" / "failure_log.jsonl").exists())

        self.assertEqual((ROOT / "logs" / "run_log.jsonl").stat().st_size, run_log_size)
        self.assertEqual((ROOT / "logs" / "failure_log.jsonl").stat().st_size, failure_log_size)

    def test_plan_workflow_side_effects_stay_inside_isolated_project_root(self):
        run_log_size = (ROOT / "logs" / "run_log.jsonl").stat().st_size
        failure_log_size = (ROOT / "logs" / "failure_log.jsonl").stat().st_size

        with copy_isolated_project_root() as temp_root_name:
            temp_root = Path(temp_root_name)
            result = plan_workflow_fix(
                temp_root,
                temp_root / "workflows" / "broken_missing_summary_chain.yaml",
                repair_id="repair-action-isolated-planned",
            )

            self.assertEqual(result["status"], "planned")
            self.assertTrue(
                (temp_root / "workflows" / "generated" / "broken_missing_summary_chain.planned.yaml").exists()
            )
            self.assertTrue((temp_root / "logs" / "run_log.jsonl").exists())
            self.assertTrue((temp_root / "logs" / "failure_log.jsonl").exists())

        self.assertEqual((ROOT / "logs" / "run_log.jsonl").stat().st_size, run_log_size)
        self.assertEqual((ROOT / "logs" / "failure_log.jsonl").stat().st_size, failure_log_size)


if __name__ == "__main__":
    unittest.main()
