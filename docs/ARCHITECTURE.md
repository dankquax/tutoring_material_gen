# Architecture

## Pipeline: Input -> Extraction -> Synthesis -> Output

The engine is on-demand and prompt/study-plan driven, not a fixed
topic-by-topic batch job. Every generation run is one pass through these
four steps:

**Step 1 -- Input ingestion.** The user supplies an on-demand Target
Prompt, or points at a custom Study Plan (`00_syllabus/*.md`). Nothing
downstream runs until this exists (see `CLAUDE.md` Startup Workflow).

**Step 2 -- Extraction & Resolution.** The engine fetches raw metadata
from `01_raw_sources/` via `02_parsers/` (mechanical, deterministic,
docx/pdf -> Markdown only), aligns the requested competencies against the
strict sequence of `00_syllabus/` (the Syllabus Anchor -- terminology,
scope, and depth here override anything found downstream), then builds or
appends to the living `03_knowledge_base/` Markdown documents.

**Step 3 -- Synthesis & Layout.** The engine pulls structure exclusively
from the abstract `04_templates/` blueprint (environments, section order,
placeholders -- never topic content) and populates it with textual
content from the `03_knowledge_base/` files selected in Step 2.

**Step 4 -- Output.** The engine writes the compiled `.tex` source out to
`05_output/`. The `.tex` file is the production deliverable; PDF delivery
is out of scope (`./compile.sh` only asserts syntax health -- see
`CLAUDE.md` MODEL-ROUTING & OUTPUT BOUNDARY POLICY).

```
Step 1            Step 2                                          Step 3                Step 4
-------            ------                                          ------                ------
Target Prompt  ->  01_raw_sources/ --(02_parsers/*.py)--> 03_knowledge_base/  ->  [agent: 04_templates/  ->  05_output/
or Study Plan       (read-only)         (mechanical)        (living Markdown,        + 03_knowledge_base/]      *.tex
(00_syllabus/*.md)                                           agent may also                                 (deliverable;
                         ^                                    edit directly,                                  PDF delivery
                         |                                    RULE 7)                                         out of scope)
                         +---- anchored against 00_syllabus/ (Syllabus Anchor: scope/terms/depth) -------------+
```

## Directories

| Directory | Reads from | Writes to | Owner |
| --- | --- | --- | --- |
| `00_syllabus/` | (external: official Cambridge 0478 syllabus + study plans) | — (read-only) | human/maintainer |
| `01_raw_sources/` | (external: docx/pdf source material) | — (read-only) | human/maintainer |
| `02_parsers/` | `01_raw_sources/` | `03_knowledge_base/` | Python scripts |
| `03_knowledge_base/` | `00_syllabus/` (mapping guidance) | itself | parsers **and** the agent (see Living Database) |
| `04_templates/` | — | — | maintainer (structure only) |
| `05_output/` | `03_knowledge_base/` + `04_templates/`, anchored against `00_syllabus/` | itself (`.tex`, plus incidental `.pdf`/logs from `./compile.sh`'s syntax check) | agent authoring + `compile.sh` |

`01_raw_sources/` and `00_syllabus/` are the only true read-only layers. No
step writes back into either of them. `02_parsers/` never touches
`05_output/`; the agent authoring step never touches `01_raw_sources/` or
`02_parsers/`.

## Core Principles

### 1. The Living Database

`03_knowledge_base/*.md` is not a frozen, parser-only artifact. It is a
living set of Markdown documents that the agent is permitted and encouraged
to refine over time:

- Fix formatting defects, OCR/extraction artifacts, or broken headings
  found on review.
- Append newly parsed questions, sources, or topic content into an
  existing `Topic_XX_Name.md` rather than only creating new files.
- Any such edit is still bound by `CLAUDE.md`'s never-hallucinate rule --
  refining presentation of real content is always allowed; inventing
  content is never allowed, regardless of which actor (parser or agent)
  is doing the writing.

This supersedes the older assumption that `03_knowledge_base/` is solely
"the target of parsers" with no other writer.

### 2. Dynamic Assembly

`05_output/` generation is structurally agnostic. There is no fixed
"notes file" or "worksheet file" shape the system enforces. A single
Target Prompt or Study Plan can drive the agent to produce a 10-minute
quiz, an 8-week bootcamp pack, a standalone mark scheme, full class notes,
or any other document shape -- as long as every educational claim in it
still traces back to `03_knowledge_base/` (or is marked
`% TODO: Insufficient source content`) and every structural element comes
from `04_templates/`.

### 3. The Syllabus Anchor

`00_syllabus/` is the absolute ground truth for *what* gets generated and
*how it's scoped* -- not just a topic-mapping lookup. No matter how
flexible the requested output is, the agent's first step before
generating into `05_output/` is to cross-reference the requested topics
against the official syllabus. The syllabus's terminology, scope, and
depth take priority over the knowledge base: if `03_knowledge_base/`
contains material that is out of scope, uses non-syllabus terminology, or
exceeds the syllabus's required depth for that topic, the generated
`05_output/` document must be filtered/adapted to match the syllabus --
never the reverse.

## Why this shape

- **Read-only layers (`00_syllabus/`, `01_raw_sources/`) vs. living layers
  (`03_knowledge_base/`, `05_output/`)** keeps the two sources of ground
  truth -- "what the syllabus requires" and "what the source material
  says" -- stable, while still letting the system improve its own working
  copy of the content and its generated artifacts over time.
- **Parsers vs. agent authoring are separate steps** because parsing is
  mechanical (docx/pdf -> Markdown) and deterministic, while LaTeX
  authoring and knowledge-base refinement require judgment and must be
  auditable for hallucination -- keeping them separate makes each
  independently verifiable.
- **`04_templates/` has no content** so the same blueprint can be reused
  across all 10 syllabus topics, and across any document shape, without
  drift.
- **The deliverable is `.tex`, not PDF** -- pdflatex's exit code is the
  syntax-health gate; client-facing PDF polish is a separate, out-of-scope
  concern, keeping this engine's job narrowly scoped to correct, faithful
  LaTeX source generation.
