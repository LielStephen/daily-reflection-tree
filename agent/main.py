"""CLI runner for the deterministic daily reflection tree."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


NULL_PARENT = {"", "null", "None", "NULL"}
AXIS_ORDER = {
    "axis1": ["internal", "external"],
    "axis2": ["contribution", "entitlement"],
    "axis3": ["altro", "self"],
}
SUMMARY_LINES = {
    ("internal", "contribution", "altro"): "keep turning pressure into clear, useful action for other people.",
    ("internal", "contribution", "self"): "you had agency and contribution; tomorrow, widen the frame one step sooner.",
    ("internal", "entitlement", "altro"): "convert the need you noticed into a clear ask, then pair it with one helpful action.",
    ("internal", "entitlement", "self"): "name the ask directly, then choose one controllable next move.",
    ("external", "contribution", "altro"): "you can respect what was outside your control and still keep contributing usefully.",
    ("external", "contribution", "self"): "protect your energy, then pick one small action that helps the team too.",
    ("external", "entitlement", "altro"): "fairness matters; make the need specific and keep the shared mission visible.",
    ("external", "entitlement", "self"): "start tomorrow by separating what happened from the one thing you can steer.",
}


@dataclass(frozen=True)
class Node:
    id: str
    parent_id: str
    type: str
    text: str
    options: str
    target: str
    signal: str


class ReflectionRunner:
    def __init__(self, nodes: list[Node]) -> None:
        self.nodes = {node.id: node for node in nodes}
        self.children: dict[str, list[str]] = defaultdict(list)
        for node in nodes:
            if node.parent_id not in NULL_PARENT:
                self.children[node.parent_id].append(node.id)

        self.answers: dict[str, str] = {}
        self.last_answer = ""
        self.signals: dict[str, Counter[str]] = defaultdict(Counter)

    def run(self) -> None:
        current_id = "START"
        visited_steps = 0
        while current_id:
            visited_steps += 1
            if visited_steps > 500:
                raise RuntimeError("stopped after 500 steps; possible cycle in tree")
            node = self.nodes[current_id]
            self.tally(node)

            if node.type == "decision":
                current_id = self.route_decision(node)
                continue

            text = self.interpolate(node.text)
            if text:
                print(text)

            if node.type == "question":
                answer = self.ask(node)
                self.answers[node.id] = answer
                self.last_answer = answer
                current_id = self.next_id(node)
                print()
            elif node.type == "end":
                break
            else:
                current_id = self.next_id(node)
                if current_id:
                    print()

    def tally(self, node: Node) -> None:
        if not node.signal:
            return
        axis, pole = node.signal.split(":", maxsplit=1)
        self.signals[axis.strip()][pole.strip()] += 1

    def ask(self, node: Node) -> str:
        options = [part.strip() for part in node.options.split("|") if part.strip()]
        for index, option in enumerate(options, start=1):
            print(f"  {index}. {option}")

        while True:
            try:
                raw = input(f"Choose 1-{len(options)}: ").strip()
            except EOFError:
                raw = "1"

            if not raw:
                raw = "1"
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                answer = options[int(raw) - 1]
                print(f"> {answer}")
                return answer
            print(f"Please enter a number from 1 to {len(options)}.")

    def route_decision(self, node: Node) -> str:
        rules = [part.strip() for part in node.options.split(";") if part.strip()]
        fallback = ""
        for rule in rules:
            condition, target = rule.rsplit(":", maxsplit=1)
            target = target.strip()
            fallback = fallback or target

            key, value = condition.split("=", maxsplit=1)
            key = key.strip()
            values = {part.strip() for part in value.split("|") if part.strip()}

            if key == "answer" and self.last_answer in values:
                return target
            if key == "dominant" and self.dominant_for_node(node.id) in values:
                return target

        if fallback:
            return fallback
        raise RuntimeError(f"{node.id}: no routing rule matched and no fallback exists")

    def dominant_for_node(self, node_id: str) -> str:
        if node_id.startswith("A1_"):
            return self.dominant("axis1")
        if node_id.startswith("A2_"):
            return self.dominant("axis2")
        if node_id.startswith("A3_"):
            return self.dominant("axis3")
        return ""

    def dominant(self, axis: str) -> str:
        counts = self.signals[axis]
        if not counts:
            return "unclear"
        order = AXIS_ORDER.get(axis, sorted(counts))
        return max(order, key=lambda pole: (counts[pole], -order.index(pole)))

    def next_id(self, node: Node) -> str:
        if node.target:
            return node.target
        children = self.children.get(node.id, [])
        return children[0] if children else ""

    def interpolate(self, text: str) -> str:
        if not text:
            return text

        def replace(match: re.Match[str]) -> str:
            token = match.group(1)
            if token.endswith(".answer"):
                return self.answers.get(token.removesuffix(".answer"), "")
            if token.endswith(".dominant"):
                return self.dominant(token.removesuffix(".dominant"))
            if token == "summary_reflection":
                key = (
                    self.dominant("axis1"),
                    self.dominant("axis2"),
                    self.dominant("axis3"),
                )
                return SUMMARY_LINES.get(key, "choose one specific action you can repeat tomorrow.")
            return match.group(0)

        return re.sub(r"\{([^{}]+)\}", replace, text)


def load_nodes(path: Path) -> list[Node]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [
            Node(
                id=(row.get("id") or "").strip(),
                parent_id=(row.get("parentId") or "").strip(),
                type=(row.get("type") or "").strip(),
                text=(row.get("text") or "").strip(),
                options=(row.get("options") or "").strip(),
                target=(row.get("target") or "").strip(),
                signal=(row.get("signal") or "").strip(),
            )
            for row in reader
        ]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python agent/main.py tree/reflection-tree.tsv", file=sys.stderr)
        return 2

    try:
        ReflectionRunner(load_nodes(Path(argv[1]))).run()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

