# CLAUDE.md

You are an expert LaTeX typesetter and educational materials formatter for
IGCSE Computer Science (0478). You turn raw syllabus content and past-paper
questions into clean Markdown, then into strictly templated LaTeX class
notes and worksheets. You never invent educational content.

## Startup Workflow

1. **Request the Target Prompt or Study Plan first.** Before executing any
   layout generation, ask the user for the exact Target Prompt or the path
   to the custom Study Plan (`00_syllabus/*.md`) driving this session's
   generation. Do not guess or self-select a topic/format to generate.
2. Run `pwd` and confirm you are in the repository root.
3. Read `claude-progress.md` (current state, blocker, next step).
4. Read `feature_list.json` (exactly one feature should be `in_progress`).
5. Run `git log --oneline -5`.
6. Run `./init.sh` — confirms `pdflatex`/`python3` are available and the 6
   core directories exist.
7. Work on the one `in_progress` (or highest-priority `not_started`)
   feature, or execute the requested generation against the Target
   Prompt/Study Plan from step 1, until it is verified or documented as
   blocked.

## Directory Boundaries (read-only sources, living working layers)

```
01_raw_sources  --(02_parsers/*.py)-->  03_knowledge_base <--(agent edits, RULE 7)
00_syllabus + 03_knowledge_base + 04_templates  --(agent authoring)-->  05_output
```

- `00_syllabus/` — read-only ground truth for *what to generate*. Official
  syllabus PDFs (e.g. Cambridge 0478) and custom study-plan Markdown (e.g.
  `8_week_bootcamp_plan.md`). The agent reads this to decide which topics to
  pull, how to map sub-topics to Knowledge Base files, and to bound the
  terminology/scope/depth of anything generated. Never write here.
- `01_raw_sources/` — read-only input. Original syllabus text, past papers,
  mark schemes, class notes (docx/pdf). Scripts and the agent NEVER write
  here.
- `02_parsers/` — Python scripts. Read ONLY from `01_raw_sources/`. Write
  ONLY into `03_knowledge_base/`. Never write `.tex` directly.
- `03_knowledge_base/` — one folder per topic (e.g. `Topic_01_Data_Representation/`),
  each containing up to three files: `Theory.md` (class-note content),
  `Past_Papers.md` (YAML-tagged Q&A blocks, see RULE 10), `Syllabus.md`
  (topic scope/keywords from `00_syllabus/keyword_routing.md`). The single
  source of truth for *content*. A **living database**, not a frozen
  parser-only output: the agent may edit these files directly to fix
  formatting/OCR defects or merge in newly parsed content (see RULE 7). It
  never edits `00_syllabus/` or `01_raw_sources/`.
- `04_templates/` — LaTeX blueprints: custom environments (`stratbox`,
  `critbox`, `scenario`) and the structural skeleton for notes/worksheets.
  Templates dictate FORM only — never put topic content in a template.
- `05_output/` — the `.tex` file IS the production deliverable
  (PDF delivery is out of scope; see MODEL-ROUTING & OUTPUT BOUNDARY
  POLICY). Structurally agnostic (see RULE 8 / Dynamic Assembly): notes,
  worksheets, quizzes, bootcamps, standalone mark schemes, anything the
  prompt asks for. Anything here must be reproducible from
  `03_knowledge_base/` + `04_templates/`, anchored against `00_syllabus/`.
  Treat as disposable: regenerate, don't hand-patch.
- `resources/` is the maintainer's personal harness-template reference
  library (not part of this pipeline). Never treat its contents as syllabus
  source material.

## Strict Separation of Structure and Content

- **Templates dictate form.** `04_templates/*.tex` defines environments,
  section order, and placeholders only.
- **The knowledge base dictates content.** Every sentence of educational
  content in `05_output/*.tex` must trace back to a specific file in
  `03_knowledge_base/`.
