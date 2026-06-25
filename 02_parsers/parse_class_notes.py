#!/usr/bin/env python3
"""Parse a class-notes file (PDF or DOCX) in 01_raw_sources/ into clean
Markdown in 03_knowledge_base/.

Usage:
    python parse_class_notes.py <input.pdf|.docx> --topic 01 --name Data_Representation

Reads ONLY from 01_raw_sources/. Writes ONLY into 03_knowledge_base/, using
the Topic_XX_Name.md naming convention (official syllabus numbering -- see
00_syllabus/). If the target file already exists, the parsed content is
APPENDED as a new section rather than overwritten, since a topic's
Markdown is meant to accumulate from multiple raw sources (e.g. a full
notes PDF and a separate summary docx) without losing earlier work.

PDF heuristics are tuned to this department's notes style: short
header-like lines, "-"/bullet-glyph exam-style points, and number-table
blocks for conversions (kept as fenced code blocks).

DOCX extraction relies on real structural signals instead of text shape:
a paragraph is a heading only if ALL of its text is bold, and a bullet
only if Word's own list numbering (`<w:numPr>`) is present. Processing
stops entirely at a paragraph reading exactly "Worksheet" or "Answers" --
in this department's summary template that marks an appendix of
past-paper references with no real text (pasted screenshots), not notes
content.
"""

import argparse
import re
import sys
from pathlib import Path

import docx
import pdfplumber

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_SOURCES_DIR = ROOT_DIR / "01_raw_sources"
KNOWLEDGE_BASE_DIR = ROOT_DIR / "03_knowledge_base"

SUBSECTION_RE = re.compile(r"^\d+\.\d+\s+\S")
NUMBERED_HEADING_RE = re.compile(r"^\d+\.\s+[A-Z][a-zA-Z ]{2,40}$")
BULLET_RE = re.compile(r"^[-•●–—«]\s*")
TABLE_ROW_RE = re.compile(r"^[\d\sA-Fa-f.,+\-=()%]+$")
DOCX_STOP_HEADINGS = {"worksheet", "answers"}


# --- PDF extraction --------------------------------------------------------

def extract_pdf_lines(pdf_path: Path) -> list[str]:
    lines: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1.5) or ""
            for raw_line in text.split("\n"):
                line = raw_line.strip()
                if line:
                    lines.append(line)
    return lines


def is_pdf_heading(line: str) -> bool:
    if BULLET_RE.match(line):
        return False
    if TABLE_ROW_RE.match(line):
        return False
    if SUBSECTION_RE.match(line):
        return True
    word_count = len(line.split())
    ends_mid_sentence = line.endswith((".", ",", ";")) and not line.endswith("...")
    return word_count <= 7 and not ends_mid_sentence and line[0].isalpha() and line[0].isupper()


def is_table_row(line: str) -> bool:
    return bool(TABLE_ROW_RE.match(line)) and any(ch.isdigit() for ch in line)


def pdf_to_markdown_lines(pdf_path: Path) -> list[str]:
    lines = extract_pdf_lines(pdf_path)
    out: list[str] = []
    table_buffer: list[str] = []

    def flush_table():
        if table_buffer:
            out.append("```")
            out.extend(table_buffer)
            out.append("```")
            out.append("")
            table_buffer.clear()

    # Drop the source's own first line (its title) -- the caller emits its own H1.
    body = lines[1:] if lines else []

    for line in body:
        if is_table_row(line):
            table_buffer.append(line)
            continue
        flush_table()

        if SUBSECTION_RE.match(line):
            out.append(f"## {line}")
            out.append("")
        elif NUMBERED_HEADING_RE.match(line) or is_pdf_heading(line):
            out.append(f"### {line}")
            out.append("")
        elif BULLET_RE.match(line):
            out.append(f"- {BULLET_RE.sub('', line)}")
        else:
            out.append(line)
            out.append("")

    flush_table()
    return out


# --- DOCX extraction --------------------------------------------------------

