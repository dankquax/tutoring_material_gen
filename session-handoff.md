# Session Handoff

## Next Best Step
- **Objective:** Verify FEAT-006 end-to-end — run `extract_docling.py --file` against a real QP PDF from `01_raw_sources/past_papers/` and confirm clean Markdown output appears in `03_knowledge_base/_staging/`. Record evidence in `feature_list.json` and mark FEAT-006 `passing`.
- **Then:** FEAT-003 final gap — generate a worksheet using `Past_Papers.md` questions + mark scheme (multi-source stitch) to complete FEAT-003 verification #2.

## Current Blockers / Risks
- FEAT-006 evidence still unrecorded — needs a real Docling PDF extraction run.
- Topics 7–10 have no class-notes raw sources (Theory.md missing).
- KB still contains old FEAT-005-era entries (`source_file: PastPaper_0478_xxx.md` format) — lower routing quality but no duplicates.
- tcolorbox title constraint: commas and bare parentheses in `\begin{envname}[...]` custom titles are pgfkeys separators; use em-dash or rephrase to avoid compile errors.

## Recent History (STRICT LIMIT: Last 2 Sessions Only)

**Session 019 (2026-06-29):**
- **Completed:** FEAT-003 single-topic class notes generation for Topic 04. Wrote `05_output/Topic_04_Software.tex` from scratch covering syllabus 4.1 (system vs application software, OS functions x9, software hierarchy, interrupt types and handling cycle) and 4.2 (high-level vs low-level languages, assembler/compiler/interpreter, IDE functions). All 6 environments deployed (learningoutcomes, critbox ×3, stratbox ×4, errortrap ×1, scenario ×2, modelans ×1). Two TikZ diagrams: software hierarchy stacked rectangles and interrupt handling cycle flow. Zero hallucinated content — all claims trace to Theory.md / Past_Papers.md. `./compile.sh` → PASS exit 0 on first attempt.
- **Unfinished:** FEAT-006 evidence; FEAT-003 multi-source stitching (worksheet).

**Session 018 (2026-06-29):**
- **Completed:** FEAT-003 single-topic class notes generation for Topic 02. Wrote `05_output/Topic_02_Data_Transmission.tex` from scratch covering syllabus 2.1/2.2/2.3. All 6 environments deployed (learningoutcomes, stratbox ×4, critbox ×5, errortrap ×1, scenario ×3, modelans ×1). Zero hallucinated content. `./compile.sh` → PASS exit 0.
- **Unfinished:** FEAT-006 evidence; FEAT-003 multi-source stitching (worksheet).

## Compacted Archive

*Sessions 001–017 (2026-06-25/29): Harness baseline built. TinyTeX/tcolorbox installed. igcse_preamble.tex (6 box environments) + igcse_blueprint.tex (weekly skeleton) authored. Topic_01/02 .tex compiled PASS. parse_class_notes.py + parse_past_paper.py hardened across all 2025 papers. 35 past papers parsed 2020–2025; 305 questions routed to 10 topics. KB normalized to 10 folder-per-topic structure. FEAT-001–005 all passing. Architecture upgraded to Docling/regex/cosine pipeline (FEAT-006/007/008). FEAT-007 fully stabilized (link_qa.py): hierarchical sort, garbage filters, validate_pairs(). FEAT-008 passing: w25+2024 papers routed (127+293 pairs). KB surgery: 32 duplicates deleted, 38 source_file injected, 37 stray artifacts stripped. Router: 10 anchors rewritten with disambiguation clauses; preamble context injection for sub-questions <60 chars. Session 016 (2026-06-27): Full stabilization pass — purged 437 old 2024 KB entries, link_qa.py numeric-label guard, route_hybrid.py hardening (breadcrumbs hardcoded, marks via regex, LLM keywords-only); KB: 998 entries, 0 missing source_file. Session 017 (2026-06-29): FEAT-003 Topic_01_Data_Representation.tex written; all 6 environments deployed; tcolorbox pgfkeys constraint discovered (commas/parens break compilation); PASS exit 0.*
