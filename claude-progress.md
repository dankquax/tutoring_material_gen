# Progress Log

## Current Verified State

- Repository root: `_project/` (this repo)
- Standard startup path: `./init.sh`
- Standard verification path: `./compile.sh 05_output/<file>.tex`
- Current highest-priority unfinished feature: `pipeline-001` (end-to-end vertical slice for Topic 1)
- Current blocker: `pdflatex` and `python3` are not installed/on PATH in this environment — `init.sh` reports this as a warning but does not block directory setup. Install both before starting `pipeline-001`.

## Session Log

### Session 001

- Date: 2026-06-25
- Goal: Initialize the repository harness before any feature work — directory boundaries, root instructions, feature tracker, scripts, docs.
- Completed:
  - Migrated real raw material out of the old ad hoc `source_docs/` into `01_raw_sources/` (`class_notes_docs`, `past_papers`, `syllabus`, `notes_bank`, `question_bank`, `latex_template_sample`); removed the now-empty `source_docs/` and `class_materials_tex/` shells.
  - Created `02_parsers/`, `03_knowledge_base/`, `04_templates/`, `05_output/` (empty, ready for feature work).
  - Wrote `CLAUDE.md`, `feature_list.json` (9 features), `claude-progress.md`, `init.sh`, `compile.sh`, `clean-state-checklist.md`, `evaluator-rubric.md`, `docs/ARCHITECTURE.md`, `docs/PIPELINE.md`.
- Verification run: `./init.sh` (directory + dependency check only — no feature code exists yet to compile).
- Evidence captured: see Session 001 entry in this file once `./init.sh` output is confirmed in Phase 4 of this session.
- Commits: harness baseline commit (see `git log`).
- Files or artifacts updated: all root harness files listed above, plus the directory migration.
- Known risk or unresolved issue: `pdflatex`/`python3` missing locally (see blocker above); the official 10-topic syllabus numbering has not yet been reconciled against the 7-folder split in `01_raw_sources/class_notes_docs/` — first parser (`parsing-001`) must resolve this mapping.
- Next best step: install `pdflatex` (e.g. a TeX Live/MiKTeX distribution) and `python3`, then start `pipeline-001` — write the first parser script against one class-notes file for Topic 1.
