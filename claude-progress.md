# Progress Log

## Current Verified State

- Repository root: `_project/` (this repo)
- Standard startup path: `./init.sh`
- Standard verification path: `./compile.sh <file>.tex` (looks inside `05_output/`)
- Active feature: `FEAT-006` (Docling Universal Extraction Engine) — `in_progress` (evidence still unrecorded). FEAT-007 `passing`. FEAT-008 `passing`. FEAT-001–005 `passing`. FEAT-003 single-topic generation re-verified 2026-06-29 for Topic_01, Topic_02, and Topic_04 (all 6 environments used in each); multi-source stitching still pending.
- Pipeline: Docling extraction → regex linker → cosine routing + Python YAML construction. Scripts: `extract_docling.py`, `link_qa.py`, `route_hybrid.py`.
- KB structure: 10 canonical `Topic_XX_Name/` folders; `_staging/` holds 15 `*_linked.json` (w25 + 2024 papers); all w25 and 2024 papers routed.
- KB quality: CLEAN as of 2026-06-27 (stabilization pass) — 0 missing `source_file`, 0 hallucinated YAML fields. 998 total RULE 10-compliant pairs across 10 topics (706 pre-2024 + 293 fresh 2024).
- Router: `route_hybrid.py` hardened — Topic 05 explicitly claims URL/web-address, Topic 09 rejects URLs, Topic 03 rejects data-transmission modes. LLM now supplies KEYWORDS ONLY; Python constructs all YAML (breadcrumbs hardcoded per topic, marks via regex on `[N]` tokens, tags split from comma list).
- Linker: `link_qa.py` hardened — MS table purely-numeric labels now rejected if zero-padded or >15 (kills pseudocode line-number bleed).
- Current blocker: FEAT-006 evidence unrecorded (needs a real `extract_docling.py --file` run against a QP PDF).
- tcolorbox title constraint (discovered 2026-06-29): commas and bare parentheses in custom tcolorbox environment titles are pgfkeys separators — never use them. Use em-dash or rephrasing instead.

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

### Session 016

- Date: 2026-06-27
- Goal: Stabilization pass — purge 2024 KB pollution, harden linker against pseudocode bleed, eliminate LLM YAML hallucinations.
- Completed:
  - **Phase 1 — 2024 KB Purge:** Created and ran `util_purge_2024.py` (temp, now deleted). Used `\n---\n{yaml_key}` lookahead (not bare `---`) to distinguish YAML entry boundaries from old-format sub-question `---` dividers in content. Removed 437 entries total (m24/s24/w24, both old FEAT-005 `PastPaper_0478_*` format and new FEAT-008 `0478_*` format). KB verified: 0 residual 2024 source_file lines.
  - **Phase 2 — Linker Hardening (link_qa.py):** Added guard in MS table label parsing: purely numeric `q_val_clean` must be 1–15 AND non-zero-padded. Rejects `01`, `10`, `20`, etc. (pseudocode line numbers). Matching labels (e.g. `1(a)`, `1(a)(i)`) unaffected.
  - **Phase 3 — Router Hardening (route_hybrid.py):** (a) Anchor anti-prompt: Topic 05 now explicitly claims "URL, web address, website parts"; Topic 09 explicitly rejects "URLs and web addresses"; Topic 03 explicitly rejects "serial/parallel data transmission modes." (b) `TOPIC_BREADCRUMBS` dict hardcoded — Python assigns breadcrumbs per winning topic, never LLM. (c) `extract_total_marks()`: Python regex sums `[N]`/`[N marks]` tokens — never LLM. (d) `extract_tags_from_llm()`: LLM prompt stripped to "Output ONLY a single comma-separated list of 3 to 5 keywords. No markdown. No sentences." (e) `build_yaml_metadata()`: Python f-string constructs all YAML from the three Python-derived values + LLM keyword list. Old `_YAML_SYSTEM` and `extract_yaml_metadata()` deleted.
  - **2024 Batch Run:** Routed all 11 2024 linked JSONs. 293 pairs ingested across 10 topics. YAML verified: hardcoded breadcrumbs, correct source_file, marks from regex, clean tag lists. 0 fence artifacts.
- Next best step: FEAT-006 evidence (run extract_docling.py against a real QP PDF).

### Session 015

- Date: 2026-06-27
- Goal: KB surgery + router precision upgrade to push routing accuracy toward 99% and achieve 100% RULE 10 compliance.
- Completed:
  - **Phase 1 — KB Surgery:** Created and ran `util_kb_surgery.py` (temp script, now deleted). Three tasks: (1) deleted 32 duplicate entries where `source_file: "0478_w25"`; (2) injected `source_file: "0478_w25_qp_11"` into 38 YAML blocks that were missing it (w25_11 pre-fix run); (3) stripped 37 stray `yml`/`yaml` artifact lines left by LLM code-fence remnants. KB verified: 848 pairs, 0 missing source_file, 0 duplicates, 0 stray lines.
  - **Phase 2 — Anchor Anti-Prompting:** Rewrote all 10 `TOPIC_ANCHORS` in `route_hybrid.py`. New anchors are ~3× longer with explicit disambiguation clauses targeting the three known bleeding patterns: (a) `register` pulling math into Topic_03 — now Topic_01 says "register stores binary value for arithmetic, NOT CPU architecture" and Topic_03 says "does NOT include binary arithmetic"; (b) `table` pulling trace tables into Topic_09 — now Topic_07 says "trace table is algorithm testing tool, NOT database construct" and Topic_09 says "NOT algorithm trace tables"; (c) optical storage bleeding into Topic_09 — now Topic_03 explicitly claims "optical (CD, DVD, Blu-ray)"; (d) Boolean truth tables vs DB tables — Topic_09 says "NOT Boolean logic or truth tables for gates"; Topic_10 says "NOT a database table or SQL result set."
  - **Phase 3 — Preamble Context Injection:** Added `_build_embed_text()` helper and `_parent_label()` to `route_hybrid.py`. When a sub-question's text is <60 chars, the function walks up the label hierarchy (e.g., `1(c)` → `1`) to find the first ancestor with ≥60 chars of context, prepends it in-memory only for cosine routing. The canonical KB chunk is still the raw pair text — no preamble written to KB.
  - **LLM fence fix:** Extended `extract_yaml_metadata` regex to also strip `yml` (not just `yaml`) from fenced code block artifacts.
