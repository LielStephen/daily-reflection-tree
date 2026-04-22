# Daily Reflection Tree (Deterministic)

This repo contains a deterministic end-of-day reflection tool built as a decision tree (no LLM at runtime), plus a small CLI agent that walks the tree.

## Repo structure

- `tree/reflection-tree.tsv` — **the product**: readable tree data (nodes, options, routing rules, signals)
- `tree/tree-diagram.md` — Mermaid diagram of the main structure
- `agent/main.py` — CLI runner (loads TSV, walks nodes, records state, computes axis dominants, interpolates text)
- `agent/validate_tree.py` — quick validator (IDs, parents, routing targets, reachability)
- `transcripts/` — two sample runs
- `write-up.md` — design rationale (≤ ~2 pages)

## Run (Python)

From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r agent/requirements.txt

python agent/validate_tree.py tree/reflection-tree.tsv
python agent/main.py tree/reflection-tree.tsv
```

## How the TSV works

Columns:

- `id` — unique node identifier
- `parentId` — parent node ID (`null` for root-level nodes)
- `type` — `start | question | decision | reflection | bridge | summary | end`
- `text` — text shown to user; supports `{NODE_ID.answer}` interpolation + summary variables like `{axis1.dominant}`
- `options` — for `question`: pipe-separated fixed options
  - for `decision`: routing rules (not user-visible) using `answer=...:TARGET` or `dominant=...:TARGET`
- `target` — explicit jump target (used for `bridge`)
- `signal` — optional tally tag like `axis1:internal` or `axis2:entitlement`

Decision routing rules are evaluated left-to-right; the first match wins.

---

**Constraint compliance:** No free text input, no LLM calls at runtime, fully deterministic paths.