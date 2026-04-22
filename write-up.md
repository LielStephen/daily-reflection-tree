# Write-up (≤2 pages): Daily Reflection Tree

## What I built

I designed a **deterministic reflection decision tree** that guides an employee through three psychological axes in sequence:

1. **Axis 1 — Locus (Victim ↔ Victor):** external vs internal locus of control + growth mindset framing.
2. **Axis 2 — Orientation (Entitlement ↔ Contribution):** what I deserved vs what I gave.
3. **Axis 3 — Radius (Self-centrism ↔ Altrocentrism):** me vs us/customer/others.

The tree is shipped as data (`tree/reflection-tree.tsv`). A small CLI agent (bonus) loads the TSV and walks the user through questions with **fixed options**, branching deterministically based on answers and accumulated signals.

## Design choices (and why)

### 1) Conversational, not survey-like
I kept questions short and concrete, and placed brief reflections after each axis to avoid the “checkbox” feeling. The reflections are not moralizing; they validate the day and then gently widen perspective.

### 2) Options are “honest”, not leading
Each question has 3–5 options that a real tired employee could plausibly pick. I avoided “good vs bad” phrasing; instead, options differ by *frame* (agency vs circumstance, giving vs expecting, me vs others).

### 3) Branching strategy
I used a mix of:
- **answer-based branching** (immediate interpretation of a specific response), and
- **signal-based branching** (tally across multiple questions, then decide “dominant” pole per axis).

This supports determinism while reducing brittleness: a single answer won’t fully define the employee; the axis dominant is based on multiple signals.

### 4) Interpolation for personalization without generation
To keep the experience human, reflections reuse the user’s own words via `{NODE.answer}` placeholders (e.g., “You described today as ‘{A1_OPEN.answer}’…”). This produces a feeling of personalization without any LLM or free-text.

### 5) Transitions between axes
Bridges explicitly connect the axes:
- Agency (Axis 1) naturally invites “what did I do for others?” (Axis 2).
- Contribution (Axis 2) naturally expands concern beyond the self (Axis 3).

## Psychological grounding (high level)

- **Locus of Control (Rotter, 1954):** internal vs external explanations for outcomes.
- **Growth Mindset (Dweck, 2006):** shifting from fixed explanations to controllable strategies.
- **Psychological Entitlement (Campbell et al., 2004):** expectations of special treatment independent of contribution.
- **Organizational Citizenship Behavior (Organ, 1988):** discretionary actions that support others and the org.
- **Self-transcendence (Maslow, 1969):** meaning expands when the frame includes service beyond self.
- **Perspective-taking (Batson, 2011):** imagining others’ experiences.

## What I’d improve with more time

- Add a “repair loop” for conflict days (apology, clarification, re-commitment) with more nuanced branches.
- Add optional micro-actions at the end (still deterministic): 1 small agency action, 1 contribution action, 1 perspective action.
- Expand the tree with role-specific variants (IC vs manager) while keeping the same underlying axes.

---

The intent is a predictable, auditable, repeatable reflection experience that feels human through careful wording, not generative AI.