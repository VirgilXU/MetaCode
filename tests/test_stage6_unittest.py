import unittest
from pathlib import Path

from core.capability_graph import build_capability_graph, score_path, summarize_graph


ROOT = Path(__file__).resolve().parents[1]


class Stage6CapabilityGraphTest(unittest.TestCase):
    def test_capability_graph_builds_expected_shape(self):
        graph = build_capability_graph(ROOT)

        self.assertEqual(graph["metacode_count"], 15)
        self.assertEqual(graph["workflow_count"], 10)
        self.assertGreaterEqual(graph["edge_count"], 10)
        self.assertIn("data.raw_text", graph["field_producers"])
        self.assertIn("data.raw_text", graph["field_consumers"])
        self.assertEqual(graph["unresolved_fields"], [])

    def test_core_nodes_include_high_reuse_markdown_reader(self):
        summary = summarize_graph(ROOT)
        core_ids = [node["id"] for node in summary["core_nodes"]]

        self.assertIn("io.read_markdown_file", core_ids)
        self.assertIn("io.write_markdown", core_ids)

    def test_bridge_nodes_include_text_cleaner(self):
        summary = summarize_graph(ROOT)
        bridge_ids = [node["id"] for node in summary["bridge_nodes"]]

        self.assertIn("text.clean_text_basic", bridge_ids)

    def test_path_scoring_scores_valid_plan(self):
        graph = build_capability_graph(ROOT)
        result = score_path(["io.read_markdown_file", "text.clean_text_basic"], graph)

        self.assertEqual(result["status"], "scored")
        self.assertEqual(result["length"], 2)
        self.assertGreater(result["score"], 0)

    def test_path_scoring_rejects_unknown_node(self):
        graph = build_capability_graph(ROOT)
        result = score_path(["missing.metacode"], graph)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["missing_nodes"], ["missing.metacode"])


if __name__ == "__main__":
    unittest.main()