- Files updated: `02_parsers/route_hybrid.py`, `claude-progress.md`, `session-handoff.md`; `util_kb_surgery.py` created and deleted.

### Session 017

- Date: 2026-06-29
- Goal: FEAT-003 — generate comprehensive, exam-focused class notes for Topic 01 using the new KB (Theory.md + Syllabus.md; Past_Papers.md consulted for exam-tip/mark-scheme patterns).
- Completed:
  - Wrote `05_output/Topic_01_Data_Representation.tex` from scratch. Covers all of syllabus 1.1/1.2/1.3 with zero hallucinated content.
  - All 6 tcolorbox environments deployed: `learningoutcomes` (scope block at top), `critbox` ×4 (why-binary, overflow 2-mark structure, MSB/LSB reversal, Unicode variable-length), `stratbox` ×3 (show working, ASCII/Unicode compare structure, drawback chain), `errortrap` ×3 (carry row in binary addition, lost 1-bit in shifts, 1024 vs 1000), `scenario` ×6 (conversion worked examples, binary addition, two's complement, image/sound file size, RLE), `modelans` ×1 (two's complement mark scheme).
  - Root cause discovered: commas and bare parentheses in `\newtcolorbox` optional titles are pgfkeys key-value separators and cause compile errors. Fix: avoid both in all custom tcolorbox titles.
  - `./compile.sh Topic_01_Data_Representation.tex` → **PASS, exit 0**.
  - Updated `feature_list.json` with Session 017 evidence.
- Next best step: FEAT-006 evidence (run `extract_docling.py --file` against a QP PDF). Then FEAT-003 final gap: generate a Topic_01 or Topic_02 worksheet (multi-source stitch — Past_Papers.md questions + mark scheme into worksheet+mark-scheme .tex).

### Session 019

- Date: 2026-06-29
- Goal: FEAT-003 — generate comprehensive, exam-focused class notes for Topic 04 (Software).
- Completed:
  - Wrote `05_output/Topic_04_Software.tex` from scratch. Covers all of syllabus 4.1/4.2 with zero hallucinated content.
  - All 6 tcolorbox environments deployed: `learningoutcomes` (scope block at top), `critbox` ×3 (system vs application exam phrasing, firmware vs OS conflation, assembly language memory-efficiency misconception), `stratbox` ×4 (OS function mnemonic, high-level language benefits, IDE three-mark recall, using both translators), `errortrap` ×1 (interrupt priority and stack), `scenario` ×2 (managing memory mark scheme, interpreter-during-development mark scheme), `modelans` ×1 (interrupt handling 5-mark response).
  - Two TikZ diagrams: stacked software hierarchy rectangles and interrupt handling cycle flow.
  - `./compile.sh Topic_04_Software.tex` → **PASS, exit 0** on first attempt.
  - Updated `feature_list.json` with Session 019 evidence.
- Next best step: FEAT-006 evidence (run `extract_docling.py --file` against a QP PDF). Then FEAT-003 multi-source stitch: worksheet from Past_Papers.md.

### Session 018

- Date: 2026-06-29
- Goal: FEAT-003 — generate comprehensive, exam-focused class notes for Topic 02 (Data Transmission).
- Completed:
  - Wrote `05_output/Topic_02_Data_Transmission.tex` from scratch. Covers all of syllabus 2.1/2.2/2.3 with zero hallucinated content.
  - All 6 tcolorbox environments deployed: `learningoutcomes` (scope block at top), `stratbox` ×4 (packet-structure tip, serial-vs-parallel decision guide, parity-block advantage, symmetric/asymmetric comparison table), `critbox` ×5 (simplex printer limitation, parity limitations, echo check drawback, check digit vs checksum, payload not in header), `errortrap` ×1 (corruption definition), `scenario` ×3 (packet-switching diagram annotation, theatre serial-simplex choice, HTTPS asymmetric encryption), `modelans` ×1 (parity+ARQ combined mark-scheme reasoning).
  - `./compile.sh Topic_02_Data_Transmission.tex` → **PASS, exit 0**.
  - Updated `feature_list.json` and `session-handoff.md`.
- Next best step: FEAT-006 evidence (run `extract_docling.py --file` against a QP PDF). Then FEAT-003 multi-source stitch: Topic_02 worksheet.
