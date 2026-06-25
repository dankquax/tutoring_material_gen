# Template Guide

These templates are ready to copy into your own project. Each serves a specific purpose in the agent's workflow. Edit the contents to match your project's commands, paths, feature names, and verification steps.

## How to Get Started

Copy these four files into your project root first:

1. `AGENTS.md` or `CLAUDE.md`
2. `init.sh`
3. `claude-progress.md`
4. `feature_list.json`

Each template has a word budget — see [`../reference/document-budgets.md`](../reference/document-budgets.md). Keep edits inside it; an unbounded progress log defeats its own purpose.

Add remaining files as your project grows, or hand an agent the [Project Harness Bootstrap Prompt](./project-harness-prompt.md) along with a project description to generate the whole set (plus `docs/` and `scripts/`) tailored to your project in one pass.

---

## AGENTS.md

The root instruction file for agent sessions. Replace the startup workflow steps with your actual project paths and commands, adjust working rules to match your conventions, and keep the definition of done section.

**What it does for the agent:**

- Tells it to read progress and feature state before starting work
- Forces it to work on one feature at a time
- Requires evidence before marking anything as done
- Defines what a clean end-of-session looks like

Use `AGENTS.md` for Codex or other agents. Use `CLAUDE.md` if working with Claude Code — the structure is the same, just formatted for Claude's instruction style.

## init.sh

The startup script that runs dependency installation, verification, and prints the start command in one shot. Copy to your project root and edit these three variables at the top:

- `INSTALL_CMD` — your dependency install command (e.g. `npm install`)
- `VERIFY_CMD` — your basic verification command (e.g. `npm test`)
- `START_CMD` — your dev server start command (e.g. `npm run dev`)

Then run `chmod +x init.sh`. The script prints the current directory, installs dependencies, runs verification, and prints (or runs) the start command. If verification fails, the agent should stop and fix the baseline first.

## claude-progress.md

The progress log read at the start of every session and updated at the end. Copy to your project root and fill in the "Current Verified State" section with your project's info, then update the session record after each session.

**Current Verified State fields:**

- `Repository root directory` — where the project lives
- `Standard startup path` — command to get the project running
- `Standard verification path` — command to run tests
- `Highest priority unfinished feature` — what the next session should work on
- `Current blocker` — anything that's stuck

**Session Record fields:**

- `Goal` — what you planned to do
- `Completed` — what actually got done
- `Verification run` — what tests were executed
- `Evidence recorded` — what proof was captured
- `Commits` — what was committed
- `Known risks` — what might be broken
- `Next best action` — where the next session should start

## feature_list.json

The feature tracker: a machine-readable list of every feature with its status, verification steps, and evidence. Replace the example features with your own. Each feature needs:

- `id` — short unique identifier
- `priority` — integer, lower = higher priority
- `area` — which part of the app (e.g. "chat", "import")
- `title` — short description
- `user_visible_behavior` — what the user should see when it works
- `status` — one of `not_started`, `in_progress`, `blocked`, `passing`
- `verification` — step-by-step instructions to confirm it works
- `evidence` — recorded proof that verification passed
- `notes` — any extra context

**Status rules:**

- `not_started` — hasn't been touched
- `in_progress` — the one feature currently being worked on (only one at a time)
- `blocked` — can't proceed due to a documented issue
- `passing` — verification passed and evidence is recorded

## session-handoff.md

A compact handoff note between sessions for quick continuation. Copy to your project root and fill out at the end of each session.

**What each section covers:**

- **Currently verified** — what's confirmed working and verification run
- **Changes this session** — what code or infrastructure changed
- **Still broken or unverified** — known issues and risky areas
- **Next best action** — what the next session should do
- **Commands** — startup, verification, and debug commands for quick reference

This file is optional for small sessions, but important when sessions are long or the project has multiple active areas.

## clean-state-checklist.md

A checklist to run before ending each session, ensuring the repo is in a good state for the next session. The agent should check these items as part of its end-of-session routine:

- Standard startup still works
- Standard verification still runs
- Progress log is updated
- Feature list reflects actual state (no false `passing` entries)
- No half-finished work left unrecorded
- Next session can continue without manual fixes

## evaluator-rubric.md

A scorecard for reviewing agent output quality after sessions or at project milestones. After completing work, score across six dimensions (0-2 each):

1. **Correctness** — does the implementation match the target behavior?
2. **Verification** — were the required checks actually run, with evidence?
3. **Scope discipline** — did the agent stay within the selected feature?
4. **Reliability** — does the result survive a restart or re-run?
5. **Maintainability** — is the code and documentation clear for the next session?
6. **Handoff readiness** — can a new session continue using only repo artifacts?

Conclusion options: Accept (meets the bar), Revise (needs fixes), or Block (fundamental issues). The evaluator needs tuning: agents are poor self-judges. Compare its scores against your human judgment. Where they diverge, make the rubric more specific. Plan for 3-5 tuning rounds.

## quality-document.md

A quality snapshot grading each product domain and architectural layer in your project. Tracks codebase health over time, not just individual session output.

Copy to your project root. Before a session, read it to understand where the codebase is weakest. After a session, update grades based on what changed. Over time, compare snapshots to see which harness changes improved codebase health.

**What it grades:**

- **Product domains** (e.g., document import, Q&A flow, indexing): each domain gets a grade (A-D) across verification status, agent legibility, test stability, and key gaps
- **Architectural layers** (e.g., main process, preload, renderer, services): each layer gets a grade for boundary enforcement and agent legibility

The evaluator rubric scores individual agent outputs ("Did the agent do good work this session?"). The quality document scores the codebase itself ("Is the project getting stronger or weaker over time?").

Update after each significant session, before benchmark comparisons, after cleanup passes, or when onboarding a new agent or model.

**Harness simplification tie-in:**

To check whether a harness component is still needed: (1) Take a quality snapshot, (2) Remove one component, (3) Run the benchmark task suite, (4) Take another snapshot, (5) Compare — if grades didn't drop, the component was overhead; if they did, restore it.
