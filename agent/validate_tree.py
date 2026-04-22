"""Validate the deterministic reflection tree TSV."""

from __future__ import annotations

import csv
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = {"id", "parentId", "type", "text", "options", "target", "signal"}
VALID_TYPES = {"start", "question", "decision", "reflection", "bridge", "summary", "end"}
NULL_PARENT = {"", "null", "None", "NULL"}


@dataclass(frozen=True)
class Node:
    id: str
    parent_id: str
    type: str
    text: str
    options: str
    target: str
    signal: str


def load_nodes(path: Path) -> list[Node]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError("TSV is empty or missing a header row")

        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")

        nodes: list[Node] = []
        for line_number, row in enumerate(reader, start=2):
            node_id = (row.get("id") or "").strip()
            if not node_id:
                raise ValueError(f"line {line_number}: id is required")
            nodes.append(
                Node(
                    id=node_id,
                    parent_id=(row.get("parentId") or "").strip(),
                    type=(row.get("type") or "").strip(),
                    text=(row.get("text") or "").strip(),
                    options=(row.get("options") or "").strip(),
                    target=(row.get("target") or "").strip(),
                    signal=(row.get("signal") or "").strip(),
                )
            )
    return nodes


def parse_decision_targets(options: str) -> list[str]:
    targets: list[str] = []
    for rule in [part.strip() for part in options.split(";") if part.strip()]:
        if ":" not in rule:
            raise ValueError(f"decision rule is missing target separator ':': {rule}")
        _, target = rule.rsplit(":", maxsplit=1)
        targets.append(target.strip())
    return targets


def validate(nodes: list[Node]) -> list[str]:
    warnings: list[str] = []
    errors: list[str] = []
    ids: dict[str, Node] = {}
    children: dict[str, list[str]] = defaultdict(list)

    for node in nodes:
        if node.id in ids:
            errors.append(f"duplicate id: {node.id}")
        ids[node.id] = node

        if node.type not in VALID_TYPES:
            errors.append(f"{node.id}: invalid type '{node.type}'")

        if node.parent_id not in NULL_PARENT:
            children[node.parent_id].append(node.id)

        if node.type == "question" and not node.options:
            errors.append(f"{node.id}: question nodes must define fixed options")

        if node.type == "decision" and not node.options:
            errors.append(f"{node.id}: decision nodes must define routing rules")

        if node.type == "bridge" and not node.target:
            errors.append(f"{node.id}: bridge nodes must define a target")

        if node.signal and ":" not in node.signal:
            errors.append(f"{node.id}: signal must use axis:pole format")

    for node in nodes:
        if node.parent_id not in NULL_PARENT and node.parent_id not in ids:
            errors.append(f"{node.id}: parentId '{node.parent_id}' does not exist")
        if node.target and node.target not in ids:
            errors.append(f"{node.id}: target '{node.target}' does not exist")
        if node.type == "decision":
            try:
                targets = parse_decision_targets(node.options)
            except ValueError as exc:
                errors.append(f"{node.id}: {exc}")
                targets = []
            for target in targets:
                if target not in ids:
                    errors.append(f"{node.id}: decision target '{target}' does not exist")

    root_ids = [node.id for node in nodes if node.parent_id in NULL_PARENT]
    if "START" not in ids:
        errors.append("missing START node")
    elif "START" not in root_ids:
        errors.append("START must be a root node")
    if not any(node.type == "end" for node in nodes):
        errors.append("missing end node")

    if len(nodes) < 50:
        warnings.append(f"tree has {len(nodes)} nodes; assignment asked for 50+")

    if errors:
        raise ValueError("\n".join(errors))

    reachable = reachable_ids(ids, children)
    unreachable = sorted(set(ids).difference(reachable))
    if unreachable:
        warnings.append("unreachable nodes: " + ", ".join(unreachable))

    dead_ends = []
    for node_id in reachable:
        node = ids[node_id]
        if node.type != "end" and not outgoing_ids(node, children):
            dead_ends.append(node_id)
    if dead_ends:
        warnings.append("reachable non-end nodes with no outgoing path: " + ", ".join(sorted(dead_ends)))

    if not any(ids[node_id].type == "end" for node_id in reachable):
        raise ValueError("no end node is reachable from START")

    return warnings


def outgoing_ids(node: Node, children: dict[str, list[str]]) -> list[str]:
    if node.target:
        return [node.target]
    if node.type == "decision":
        return parse_decision_targets(node.options)
    return children.get(node.id, [])


def reachable_ids(ids: dict[str, Node], children: dict[str, list[str]]) -> set[str]:
    seen: set[str] = set()
    queue: deque[str] = deque(["START"])
    while queue:
        node_id = queue.popleft()
        if node_id in seen:
            continue
        seen.add(node_id)
        node = ids[node_id]
        for next_id in outgoing_ids(node, children):
            if next_id in ids and next_id not in seen:
                queue.append(next_id)
    return seen


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python agent/validate_tree.py tree/reflection-tree.tsv", file=sys.stderr)
        return 2

    path = Path(argv[1])
    try:
        nodes = load_nodes(path)
        warnings = validate(nodes)
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {path} contains {len(nodes)} valid nodes.")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

