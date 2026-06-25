# Document Size Budgets

Harness artifacts solve cold-start confusion and weak handoff (see
`method-map.md`), but every artifact that grows unboundedly across sessions
becomes the next session's cold-start problem: a 3,500-word progress log is
no easier to "read first" than no progress log at all. This note adds a
budget to the failure mode method-map.md doesn't cover: **document bloat**.

## The Tiers

| Tier | What | Example files | Why this size |
| --- | --- | --- | --- |
| A — Operational pulse | Read every session, must stay skimmable | `claude-progress.md` (900w), `session-handoff.md` (300w), `clean-state-checklist.md` (150w) | If it takes longer to read than to re-derive, it has failed its purpose |
| B — Bounded record fields | Per-unit fields inside a larger file | `feature_list.json` `notes` (40w/feature), `evidence` (200w/feature) | One feature's history shouldn't crowd out the rest of the file |
| C — Standing reference | Read occasionally, sets durable rules | `AGENTS.md`/`CLAUDE.md` (700w), `docs/ARCHITECTURE.md`/`PRODUCT.md`/`RELIABILITY.md` (800w), `evaluator-rubric.md`/`quality-document.md` (500w), skill files (600w) | Instructions agents must hold in working memory every session |
| D — Per-feature design docs | One per feature, written once | `docs/PRD_*.md` (1200w) | Enough room for a real design discussion without becoming the implementation |
| E — User-facing guide | Comprehensive but still capped | `USER_GUIDE.md` (2000w) | Largest allowance; trim sections for superseded features instead of just appending |

The same tiers apply to this resource library itself: `resources/templates/*.md`
(1200w) and `resources/reference/*.md` (900w). `resources/openai-advanced/`
is excluded — it's an external reference pack this project doesn't generate
or maintain.

`scripts/check-doc-budgets.mjs` is the enforced source of truth for the
exact numbers; this table is the explanation. If they ever disagree, the
script wins — update it, not just this doc.

## The Reaudit Pipeline

Two parts, layered:

1. **Stop hook** (automatic): fires when a session ends, runs
   `node scripts/check-doc-budgets.mjs`, and prints a non-blocking warning
   listing any file over budget. It never edits anything — hooks run shell
   commands, not model calls, so compaction needs a model.
2. **`/reaudit-harness` skill** (the actual compaction): spawns a low-cost
   model subagent (same Haiku-via-subagent pattern as `/discuss`) to rewrite
   each over-budget file more concisely. The skill must preserve every fact
   that proves a feature's status (evidence, blockers, verification
   results) — it may compact narrative and prose, but it must never delete
   or soften proof, per the existing "do not hide unfinished work" rule.

Run `/reaudit-harness` as part of "Before You Stop," not mid-feature — it
should never compete with the active feature for attention.

## Why a Budget, Not Just "Be Concise"

"Be concise" is unenforceable and the first instruction an agent drops under
pressure to document thoroughly. A number is checkable by a script, and a
script is what makes the Stop hook possible at all.