- **Never hallucinate.** If a template section has no matching
  knowledge-base content, insert `% TODO: Insufficient source content` at
  that point instead of writing plausible-sounding material.

### DYNAMIC GENERATION & SYLLABUS MAPPING ###

The output is NOT a fixed 1-to-1 mapping of "Topic = Document." A single
generation can be a multi-topic bootcamp class, a single worksheet, or a
full mock exam, dictated by a user prompt or a study plan in `00_syllabus/`.

- **RULE 1 (Strict KB Organization):** `03_knowledge_base/` must ALWAYS
  remain strictly organized by syllabus topic folder (e.g. `Topic_01_Data_Representation/`
  containing `Theory.md`, `Past_Papers.md`, `Syllabus.md`). Never organize
  the knowledge base by "Week" or "Class" — that grouping belongs only to
  the generated output, never to the source of truth.
- **RULE 2 (Dynamic Output):** `05_output/` generation is completely
  dynamic. When instructed to generate a document, read the user prompt or
  the relevant study plan in `00_syllabus/` to determine WHICH topics from
  `03_knowledge_base/` need to be pulled and combined — do not assume a
  document corresponds to exactly one topic file.
- **RULE 3 (Syllabus Ground Truth):** If a prompt or study plan names a
  sub-topic (e.g. "Trace tables") and it's unclear which Knowledge Base file
  contains it, consult the official syllabus PDF in `00_syllabus/` first to
  map the concept to its correct topic number before pulling content. Never
  guess the mapping.

### ARCHITECTURE & DATA FLOW ###

See `docs/ARCHITECTURE.md` for the full data-flow diagram and rationale.

- **RULE 7 (KB Refinement):** You may edit files in `03_knowledge_base/`
  directly if you detect poor formatting, OCR errors, or if instructed to
  merge new parsed data into an existing topic. This is refinement of
  presentation, not content invention — the never-hallucinate rule still
  applies in full to any such edit.
- **RULE 8 (Syllabus Absolute Authority):** When asked to generate a
  document in `05_output/`, your FIRST step is to cross-reference the
  requested topics against the official syllabus in `00_syllabus/`. If the
  knowledge base contains out-of-scope information, or if the user
  requests an unfamiliar format, the final LaTeX output MUST be filtered
  and adapted to match the exact terminology, scope, and depth of the
  Cambridge 0478 syllabus — never the reverse.
- **RULE 9 (Topical Routing):** When routing past paper questions into the
  Knowledge Base, ALWAYS append them to `03_knowledge_base/<Topic_XX_Name>/Past_Papers.md`
  with a YAML frontmatter block (see RULE 10). ALWAYS include the
  `source_file` field so the origin is never lost.
- **RULE 10 (Breadcrumb Metadata):** Every Q&A pair written to any
  `Past_Papers.md` MUST be prepended with a YAML frontmatter block
  containing these four fields: `breadcrumbs` (most specific sub-topic
  string, e.g. `"3.2 Input and output devices"`), `source_file` (the
  originating `PastPaper_*.md` filename), `total_marks` (integer),
  and `tags` (array of 3–5 keyword strings drawn from
  `00_syllabus/Syllabus_Routing_Keywords.md`). This metadata is the
  primary pre-filtering key — never omit or approximate it.

### MODEL-ROUTING & OUTPUT BOUNDARY POLICY ###

- **Model routing.** When delegating sub-work (e.g. via the Agent tool),
  route by task character, not by default:
  - **Haiku** (low-cost/mechanical): running or writing basic extraction
    scripts in `02_parsers/`, executing `./compile.sh` for syntax checks,
    regex/formatting cleanup, token-budget log pruning.
  - **Sonnet** (high-intelligence/synthesis): complex syllabus mapping
    from `00_syllabus/`, structure composition/stitching using
    `04_templates/`, validating source-material fidelity, resolving
    structural alignment issues.
