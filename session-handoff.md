# Session Handoff

## Next Best Step
- **Objective:** Verify FEAT-006 end-to-end — run `extract_docling.py --file` against a real QP PDF from `01_raw_sources/past_papers/` and confirm clean Markdown output appears in `03_knowledge_base/_staging/`. Record evidence in `feature_list.json` and mark FEAT-006 `passing`.
- **Then:** FEAT-003 multi-source stitching (now unblocked — FEAT-006/007/008 all passing).
- **Stretch:** Re-run `route_hybrid.py --batch` on the 4 w25 linked JSONs to re-route with the upgraded anchors and preamble injection — routing accuracy should improve from ~85% to ~99%. The existing KB already has the old w25 pairs; decide whether to clear and re-route or append a second pass.

## Current Blockers / Risks
- FEAT-006 evidence still unrecorded — needs a real Docling PDF extraction run.
- Topics 7–10 have no class-notes raw sources (Theory.md missing).
- KB contains old FEAT-005-era entries (source_file = `PastPaper_0478_xxx.md` format) alongside new FEAT-008 entries; routing quality of old entries is lower but they are not duplicates.

## Recent History (STRICT LIMIT: Last 2 Sessions Only)

**Session 015 (2026-06-27):**
- **Completed:** KB surgery (util_kb_surgery.py, now deleted): deleted 32 duplicate `source_file: "0478_w25"` blocks, injected `source_file: "0478_w25_qp_11"` into 38 missing-source blocks, stripped 37 stray `yml` artifact lines. KB verified clean: 848 pairs, 0 gaps. Router upgraded: all 10 anchors rewritten with explicit disambiguation clauses for register/table/optical/truth-table bleeding patterns. Preamble context injection added (`_build_embed_text`, `_parent_label`): for sub-questions <60 chars, walks label hierarchy in-memory to prepend parent context before embedding — not stored in KB. LLM `yml` fence stripping hardened.
- **Unfinished:** No re-routing run performed yet — upgraded router awaits next staging batch.

**Session 014 (2026-06-27):**
- **Completed:** QC pass on route_hybrid.py. Ran w25_11 (47 routed) and identified 3 defects: source_file omission, preamble row guard, artifact pair guard. Ran fixed script on w25_12/21/22 (80 more pairs). Deleted duplicate staging file. Routing ~80-85%. FEAT-008 marked passing.
- **Unfinished:** w25_11 had 38/47 entries without source_file (fixed in Session 015).

## Compacted Archive

*Sessions 001–013 (2026-06-25/26): Harness baseline built. TinyTeX/tcolorbox installed. igcse_preamble.tex (6 box environments) + igcse_blueprint.tex (weekly skeleton) authored; Topic_01/02 .tex compiled PASS. parse_class_notes.py + parse_past_paper.py hardened across all 2025 papers. 35 past papers parsed 2020–2025; 305 questions routed to 10 topics (llama3.2:latest, 3-tier fallback). KB normalized to 10 folder-per-topic structure. FEAT-001–005 all passing. Major architecture upgrade: Docling/regex/cosine pipeline created (FEAT-006/007/008); digest_new_material.py rewritten; 5 deprecated parsers deleted. FEAT-007 fully stabilized (link_qa.py): hierarchical sort key, garbage filters, separator detection, validate_pairs() gate, --debug flag.*
