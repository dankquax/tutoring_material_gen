# Session Handoff

## Next Best Step
- **Objective:** Verify FEAT-006 end-to-end — run `extract_docling.py --file` against a real QP PDF from `01_raw_sources/past_papers/` and confirm clean Markdown output appears in `03_knowledge_base/_staging/`. Record evidence in `feature_list.json` and mark FEAT-006 `passing`.
- **Then:** FEAT-003 multi-source stitching (now unblocked — FEAT-006/007/008 all passing).

## Current Blockers / Risks
- FEAT-006 evidence still unrecorded — needs a real Docling PDF extraction run.
- Topics 7–10 have no class-notes raw sources (Theory.md missing).
- KB still contains old FEAT-005-era entries (`source_file: PastPaper_0478_xxx.md` format) — lower routing quality but no duplicates.

## Recent History (STRICT LIMIT: Last 2 Sessions Only)

**Session 016 (2026-06-27):**
- **Completed:** Full stabilization pass. Phase 1: `util_purge_2024.py` (deleted) — purged 437 old 2024 entries (both FEAT-005 and FEAT-008 formats). Key fix: used `\n---\n{yaml_key}` lookahead to avoid stopping at content `---` dividers in old format. Phase 2: `link_qa.py` — added guard rejecting zero-padded or >15 purely-numeric MS table labels (kills pseudocode line-number bleed). Phase 3: `route_hybrid.py` — Topic 05/09/03 anchor anti-prompting; `TOPIC_BREADCRUMBS` hardcoded per topic; `extract_total_marks()` Python regex; LLM prompt to keywords-only; `build_yaml_metadata()` f-string YAML constructor. Fresh 2024 batch: 293 pairs routed across 11 papers. KB: 998 total entries, 0 missing source_file, 0 fence artifacts.
- **Unfinished:** Nothing — all three phases complete and verified.

**Session 015 (2026-06-27):**
- **Completed:** KB surgery (util_kb_surgery.py, now deleted): deleted 32 duplicate `source_file: "0478_w25"` blocks, injected source_file into 38 missing blocks, stripped 37 stray yml artifact lines. Router upgraded: 10 anchors rewritten with disambiguation clauses; preamble context injection (`_build_embed_text`/`_parent_label`) for sub-questions <60 chars.
- **Unfinished:** 2024 re-routing deferred to Session 016 (now done).

## Compacted Archive

*Sessions 001–014 (2026-06-25/27): Harness baseline built. TinyTeX/tcolorbox installed. igcse_preamble.tex (6 box environments) + igcse_blueprint.tex (weekly skeleton) authored; Topic_01/02 .tex compiled PASS. parse_class_notes.py + parse_past_paper.py hardened across all 2025 papers. 35 past papers parsed 2020–2025; 305 questions routed to 10 topics (llama3.2:latest, 3-tier fallback). KB normalized to 10 folder-per-topic structure. FEAT-001–005 all passing. Major architecture upgrade: Docling/regex/cosine pipeline created (FEAT-006/007/008); digest_new_material.py rewritten; 5 deprecated parsers deleted. FEAT-007 fully stabilized (link_qa.py): hierarchical sort key, garbage filters, separator detection, validate_pairs() gate, --debug flag. FEAT-008 passing: w25 papers fully routed (127 pairs). Session 014: source_file omission fix, preamble/artifact guard fixes.*
