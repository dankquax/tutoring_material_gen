# CLAUDE.md

You are an expert LaTeX typesetter and educational materials formatter for
IGCSE Computer Science (0478). You turn raw syllabus content and past-paper
questions into clean Markdown, then into strictly templated LaTeX class
notes and worksheets. You never invent educational content.

## Startup Workflow

1. Run `pwd` and confirm you are in the repository root.
2. Read `claude-progress.md` (current state, blocker, next step).
3. Read `feature_list.json` (exactly one feature should be `in_progress`).
4. Run `git log --oneline -5`.
5. Run `./init.sh` — confirms `pdflatex`/`python3` are available and the 6
   core directories exist.
6. Work on the one `in_progress` (or highest-priority `not_started`)
   feature until it is verified or documented as blocked.

## Directory Boundaries (strict, one-way data flow)

```
01_raw_sources  --(02_parsers/*.py)-->  03_knowledge_base
00_syllabus + 03_knowledge_base + 04_templates  --(agent authoring)-->  05_output
```

- `00_syllabus/` — read-only ground truth for *what to generate*. Official
  syllabus PDFs (e.g. Cambridge 0478) and custom study-plan Markdown (e.g.
  `8_week_bootcamp_plan.md`). The agent reads this to decide which topics to
  pull and how to map sub-topics to Knowledge Base files. Never write here.
- `01_raw_sources/` — read-only input. Original syllabus text, past papers,
  mark schemes, class notes (docx/pdf). Scripts and the agent NEVER write
  here.
- `02_parsers/` — Python scripts. Read ONLY from `01_raw_sources/`. Write
  ONLY into `03_knowledge_base/`. Never write `.tex` directly.
- `03_knowledge_base/` — clean Markdown, one file per topic, the
  single source of truth for *content*. The agent reads this and
  `04_templates/` to write `.tex`; it never edits `01_raw_sources/`.
- `04_templates/` — LaTeX blueprints: custom environments (`stratbox`,
  `critbox`, `scenario`) and the structural skeleton for notes/worksheets.
  Templates dictate FORM only — never put topic content in a template.
- `05_output/` — generated `.tex` (and compiled `.pdf`) files. Anything here
  must be reproducible from `03_knowledge_base/` + `04_templates/`. Treat
  as disposable: regenerate, don't hand-patch.
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
  remain strictly organized by syllabus topic (e.g. `Topic_01_Data_Representation.md`).
  Never organize the knowledge base by "Week" or "Class" — that grouping
  belongs only to the generated output, never to the source of truth.
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

### TOKEN & CONTEXT BUDGETING ###

- **RULE 1 (Concise Operations):** `CLAUDE.md`, `init.sh`, checklists stay
  dense and declarative. No conversational filler, no redundant instructions.
- **RULE 2 (Aggressive Log Pruning):** `claude-progress.md` carries only
  current state, active blockers, and a 1-line summary per completed task.
  No verbose old session histories.
- **RULE 3 (Knowledge Base Density):** `03_knowledge_base/*.md` is
  high-signal only — no boilerplate, no conversational phrasing, no
  repeated preamble. Prefer tables, nested lists, strict hierarchy.
- **RULE 4 (Targeted Loading):** Generating a `.tex` file never reads the
  full `03_knowledge_base/` directory. Read only the exact `Topic_XX_*.md`
  files named by the prompt or syllabus mapping.
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

Markdown and LaTeX files use `Topic_XX_Name.{md,tex}` (two-digit zero-padded
topic number, PascalCase/underscored name), e.g. `Topic_01_Data_Representation.md`
and `Topic_01_Data_Representation.tex`. Use the official 10-topic numbering
from the syllabus (matches `01_raw_sources/past_papers/topical/`), not the
7-folder split under `01_raw_sources/class_notes_docs/`. A worksheet and its
class notes for the same topic share the same `Topic_XX_Name` stem so
questions and mark schemes stay linked (e.g.
`Topic_01_Data_Representation.tex` / `Topic_01_Data_Representation_Worksheet.tex`).

## Definition of Done

A feature is `passing` only when ALL of:

1. The relevant `.tex` file compiles via `./compile.sh <file>.tex` to PDF
   with **zero pdflatex errors**.
2. The `.tex` file contains **zero hallucinated content** — every claim
   traces to `03_knowledge_base/`, or is marked
   `% TODO: Insufficient source content`.
3. The file uses only the custom environments and structure defined in
   `04_templates/` (no ad-hoc formatting).
4. `feature_list.json` evidence for that feature records the compile
   command output (or log excerpt) proving (1).

## Before You Stop

1. Update `claude-progress.md` (Current Verified State + a new Session Log entry).
2. Update `feature_list.json` status/evidence — never mark `passing` without evidence.
3. Run through `clean-state-checklist.md`.
4. Commit with a message describing the feature, not "wip".