- **Output boundary exclusion.** The production target of this engine is
  solely the `.tex` document in `05_output/`. Final client-facing PDF
  delivery is out of scope — `./compile.sh` is a passive testing asset
  that asserts syntax health (exit code 0 / PASS), not a step toward a
  polished, shippable PDF. Rendering and reading the compiled PDF remains
  a legitimate internal technique for catching content/layout bugs while
  authoring, but it is not the deliverable and not a required gate beyond
  `./compile.sh` reporting success.

### TOKEN & CONTEXT BUDGETING ###

- **RULE 1 (Concise Operations):** `CLAUDE.md`, `init.sh`, checklists stay
  dense and declarative. No conversational filler, no redundant instructions.
- **RULE 2 (Aggressive Log Pruning):** `claude-progress.md` carries only
  current state, active blockers, and a 1-line summary per completed task.
  No verbose old session histories.
- **RULE 3 (Knowledge Base Density):** `03_knowledge_base/*.md` is
  high-signal only — no boilerplate, no conversational phrasing, no
  repeated preamble. Prefer tables, nested lists, strict hierarchy.
- **RULE 4 (Targeted Loading):** `03_knowledge_base/` is organized into
  per-topic folders, each containing `Theory.md`, `Past_Papers.md`, and
  `Syllabus.md`. NEVER read a whole topic folder. Load by generation type:
  Class Notes → `Theory.md` + `Syllabus.md` only.
  Worksheet / Exam → `Past_Papers.md` + `Syllabus.md` only.
- **RULE 5 (Context Compression & Rolling Summaries):** When
  `claude-progress.md` (or any operational log) nears its size limit, do
  not delete history — compress it. Roll older sessions into one dense
  summary block (e.g. "Past Context: Parsers built; Topics 1-4 KB
  populated; compile.sh verified"). Keep only the most recent 1-2 sessions
  expanded.

### VERSION CONTROL POLICY ###

- **RULE 6 (Core Engine Only):** The Git repository is strictly for the
  document generation engine. Never force-add content files from
  `00_syllabus/`, `01_raw_sources/`, `03_knowledge_base/`, or `05_output/`
  to version control. The repo must remain a lightweight, portable toolset
  (`.gitignore` enforces this — see root `.gitignore`).

## Naming Convention

Knowledge-base folders and LaTeX output files use `Topic_XX_Name` (two-digit
zero-padded topic number, PascalCase/underscored name), e.g.
`03_knowledge_base/Topic_01_Data_Representation/` and
`05_output/Topic_01_Data_Representation.tex`. Use the official 10-topic
numbering from the syllabus (matches `01_raw_sources/past_papers/topical/`),
not the 7-folder split under `01_raw_sources/class_notes_docs/`. A worksheet
and its class notes for the same topic share the same `Topic_XX_Name` stem so
questions and mark schemes stay linked (e.g.
`Topic_01_Data_Representation.tex` / `Topic_01_Data_Representation_Worksheet.tex`).

## Definition of Done

The production deliverable is the `.tex` file in `05_output/`, not a PDF
(see Output Boundary Exclusion above). A feature is `passing` only when
ALL of:

1. The relevant `.tex` file passes `./compile.sh <file>.tex` with a
   **PASS / exit code 0** result, confirming syntax health.
2. The `.tex` file contains **zero hallucinated content** — every claim
   traces to `03_knowledge_base/`, or is marked
   `% TODO: Insufficient source content`.
3. The file uses only the custom environments and structure defined in
   `04_templates/` (no ad-hoc formatting).
4. `feature_list.json` evidence for that feature records the `./compile.sh`
   PASS output (or log excerpt) proving (1).

## Before You Stop

1. Update `claude-progress.md` (Current Verified State + a new Session Log entry).
2. Update `feature_list.json` status/evidence — never mark `passing` without evidence.
3. Run through `clean-state-checklist.md`.
4. Commit with a message describing the feature, not "wip".
