# Pipeline: Input -> Extraction -> Synthesis -> Output

## Step 1: Input ingestion

Before any generation work starts, get the exact Target Prompt or the path
to a custom Study Plan (`00_syllabus/*.md`) from the user (`CLAUDE.md`
Startup Workflow). Nothing in Steps 2-4 runs without this.

## Step 2: Extraction & Resolution (raw source -> Markdown, anchored to syllabus)

```
python3 02_parsers/<script>.py <path under 01_raw_sources/> [--out 03_knowledge_base/Topic_XX_Name.md]
```

- Parsers live in `02_parsers/`; one script per source type is fine (e.g. a
  docx class-notes parser, a PDF question/mark-scheme parser). This step is
  mechanical and deterministic -- no `.tex` output, ever.
- Output must land in `03_knowledge_base/` using the `Topic_XX_Name.md`
  convention (see `CLAUDE.md` for the numbering rule).
- If `Topic_XX_Name.md` already exists, the class-notes parser appends the
  new source as its own section rather than overwriting -- a topic's
  Markdown accumulates from multiple raw sources over time.
- `03_knowledge_base/` is a living database (see `docs/ARCHITECTURE.md` and
  `CLAUDE.md` RULE 7): the agent may also hand-edit a file directly to fix
  formatting/OCR defects or merge in content, not only via re-running a
  parser. Refining presentation is always fine; inventing content never is.
- Before pulling anything from `03_knowledge_base/` into a generation run,
  resolve the Target Prompt/Study Plan's requested competencies against
  `00_syllabus/` first (the Syllabus Anchor, `CLAUDE.md` RULE 8) -- its
  terminology, scope, and depth override the knowledge base, never the
  reverse.

## Step 3: Synthesis & Layout (Markdown + template -> .tex)

`05_output/` generation is structurally agnostic (`CLAUDE.md` RULE 8,
Dynamic Assembly in `docs/ARCHITECTURE.md`) -- there's no single fixed
"notes" or "worksheet" shape. Structure comes exclusively from
`04_templates/`; content comes exclusively from the `03_knowledge_base/`
files the Target Prompt/Study Plan named. Example, class notes for one
topic:

> Using `03_knowledge_base/Topic_01_Data_Representation.md` and the blueprint
> in `04_templates/`, generate `05_output/Topic_01_Data_Representation.tex`.
> Use only the `stratbox`/`critbox`/`scenario` environments defined in the
> template. Mark any section with no matching knowledge-base content as
> `% TODO: Insufficient source content` — do not invent content.

For a worksheet, point at the parsed past-paper Markdown instead and ask for
`05_output/Topic_01_Data_Representation_Worksheet.tex`. For anything else
(a multi-topic quiz, a bootcamp pack, a standalone mark scheme), the same
rules apply: pull the sources the prompt names, anchor against the
syllabus, trace every claim to the knowledge base, and use only the
template's defined structure.

## Step 4: Output (.tex is the deliverable)

```
./compile.sh Topic_01_Data_Representation.tex
```

- The `.tex` file written to `05_output/` is the production deliverable.
  Final client-facing PDF delivery is out of scope (`CLAUDE.md`
  MODEL-ROUTING & OUTPUT BOUNDARY POLICY).
- `compile.sh` runs `pdflatex` inside `05_output/` purely as a passive
  syntax-health check and prints `PASS` (exit code 0) or `FAIL` (with the
  first LaTeX errors from the log). A PDF is an incidental byproduct of
  that check, not something this step needs to polish or ship.
- A feature is not `passing` in `feature_list.json` until this reports PASS
  and the PASS output is recorded as evidence.
- Update `claude-progress.md` and `feature_list.json` per `CLAUDE.md`'s
  "Before You Stop" section before ending the session.