def is_docx_heading(paragraph) -> bool:
    runs = [r for r in paragraph.runs if r.text.strip()]
    if not runs:
        return False
    if not all(r.bold for r in runs):
        return False
    text = paragraph.text.strip()
    if len(text) <= 80:
        return True
    # Numbered subsection titles (e.g. "4.2 Programming Languages, ...") are
    # an unambiguous structural marker even when long -- don't drop them
    # just because the title itself runs past the generic length cap.
    return bool(SUBSECTION_RE.match(text))


def is_docx_list_item(paragraph) -> bool:
    return "<w:numPr>" in paragraph._p.xml


def docx_table_to_markdown(table) -> list[str]:
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    if not rows:
        return []
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(["---"] * len(rows[0])) + "|"]
    for row in rows[1:]:
        out.append("| " + " | ".join(row) + " |")
    out.append("")
    return out


def docx_to_markdown_lines(docx_path: Path) -> list[str]:
    document = docx.Document(docx_path)
    out: list[str] = []
    first_heading_seen = False

    for block in document.iter_inner_content():
        if isinstance(block, docx.table.Table):
            out.extend(docx_table_to_markdown(block))
            continue

        text = block.text.strip()
        if not text:
            continue

        # Checked regardless of formatting -- in this department's summary
        # template, "Worksheet"/"Answers" are NOT bold in the source XML
        # despite reading visually as section labels, so heading detection
        # alone won't catch them.
        if text.lower() in DOCX_STOP_HEADINGS:
            break

        if is_docx_heading(block):
            if not first_heading_seen:
                # Drop the source's own title -- the caller emits its own H1.
                first_heading_seen = True
                continue
            if re.match(r"^\d+\.\d+\s+\S", text):
                out.append(f"## {text}")
            elif re.match(r"^\d+\.\s+\S", text):
                out.append(f"## {text}")
            elif re.match(r"^[a-z]\.\s+\S", text):
                out.append(f"### {text}")
            else:
                out.append(f"#### {text}")
            out.append("")
        elif is_docx_list_item(block):
            out.append(f"- {text}")
        else:
            out.append(text)
            out.append("")

    return out


# --- Shared output ----------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path, help="Path to a .pdf or .docx under 01_raw_sources/")
    parser.add_argument("--topic", required=True, help="Two-digit syllabus topic number, e.g. 01")
    parser.add_argument("--name", required=True, help="Topic name in Topic_XX_Name form, e.g. Data_Representation")
    args = parser.parse_args()

    input_file = args.input_file.resolve()
    try:
        input_file.relative_to(RAW_SOURCES_DIR.resolve())
    except ValueError:
        print(f"FAIL: input must be under {RAW_SOURCES_DIR} (got {input_file})", file=sys.stderr)
        return 1
    if not input_file.is_file():
        print(f"FAIL: {input_file} does not exist.", file=sys.stderr)
        return 1

    suffix = input_file.suffix.lower()
    if suffix == ".pdf":
        body_lines = pdf_to_markdown_lines(input_file)
    elif suffix == ".docx":
        body_lines = docx_to_markdown_lines(input_file)
    else:
        print(f"FAIL: unsupported file type {suffix} (expected .pdf or .docx)", file=sys.stderr)
        return 1

    if not body_lines:
        print(f"FAIL: no content extracted from {input_file}.", file=sys.stderr)
        return 1

    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = KNOWLEDGE_BASE_DIR / f"Topic_{args.topic}_{args.name}.md"
    title = f"Topic {int(args.topic)}: {args.name.replace('_', ' ')}"

    if output_path.exists():
        existing = output_path.read_text(encoding="utf-8").rstrip()
        section = "\n".join([f"## Additional Source: {input_file.name}", ""] + body_lines).rstrip()
        markdown = existing + "\n\n" + section + "\n"
        mode = "appended to"
    else:
        markdown = "\n".join([f"# {title}", ""] + body_lines).rstrip() + "\n"
        mode = "wrote"

    output_path.write_text(markdown, encoding="utf-8")
    print(f"PASS: {mode} {output_path} ({len(body_lines)} new lines from {input_file.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
