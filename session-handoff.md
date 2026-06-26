# Session Handoff

## Next Best Step
- **Objective:** Resume `FEAT-003` (multi-source stitching) — generate a worksheet that combines a topic's `Theory.md` with its newly-routed `Past_Papers.md` entries into one worksheet + mark-scheme `.tex` document in `05_output/`. Confirm it compiles via `./compile.sh`.
- **Target File:** `05_output/Topic_01_Data_Representation_Worksheet.tex` (or whichever topic the user names)

## Current Blockers / Risks
- `merge_theory_ollama.py` truncates combined documents exceeding ~6 000 chars (context-window guard for small models). Topics with long existing Theory.md files may get partial merges; a warning is printed when this fires.
- Topics 7–10 have no class-notes raw sources yet — the notes pipeline will report zero files for those topics until sources are added to `01_raw_sources/class_notes_docs/`.
- Class notes detection requires parent directory of each file to be named exactly `Topic_XX_Name`; files sitting directly in `01_raw_sources/class_notes_docs/` (no subfolder) will be skipped.
- Topic_08 (8 questions) and Topic_09 (9 questions) have low past-paper coverage — this reflects the actual exam's lower weighting for standalone programming/SQL questions, not a routing failure.

## Recent History (STRICT LIMIT: Last 2 Sessions Only)

**Session 010 (2026-06-26):**
- **Completed:** Upgraded `route_questions_ollama.py` with comprehensive 10-topic system prompt (explicit keyword maps + negative constraints for Topics 02/03/06, exact valid folder name list). Fixed `DEFAULT_MODEL` from `llama3` (non-existent on this system) to `llama3.2:latest` in both `route_questions_ollama.py` and `digest_new_material.py`. Added three-tier JSON fallback parser (`raw_decode` → prose-wrapped `{...}` block + unquoted-string fixer → regex field extraction) to handle llama3.2:3b's inconsistent JSON output. Reset: cleared all 10 `Past_Papers.md` files, removed 35 `pastpaper::` state entries (21 notes entries retained). Re-ran `route_questions_ollama.py --model llama3.2:latest`: **305 questions routed, 0 skipped** across all 10 topics (T01:36, T02:34, T03:59, T04:29, T05:50, T06:22, T07:44, T08:8, T09:9, T10:14). Re-bootstrapped state file via `bootstrap_state.py` (56 entries). Deleted 35 intermediate `PastPaper_*.md` files from KB root (pending cleanup from Session 008 now resolved).
- **Unfinished:** Nothing blocking. Next step is FEAT-003 multi-source worksheet generation.

**Session 008 (2026-06-26):**
- **Completed:** KB folder-per-topic normalization, `route_questions_ollama.py` (FEAT-005), `split_syllabus.py`, batch parse of 35 past papers (2020–2025), full routing run, cleanup of 8 hallucinated folders, all 10 topic folders now have `Syllabus.md`.
- **Unfinished:** Flat `PastPaper_*.md` files at KB root not yet deleted (resolved in Session 010).

## Compacted Archive

*Sessions 001–007 (2026-06-25): Harness baseline built (CLAUDE.md, init.sh, compile.sh, feature_list.json 9-feature → 4-engine-feature refactor, docs/ARCHITECTURE.md, docs/PIPELINE.md). TinyTeX + tcolorbox installed. parse_class_notes.py written and hardened for PDF (heuristic headings, bullet detection, table fencing) and DOCX (bold-run heading detection, Word numPr bullet detection, stop-words); Topics 1–6 parsed. parse_past_paper.py written and hardened (pdfplumber.find_tables() column-independent thresholds, boilerplate filters, pseudo-code line-number guard, watermark/cid filtering, multi-page MS answer merging); 35 past papers parsed 2020–2025. igcse_preamble.tex authored (stratbox/critbox/scenario/learningoutcomes/errortrap/modelans, booktabs, longtable, tikz, fancyhdr footer fix). Topic_01 and Topic_02 .tex files compiled PASS. FEAT-001–005 all passing. Study plan 00_syllabus/6_month_zero_to_hero_plan.md added. Session 009: wrote merge_theory_ollama.py and digest_new_material.py (master orchestrator with SHA-256 state tracking); updated CLAUDE.md Startup/TOKEN/Before-You-Stop sections.*
