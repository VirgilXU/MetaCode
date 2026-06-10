from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from core.registry import build_registry


SKIP_WORKFLOWS = {
    "broken_missing_clean_text.yaml",
    "broken_missing_summary_chain.yaml",
}


def load_stable_workflows(root: Path) -> list[dict[str, Any]]:
    workflows = []
    for workflow_path in sorted((root / "workflows").glob("*.yaml")):
        if workflow_path.name in SKIP_WORKFLOWS:
            continue
        with workflow_path.open("r", encoding="utf-8") as handle:
            workflow = yaml.safe_load(handle) or {}
        workflow["_path"] = str(workflow_path)
        workflows.append(workflow)
    return workflows


def workflow_usage(workflows: list[dict[str, Any]]) -> Counter:
    usage = Counter()
    for workflow in workflows:
        usage.update(workflow.get("steps", []))
    return usage


def build_capability_graph(root: Path) -> dict[str, Any]:
    registry = build_registry(root)
    workflows = load_stable_workflows(root)
    usage = workflow_usage(workflows)

    field_producers: dict[str, list[str]] = defaultdict(list)
    field_consumers: dict[str, list[str]] = defaultdict(list)
    nodes: dict[str, dict[str, Any]] = {}

    for metacode_id, identity in registry.items():
        reads = list(identity.get("context_read", []))
        writes = list(identity.get("context_write", []))
        nodes[metacode_id] = {
            "id": metacode_id,
            "category": identity.get("category", ""),
            "reads": reads,
            "writes": writes,
            "usage": usage.get(metacode_id, 0),
            "in_degree": 0,
            "out_degree": 0,
            "degree": 0,
            "bridge_score": 0,
        }
        for field in reads:
            field_consumers[field].append(metacode_id)
        for field in writes:
            field_producers[field].append(metacode_id)

    edges = []
    category_edges = Counter()
    for field, producers in field_producers.items():
        for producer in producers:
            for consumer in field_consumers.get(field, []):
                if producer == consumer:
                    continue
                edge = {
                    "from": producer,
                    "to": consumer,
                    "field": field,
                    "from_category": nodes[producer]["category"],
                    "to_category": nodes[consumer]["category"],
                }
                edges.append(edge)
                nodes[producer]["out_degree"] += 1
                nodes[consumer]["in_degree"] += 1
                category_edges[(edge["from_category"], edge["to_category"])] += 1

    for node in nodes.values():
        node["degree"] = node["in_degree"] + node["out_degree"]
        node["bridge_score"] = node["degree"] + node["usage"]

    input_only_fields = sorted(
        field
        for field in field_consumers
        if field not in field_producers and field.startswith("inputs.")
    )
    unresolved_fields = sorted(
        field
        for field in field_consumers
        if field not in field_producers and not field.startswith("inputs.")
    )
    orphan_outputs = sorted(field for field in field_producers if field not in field_consumers)

    core_nodes = sorted(
        nodes.values(),
        key=lambda node: (-node["usage"], -node["degree"], node["id"]),
    )[:5]
    bridge_nodes = sorted(
        nodes.values(),
        key=lambda node: (-node["bridge_score"], -node["out_degree"], node["id"]),
    )[:5]

    return {
        "metacode_count": len(registry),
        "workflow_count": len(workflows),
        "field_count": len(set(field_producers) | set(field_consumers)),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "field_producers": {field: sorted(ids) for field, ids in sorted(field_producers.items())},
        "field_consumers": {field: sorted(ids) for field, ids in sorted(field_consumers.items())},
        "category_edges": {
            f"{source}->{target}": count
            for (source, target), count in sorted(category_edges.items())
        },
        "input_only_fields": input_only_fields,
        "unresolved_fields": unresolved_fields,
        "orphan_outputs": orphan_outputs,
        "core_nodes": core_nodes,
        "bridge_nodes": bridge_nodes,
        "usage": dict(sorted(usage.items(), key=lambda item: (-item[1], item[0]))),
    }


def score_path(plan: list[str], graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph["nodes"]
    missing = [metacode_id for metacode_id in plan if metacode_id not in nodes]
    if missing:
        return {
            "status": "invalid",
            "missing_nodes": missing,
            "score": 0,
        }

    length_cost = len(plan)
    reuse_score = sum(nodes[metacode_id]["usage"] for metacode_id in plan)
    bridge_score = sum(nodes[metacode_id]["bridge_score"] for metacode_id in plan)
    score = reuse_score * 2 + bridge_score - length_cost * 3
    return {
        "status": "scored",
        "plan": plan,
        "length": length_cost,
        "reuse_score": reuse_score,
        "bridge_score": bridge_score,
        "score": score,
    }


def summarize_graph(root: Path) -> dict[str, Any]:
    graph = build_capability_graph(root)
    planned_chain_score = score_path(
        ["io.read_markdown_file", "text.clean_text_basic"],
        graph,
    )
    fixed_chain_score = score_path(["text.clean_text_basic"], graph)
    return {
        "metacode_count": graph["metacode_count"],
        "workflow_count": graph["workflow_count"],
        "field_count": graph["field_count"],
        "edge_count": graph["edge_count"],
        "input_only_fields": graph["input_only_fields"],
        "unresolved_fields": graph["unresolved_fields"],
        "orphan_outputs": graph["orphan_outputs"],
        "core_nodes": graph["core_nodes"],
        "bridge_nodes": graph["bridge_nodes"],
        "category_edges": graph["category_edges"],
        "planned_chain_score": planned_chain_score,
        "fixed_chain_score": fixed_chain_score,
    }
