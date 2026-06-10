import unittest
from pathlib import Path

from core.combiner import execute_workflow
from core.context import create_context, write_path
from core.recommender import suggest_for_missing_fields
from core.registry import build_registry


ROOT = Path(__file__).resolve().parents[1]


class Stage3RecommendationTest(unittest.TestCase):
    def test_recommender_finds_ready_provider_for_clean_text(self):
        registry = build_registry(ROOT)
        context = create_context({"file_path": "examples/sample_note.md"})
        write_path(context, "data.raw_text", "raw markdown text")

        suggestions = suggest_for_missing_fields(registry, context, ["data.clean_text"])

        self.assertGreaterEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["metacode_id"], "text.clean_text_basic")
        self.assertTrue(suggestions[0]["ready"])
        self.assertEqual(suggestions[0]["provides"], ["data.clean_text"])

    def test_failed_workflow_returns_structured_suggestions(self):
        result = execute_workflow(ROOT, ROOT / "workflows" / "broken_missing_clean_text.yaml")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["missing_fields"], ["data.clean_text"])
        suggestion_ids = [item["metacode_id"] for item in result["suggestions"]]
        self.assertIn("text.clean_text_basic", suggestion_ids)
        first = result["suggestions"][0]
        self.assertEqual(first["metacode_id"], "text.clean_text_basic")
        self.assertTrue(first["ready"])

    def test_recommender_marks_candidate_not_ready_when_inputs_missing(self):
        registry = build_registry(ROOT)
        context = create_context({})

        suggestions = suggest_for_missing_fields(registry, context, ["data.clean_text"])

        self.assertGreaterEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["metacode_id"], "text.clean_text_basic")
        self.assertFalse(suggestions[0]["ready"])
        self.assertEqual(suggestions[0]["unmet_inputs"], ["data.raw_text"])


if __name__ == "__main__":
    unittest.main()
