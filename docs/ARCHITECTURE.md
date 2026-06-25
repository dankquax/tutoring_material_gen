# Architecture

## Data Flow

```
01_raw_sources/              02_parsers/                03_knowledge_base/
  class_notes_docs/   --read-->  *.py  --write-->          Topic_XX_Name.md
  past_papers/                 (Python 3,                  (clean Markdown,
  syllabus/                     no .tex output)             one file per
  notes_bank/                                                topic/source-type)
  question_bank/
  latex_template_sample/
                                                                   |
                                                                   | read
                                                                   v
04_templates/                                          [agent authoring step]
  master blueprint .tex          ---------read--------->        |
  (stratbox, critbox,                                            | write
   scenario environments)                                        v
                                                        05_output/
                                                          Topic_XX_Name.tex
                                                          Topic_XX_Name_Worksheet.tex
                                                                   |
                                                                   | pdflatex
                                                                   | (compile.sh)
                                                                   v
                                                        05_output/Topic_XX_Name.pdf
```

## Directories

| Directory | Reads from | Writes to | Owner |
| --- | --- | --- | --- |
| `01_raw_sources/` | (external: docx/pdf source material) | — (read-only) | human/maintainer |
| `02_parsers/` | `01_raw_sources/` | `03_knowledge_base/` | Python scripts |
| `03_knowledge_base/` | — | — (target of parsers) | parsers |
| `04_templates/` | — | — | maintainer (structure only) |
| `05_output/` | `03_knowledge_base/` + `04_templates/` | itself (`.tex`, `.pdf`, logs) | agent authoring + `compile.sh` |

No step writes back upstream. `02_parsers/` never touches `05_output/`; the
agent authoring step never touches `01_raw_sources/` or `02_parsers/`.

## Why this shape

- **One-way flow** means a bad generation can always be regenerated from
  `03_knowledge_base/` + `04_templates/` without re-deriving from raw PDFs/docx.
- **Parsers vs. agent authoring are separate steps** because parsing is
  mechanical (docx/pdf -> Markdown) and deterministic, while LaTeX authoring
  requires judgment about template structure and must be auditable for
  hallucination — keeping them separate makes each independently verifiable.
- **`04_templates/` has no content** so the same blueprint can be reused
  across all 10 syllabus topics without drift.
