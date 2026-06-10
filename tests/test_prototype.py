from pathlib import Path

from core.combiner import execute_workflow
from core.context import create_context, has_path, write_path
from core.registry import build_registry


ROOT = Path(__file__).resolve().parents[1]


def test_context_path_helpers():
    context = create_context({"file_path": "examples/sample_note.md"})
    assert has_path(context, "inputs.file_path")
    write_path(context, "data.raw_text", "hello")
    assert has_path(context, "data.raw_text")


def test_registry_builds_with_expected_metacodes():
    registry = build_registry(ROOT)
    assert "io.read_markdown_file" in registry
    assert "text.clean_text_basic" in registry
    assert "io.write_markdown" in registry
    assert len(registry) >= 7


def test_note_to_summary_workflow_succeeds():
    result = execute_workflow(ROOT, ROOT / "workflows" / "note_to_summary.yaml")
    assert result["status"] == "success"
    assert has_path(result["context"], "data.summary")
    output_file = Path(result["context"]["artifacts"]["output_file"])
    assert output_file.exists()


def test_note_health_report_workflow_succeeds():
    result = execute_workflow(ROOT, ROOT / "workflows" / "note_health_report.yaml")
    assert result["status"] == "success"
    assert has_path(result["context"], "data.text_stats")
    assert result["context"]["data"]["text_stats"]["headings"] >= 3


def test_broken_workflow_reports_missing_clean_text():
    result = execute_workflow(ROOT, ROOT / "workflows" / "broken_missing_clean_text.yaml")
    assert result["status"] == "failed"
    assert "data.clean_text" in result["reason"]
    assert "text.simple_summary" in result["reason"]
