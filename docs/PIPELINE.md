# Pipeline: Running Parsers and Generating Documents

## 1. Run a parser (raw source -> Markdown)

```
python3 02_parsers/<script>.py <path under 01_raw_sources/> [--out 03_knowledge_base/Topic_XX_Name.md]
```

- Parsers live in `02_parsers/`; one script per source type is fine (e.g. a
  docx class-notes parser, a PDF question/mark-scheme parser).
- Output must land in `03_knowledge_base/` using the `Topic_XX_Name.md`
  convention (see `CLAUDE.md` for the numbering rule).
- Re-running a parser on the same source should overwrite its own output
  deterministically — never hand-edit a generated Markdown file in place
  without noting it, since the next parser run will silently clobber it.

## 2. Command the agent to build a document (Markdown + template -> .tex)

Give the agent a prompt naming the exact topic and source files, e.g.:

> Using `03_knowledge_base/Topic_01_Data_Representation.md` and the blueprint
> in `04_templates/`, generate `05_output/Topic_01_Data_Representation.tex`.
> Use only the `stratbox`/`critbox`/`scenario` environments defined in the
> template. Mark any section with no matching knowledge-base content as
> `% TODO: Insufficient source content` — do not invent content.

For a worksheet, point at the parsed past-paper Markdown instead and ask for
`05_output/Topic_01_Data_Representation_Worksheet.tex`.

## 3. Compile and verify

```
./compile.sh Topic_01_Data_Representation.tex
```

- `compile.sh` runs `pdflatex` inside `05_output/` and prints `PASS` (with
  the PDF path) or `FAIL` (with the first LaTeX errors from the log).
- A feature is not `passing` in `feature_list.json` until this reports PASS
  and the PASS output is recorded as evidence.

## 4. Record state

Update `claude-progress.md` and `feature_list.json` per `CLAUDE.md`'s
"Before You Stop" section before ending the session.
