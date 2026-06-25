# Project Harness Bootstrap Prompt

A comprehensive prompt for the **first session** in a new repository. Give
an agent a project description and this prompt; it returns a complete
operating harness instead of just feature code.

## How to use it

1. Copy the prompt block below into your agent's chat.
2. Replace `{{PROJECT_DESCRIPTION}}` with a few sentences — name the user,
   core action, and known constraints.
3. Replace `{{TECH_STACK}}` with your stack, or "agent's choice — propose
   one" to let it decide.
4. Send it. Review the generated `feature_list.json` and docs before continuing.

This produces the same artifact set used throughout this course (see
[index.md](./index.md) for other template guides).

---

## The Prompt

```
You are initializing a brand-new repository, before any incremental feature
work begins. Leave behind a stable operating surface so a future session
(you, another agent, or a human) can pick up this project having read only
the repository's own files, with no memory of this conversation.

PROJECT DESCRIPTION:
OmniDigest is a self-hosted AI assistant that aggregates unread emails
(IMAP/Gmail OAuth) and WhatsApp Web messages into a daily digest, viewed
through a web UI. The backend fetches messages, summarizes them via an LLM,
and pushes results live. Features: action-item extraction, calendar
integration, group-chat summaries, a customizable AI persona. Core UX:
connect accounts → sync & generate → view digest → search archives.

TECH STACK:
React + Vite + TypeScript frontend (Tailwind, shadcn/ui); Node.js + Express
backend (whatsapp-web.js, imapflow, Socket.io); SQLite + Prisma; an LLM SDK;
Docker for deployment.

Work through the following phases in order. Read the files in resources. Do not skip ahead to
implementation before Phase 4 is complete.

## Phase 1 -- Understand and decompose

1. Restate the project in your own words in one paragraph: who the user is,
   what they can do, and what "working" looks like from the outside.
2. If the tech stack was left to your judgment, propose one and give a
   one-line justification (favor boring, well-documented choices over novel
   ones unless the description demands otherwise).
3. Decompose the description into discrete, independently verifiable
   features. Each must be small enough to implement and verify in one
   sitting, and describe USER-VISIBLE behavior, not internal mechanism
   (e.g. "a user can import a .txt file and see it in the document list" --
   not "implement DocumentService.importDocument()").
4. Order features by priority: a thin vertical slice proving the whole
   stack is wired together comes first, before breadth or polish.
5. If scope, target platform, or success criteria are genuinely ambiguous
   and would change the architecture, ask one focused question first.
   Otherwise, make a reasonable assumption, write it down, and continue.

## Phase 2 -- Establish layer boundaries and conventions

Before any code, write down (and follow for the rest of the session):

- Module/layer boundaries for this stack (e.g. client-server: UI never
  imports server-only modules; CLI: command parsing never embeds business
  logic; Electron: renderer never imports Node.js core modules).
- Where cross-boundary contracts live (one types/interfaces module that is
  the single source of truth for data crossing boundaries).
- Naming/structure conventions: file layout, export style, error handling,
  state persistence.
- Logging conventions if applicable: structured (JSON) vs plain text, what
  counts as an event, and at what level.

## Phase 3 -- Create the harness artifacts

Create every file below, tailored to this specific project (do not leave
placeholder text -- fill in real commands, file paths, and feature names).

### Root files

1. **`AGENTS.md`** (and `CLAUDE.md` for Claude Code) -- root instruction
   file. Must include: a startup workflow (confirm directory, read progress
   log and feature list, check commits, run init script and baseline
   verification); working rules (one feature at a time, no marking done
   without evidence, stay in scope, never weaken verification); the layer
   boundaries from Phase 2; a Definition of Done (implemented, verified,
   evidence recorded, repo restartable); and an end-of-session checklist
   (update progress log and feature list, record blockers, commit, leave a
   clean restart path).

2. **`feature_list.json`** -- machine-readable feature tracker. Schema:
   ```json
   {
     "project": "<project-name>",
     "last_updated": "<ISO date>",
     "rules": {
       "single_active_feature": true,
       "passing_requires_evidence": true,
       "do_not_skip_verification": true
     },
     "status_legend": {
       "not_started": "Work has not begun.",
       "in_progress": "The feature is the current active task.",
       "blocked": "Work cannot continue until a documented blocker is resolved.",
       "passing": "Required verification has passed and evidence is recorded."
     },
     "features": [
       {
         "id": "<area>-<number>",
         "priority": 1,
         "area": "<feature area>",
         "title": "<short title>",
         "user_visible_behavior": "<what the user sees when it works>",
         "status": "not_started",
         "verification": ["<step 1>", "<step 2>"],
         "evidence": [],
         "notes": ""
       }
     ]
   }
   ```
   Populate with every feature from Phase 1. All features start at
   `status: "not_started"` with empty `evidence`.

3. **`claude-progress.md`** -- durable session log: "Current Verified
   State" (repo root, startup/verification commands, active feature,
   blocker) plus a "Session Log" with dated entries (goal, completion,
   verification, evidence, commits, next step).

4. **`init.sh`** -- startup/verification script: prints working directory,
   installs dependencies, runs verification, prints (or runs, if
   `RUN_START_COMMAND=1`) the app launch command. Failure blocks all
   feature work.

5. **`session-handoff.md`** -- compact continuity note: verified now,
   changed this session, broken/unverified, next best step. Keep brief.

6. **`clean-state-checklist.md`** -- pre-commit checklist: startup works,
   verification runs, progress log current, feature list accurate, no
   half-finished work, next session ready.

7. **`evaluator-rubric.md`** -- scorecard (0-2 per dimension): Correctness,
   Verification, Scope discipline, Reliability, Maintainability, Handoff.
   Verdict: Accept/Revise/Block. Needs tuning against human judgment over time.

8. **`quality-document.md`** -- health snapshot grading (A-D) each product
   domain and architectural layer on verification, legibility, and test
   stability, with change history — answers "is the codebase getting
   stronger?"

### Documentation (`docs/`)

- `docs/ARCHITECTURE.md` -- layer diagram, data flow for 2-3 key operations,
  storage layout, logging schema.
- `docs/PRODUCT.md` -- every feature as user-facing behavior and UI/CLI/API shape.
- `docs/RELIABILITY.md` (if runtime behavior matters) -- logging conventions,
  clean-state definition, performance measurement.

### Verification scripts (`scripts/`)

Include only what applies: a **boundary checker** (greps for layer-rule
violations, exits non-zero); a **data-integrity scanner** if data persists
to disk (orphans, dangling references); a **benchmark script** if
performance matters (core operations vs. sample data, pass/fail summary).

### Sample data

If the project consumes input data (documents, fixtures, requests), create
2-3 small realistic samples under `data/` or `fixtures/` for testing.

## Phase 4 -- Verify the harness itself, then stop

1. Run `./init.sh` and confirm it passes cleanly.
2. Run any boundary/scanner scripts and confirm they pass on the empty scaffold.
3. Confirm every file `AGENTS.md`'s artifacts section references actually exists.
4. Success test: could a fresh session, using only repository files, answer
   what this project does, how to start/verify it, what's unfinished, and
   the next best step? If not, fix the gap.
5. Make an initial commit describing it as the harness baseline (not a feature).
6. Stop. Do not start implementing features in this same pass.

Report back with: the feature list you produced, which harness files you
created, the result of `init.sh`, and the one open question (if any) you
need answered before implementation begins.
```

---

## Why this shape

Every artifact encodes one bet: a future session should never re-derive
context that already exists in the repo, paid up front during
initialization rather than accumulating as chat context. See
[index.md](./index.md) for individual template guides and the
[Initializer Agent Playbook](../reference/initializer-agent-playbook.md)
for the condensed checklist version.
