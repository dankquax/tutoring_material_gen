# Progress Log

## Current Verified State

- Repository root: `_project/` (this repo)
- Standard startup path: `./init.sh`
- Standard verification path: `./compile.sh <file>.tex` (looks inside `05_output/`)
- Active feature: `FEAT-006` (Docling Universal Extraction Engine) — `in_progress` (evidence still unrecorded). FEAT-007 `passing`. FEAT-008 `passing`. FEAT-001–005 `passing`. FEAT-003 (multi-source stitching) deferred.
- Pipeline: Docling extraction → regex linker → cosine routing + LLM metadata. Scripts: `extract_docling.py`, `link_qa.py`, `route_hybrid.py`.
- KB structure: 10 canonical `Topic_XX_Name/` folders; `_staging/` holds 4 `*_linked.json` (w25_11/12/21/22); w25 papers now fully routed.
- KB quality: CLEAN as of 2026-06-27 — 0 missing `source_file`, 0 duplicate `0478_w25` entries, 0 stray `yml/yaml` artifact lines (all fixed by util_kb_surgery.py, now deleted). 848 total RULE 10-compliant pairs across 10 topics.
- Router: `route_hybrid.py` upgraded — anchors now explicitly anti-prompt known confusion cases (register/table/optical-storage bleeding); preamble context injection active for short sub-questions; `yml`/`yaml` fence stripping hardened.
- Current blocker: FEAT-006 evidence unrecorded (needs a real `extract_docling.py --file` run against a QP PDF).

## Session Log

**Past Context (Sessions 001-011, compressed 2026-06-26):** Harness baseline built (CLAUDE.md, feature_list.json, init.sh, compile.sh, docs). TinyTeX/tcolorbox installed; igcse_preamble.tex authored (6 box environments: stratbox/critbox/scenario/learningoutcomes/errortrap/modelans); igcse_blueprint.tex with weekly tutoring skeleton. Topic_01 and Topic_02 .tex compiled PASS. parse_class_notes.py + parse_past_paper.py hardened (pdfplumber → column-independent, zero 'Unmatched MS Entries' across all 13 2025 papers). 35 past papers parsed 2020–2025; 305 questions routed to 10 topics via route_questions_ollama.py (llama3.2:latest, 3-tier JSON fallback). KB normalized: 10 Topic_XX_Name/ folders, each with Theory.md/Past_Papers.md/Syllabus.md. Architecture upgraded 2026-06-26: FEAT-001–005 all passing; replaced heuristic parsers with Docling/regex/cosine pipeline (FEAT-006/007/008); new scripts extract_docling.py, link_qa.py, route_hybrid.py; digest_new_material.py rewritten. 7 new 2024 pairs ingested; dry-run state-writing bug fixed. Deprecated parsers deleted.

### Session 013

- Date: 2026-06-26
- Goal: Stabilize FEAT-007 (link_qa.py) — dry-run on W25 Paper 11 pair, fix structural bugs, add validation gate, batch-verify.
- Completed:
  - Ran baseline link_qa.py on 0478_w25_qp_11.md / 0478_w25_ms_11.md: 47 pairs, no crashes, 3 defect classes confirmed and fixed.
  - Fixed _sort_key: replaced (main_num, depth, label) with hierarchical (main_num, part_ordinal, subpart_roman_int). Labels now emit in correct Cambridge reading order.
  - Fixed _is_garbage: ratio heuristic (>40% non-ASCII) replaces 4-glyph-count hardcoded charset.
  - Added _SKIP_LINE_RE: skips `<!-- ... -->` image tags, `## Cambridge IGCSE` MS section headers, Docling-prefixed comma padding `## , ,`, bare comma-padding lines.
  - Fixed _clean_body: trailing lone-numeral strip now gated on len(lines)>1, preserving short numeric MS answers ('11', '66').
  - Fixed table separator detection: `re.match(r'^[-:]+$', cells[0])` replaces character-iteration logic.
  - Added validate_pairs(): leaf detection, MISSING_MS/MISSING_Q/SEQ_GAP/PREAMBLE_LEAK checks, exit code 1 on anomalies.
  - Improved find_pairs(): warns on unpaired files without crashing.
  - Added --debug flag for state-machine tracing.
- Verification: `link_qa.py 0478_w25_qp_11.md 0478_w25_ms_11.md` → 47 pairs, 0 anomalies. Batch (--batch) → PASS. Content check: no residual noise/garbage in any field. 36 leaf pairs fully linked.
- Evidence captured in feature_list.json; FEAT-007 marked passing.
- Files updated: 02_parsers/link_qa.py, feature_list.json, claude-progress.md, session-handoff.md.
- Next best step: FEAT-006 evidence (run extract_docling.py against a real QP PDF; confirm _staging/ output; mark passing). FEAT-008 now passing.

### Session 014

- Date: 2026-06-27
- Goal: Run route_hybrid.py against all w25 _linked.json files in _staging/; QC routing accuracy and metadata quality.
- Completed: QC pass, 3 script defects fixed, w25_12/21/22 routed (80 more pairs). Duplicate staging file deleted. FEAT-008 marked passing.
- Known gap at close: w25_11 had 38/47 blocks without source_file; 32 duplicate 0478_w25 entries in KB.

### Session 015

- Date: 2026-06-27
- Goal: KB surgery + router precision upgrade to push routing accuracy toward 99% and achieve 100% RULE 10 compliance.
- Completed:
  - **Phase 1 — KB Surgery:** Created and ran `util_kb_surgery.py` (temp script, now deleted). Three tasks: (1) deleted 32 duplicate entries where `source_file: "0478_w25"`; (2) injected `source_file: "0478_w25_qp_11"` into 38 YAML blocks that were missing it (w25_11 pre-fix run); (3) stripped 37 stray `yml`/`yaml` artifact lines left by LLM code-fence remnants. KB verified: 848 pairs, 0 missing source_file, 0 duplicates, 0 stray lines.
  - **Phase 2 — Anchor Anti-Prompting:** Rewrote all 10 `TOPIC_ANCHORS` in `route_hybrid.py`. New anchors are ~3× longer with explicit disambiguation clauses targeting the three known bleeding patterns: (a) `register` pulling math into Topic_03 — now Topic_01 says "register stores binary value for arithmetic, NOT CPU architecture" and Topic_03 says "does NOT include binary arithmetic"; (b) `table` pulling trace tables into Topic_09 — now Topic_07 says "trace table is algorithm testing tool, NOT database construct" and Topic_09 says "NOT algorithm trace tables"; (c) optical storage bleeding into Topic_09 — now Topic_03 explicitly claims "optical (CD, DVD, Blu-ray)"; (d) Boolean truth tables vs DB tables — Topic_09 says "NOT Boolean logic or truth tables for gates"; Topic_10 says "NOT a database table or SQL result set."
  - **Phase 3 — Preamble Context Injection:** Added `_build_embed_text()` helper and `_parent_label()` to `route_hybrid.py`. When a sub-question's text is <60 chars, the function walks up the label hierarchy (e.g., `1(c)` → `1`) to find the first ancestor with ≥60 chars of context, prepends it in-memory only for cosine routing. The canonical KB chunk is still the raw pair text — no preamble written to KB.
  - **LLM fence fix:** Extended `extract_yaml_metadata` regex to also strip `yml` (not just `yaml`) from fenced code block artifacts.
- Files updated: `02_parsers/route_hybrid.py`, `claude-progress.md`, `session-handoff.md`; `util_kb_surgery.py` created and deleted.
