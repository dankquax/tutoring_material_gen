#!/usr/bin/env python3
"""Link an official Cambridge question paper (QP) with its mark scheme (MS)
into one Markdown file in 03_knowledge_base/, keyed by question-part label
(e.g. 1(a), 1(c)(ii)).

Usage:
    python parse_past_paper.py <qp.pdf> <ms.pdf> --code 0478_s20_11

Reads ONLY from 01_raw_sources/. Writes ONLY into 03_knowledge_base/.

Scope note: targets the official year-by-paper PDFs under
01_raw_sources/past_papers/<year>/, which have a real text layer. The
pre-sorted-by-topic 01_raw_sources/past_papers/topical/ folder is a
third-party screenshot compilation with no extractable text -- it is out
of scope for this script (would need OCR; see project notes). Output here
is NOT topic-tagged: a single paper covers many syllabus topics. Mapping
each linked Q&A pair to a Topic_XX file is a separate, later step.
"""

import argparse
import re
import sys
from pathlib import Path

import pdfplumber

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_SOURCES_DIR = ROOT_DIR / "01_raw_sources"
KNOWLEDGE_BASE_DIR = ROOT_DIR / "03_knowledge_base"

PAPER_CODE_RE = re.compile(r"^\d{4}/\d+(/[A-Z]/[A-Z]/\d+)?$")
PAGE_NUM_RE = re.compile(r"^\d+$")
DOTTED_BLANK_RE = re.compile(r"\.{5,}")
BOILERPLATE_RE = re.compile(
    r"^(PUBLISHED|BLANK PAGE|Question\s+Answer\s+Marks|GENERIC MARKING PRINCIPLE|"
    r"PhysicsAndMathsTutor\.com|.*UCLES.*|Cambridge IGCSE.*|.*Page \d+ of \d+.*)$",
    re.IGNORECASE,
)

# Recent QP printings add a rotated "DO NOT WRITE IN THIS MARGIN" strip down
# the page edge plus a scan barcode; pdfplumber recovers the watermark as
# one all-caps word per line (its letters AND word order both reversed --
# "DO NOT WRITE IN THIS MARGIN" becomes "NIGRAM SIHT NI ETIRW TON OD" before
# the line-split), and the barcode/some symbol-font glyphs as unmapped
# "(cid:N)" tokens. Neither carries real content, so both are stripped.
CID_GLYPH_RE = re.compile(r"\(cid:\d+\)")
MARGIN_WATERMARK_WORDS = {"NIGRAM", "SIHT", "NI", "ETIRW", "TON", "OD"}
BARCODE_RE = re.compile(r"^\*\s*\d+\s*\*$")

# Tick-box questions render their checkmark as a symbol-font glyph in the
# Unicode Private Use Area (e.g. U+F0FC for a Wingdings-style checkbox).
# Extraction recovers the character itself but not which column/row it was
# visually aligned to, so 2+ of them signal lost positional information.
PUA_GLYPH_RE = re.compile(r"[-]")

SUBPART_RE = re.compile(r"^\(([a-z])\)\s+(.*)$")
SUBSUBPART_RE = re.compile(r"^\(([ivx]+)\)\s+(.*)$")
MAIN_Q_RE = re.compile(r"^(\d+)\s+([A-Z(].*)$")


def is_boilerplate(line: str) -> bool:
    return bool(
        PAPER_CODE_RE.match(line)
        or PAGE_NUM_RE.match(line)
        or DOTTED_BLANK_RE.search(line)
        or BOILERPLATE_RE.match(line)
    )


def extract_lines(pdf_path: Path) -> list[str]:
    """Extracts text lines, dropping boilerplate and stopping entirely once the
    closing copyright notice is reached (it runs on with no question markers,
    so nothing after it can be reliably attributed to a question part)."""
    lines: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1.5) or ""
            for raw_line in text.split("\n"):
                line = CID_GLYPH_RE.sub("", raw_line).strip()
                if line.startswith("Permission to reproduce"):
                    return lines
                if not line or line in MARGIN_WATERMARK_WORDS or BARCODE_RE.match(line):
                    continue
                if not is_boilerplate(line):
                    lines.append(line)
    return lines


def parse_qp(lines: list[str]) -> dict[str, str]:
    """Returns {part_label: question_text}, e.g. {'1(a)': '...', '1(c)(ii)': '...'}."""
    parts: dict[str, list[str]] = {}
    current_main = ""
    current_sub = ""
    current_label = ""
    expected_main = 1

    def close_part():
        if current_label and current_label not in parts:
            parts[current_label] = []

    for line in lines:
        remaining = line

        # A main-question marker is only ever the first thing on a line, but
        # CIE often prints its first sub-part marker right after it on the
        # *same* line (e.g. "4 (a) Tickets for a theme park..."), so only
        # peel this off once before falling into the sub/sub-sub loop below.
        m_main = MAIN_Q_RE.match(remaining)
        # Programming questions often show line-numbered pseudocode/algorithm
        # listings ("01", "02", ... "17") for the candidate to trace or
        # complete. Zero-padded numbers are never real CIE question numbers
        # but can coincidentally equal expected_main (e.g. listing line "07"
        # when question 7 hasn't appeared yet), which would otherwise hijack
        # the counter and silently swallow every following real question as
        # a continuation of the listing's last line.
        if m_main and not m_main.group(1).startswith("0") and int(m_main.group(1)) == expected_main:
            current_main = m_main.group(1)
            current_sub = ""
            current_label = current_main
            expected_main += 1
            close_part()
            remaining = m_main.group(2)

        # A sub-part letter and its own first sub-sub-part roman numeral can
        # likewise share one line (e.g. "(a) (i) Identify..."), so peel off
        # every marker sitting at the front of what's left, not just one.
        while True:
            m_subsub = SUBSUBPART_RE.match(remaining)
            # "(i)" is ambiguous between a roman-numeral sub-sub-part and a
            # literal sub-part letter "i" -- once inside a lettered sub-part,
            # treat an [ivx]+ marker as nesting under it, not as a sibling.
            if m_subsub and current_main and current_sub:
                current_label = f"{current_main}({current_sub})({m_subsub.group(1)})"
                close_part()
                remaining = m_subsub.group(2)
                continue
            m_sub = SUBPART_RE.match(remaining)
            if m_sub and current_main:
                current_sub = m_sub.group(1)
                current_label = f"{current_main}({current_sub})"
                close_part()
                remaining = m_sub.group(2)
                continue
            break

        if current_label and remaining:
            parts.setdefault(current_label, []).append(remaining)

    return {label: " ".join(text_lines).strip() for label, text_lines in parts.items()}


def format_answer_cell(text: str) -> str:
    """Turns one Answer cell's raw text (PDF line-wraps preserved as \\n) into
    either a flowing paragraph (prose with no marking-point bullets) or a
    Markdown list (lines that start with a dash are separate marking points
    -- CIE mark schemes write these as e.g. "Any two from: / - Speaker / -
    Touchscreen"). A non-dash line is folded into whichever group precedes
    it, since it's a wrapped continuation of that line, not a new point."""
    raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
    groups: list[str] = []
    for line in raw_lines:
        if re.match(r"^[-−–—•]\s*", line):
            groups.append(re.sub(r"^[-−–—•]\s*", "- ", line))
        elif groups:
            groups[-1] += " " + line
        else:
            groups.append(line)
    return "\n".join(groups)


def parse_ms(pdf_path: Path) -> dict[str, dict]:
    """Returns {part_label: {'answer': str, 'marks': str}}.

    Cambridge mark schemes render the Question/Answer/Marks grid as a real
    bordered table -- pdfplumber's find_tables() reads it directly off the
    PDF's own grid lines (each logical column comes back split into 3
    sub-columns by faint internal rulings, so every row has a width that's a
    multiple of 3; the real content is the first non-empty cell in each
    third). This replaces an earlier hardcoded-x-position approach (label
    x0<120, answer 120<=x0<700, marks x0>=700) that worked for the one paper
    it was tuned against but silently produced zero matches on others, since
    different print runs shift the real column edges by tens of points.
    Nested sub-tables (e.g. a tick-grid or truth-table embedded inside one
    Answer cell) are returned by find_tables() as their own separate table
    too, with an unrelated column count that can still coincidentally be a
    multiple of 3 -- and a bare digit in their own data (e.g. a truth
    table's "0"/"1" output column) can coincidentally collide with a real
    question's number. Requiring the table's own literal "Question" header
    cell confirms it's the genuine grid and not one of these, which also
    means a long answer that spans a page break -- CIE re-prints the
    question-number label at the top of the new page's table when this
    happens -- can be safely glued back onto the same entry instead of one
    chunk silently overwriting the other.
    """
    entries: dict[str, dict] = {}
    LABEL_RE = re.compile(r"^\d+(\([a-z]+\))*$")

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.find_tables():
                rows = table.extract()
                if not rows or len(rows[0]) % 3 != 0:
                    continue
                col_width = len(rows[0]) // 3
                has_header = any(
                    (next((c for c in row[:col_width] if c), "") or "").strip() == "Question"
                    for row in rows
                )
                if not has_header:
                    continue

                current_label = ""
                current_answer: list[str] = []
                current_marks = ""

                def flush():
                    if not current_label:
                        return
                    formatted = "\n".join(current_answer).strip()
                    if current_label in entries:
                        entries[current_label]["answer"] = (
                            entries[current_label]["answer"] + "\n" + formatted
                        ).strip()
                        if current_marks and not entries[current_label]["marks"]:
                            entries[current_label]["marks"] = current_marks
                    else:
                        entries[current_label] = {"answer": formatted, "marks": current_marks}

                for row in rows:
                    label_group = row[:col_width]
                    answer_group = row[col_width:2 * col_width]
                    marks_group = row[2 * col_width:]
                    label_text = (next((c for c in label_group if c), "") or "").strip()
                    answer_raw = next((c for c in answer_group if c), "") or ""
                    marks_text = " ".join((next((c for c in marks_group if c), "") or "").split())

                    # No is_boilerplate() check here -- it's tuned for whole
                    # extracted PDF lines (page numbers, paper codes), and a
                    # bare single/double-digit question label like "1" or
                    # "3" satisfies its PAGE_NUM_RE check too, which would
                    # silently drop that question's MS entry. Table cells
                    # can't contain stray running-header/footer text in the
                    # first place (it lives outside the table's grid), so
                    # the LABEL_RE match below is the only filter needed.
                    if not label_text and not answer_raw and not marks_text:
                        continue

                    if LABEL_RE.match(label_text):
                        flush()
                        current_label = label_text
                        current_answer = [format_answer_cell(answer_raw)] if answer_raw else []
                        current_marks = marks_text
                    elif current_label and answer_raw:
                        current_answer.append(format_answer_cell(answer_raw))
                        if marks_text and not current_marks:
                            current_marks = marks_text
                flush()

    return entries


def to_markdown(paper_code: str, qp_parts: dict[str, str], ms_entries: dict[str, dict]) -> str:
    out = [f"# Past Paper {paper_code}: Linked Questions and Mark Scheme", ""]

    def sort_key(label: str):
        nums = re.findall(r"\d+|[a-z]+", label)
        return [int(n) if n.isdigit() else n for n in nums]

    # A stem can be a bare main question ("4") or a lettered sub-part that
    # itself introduces roman-numeral children ("4(c)" before "4(c)(i)") --
    # only what matters is whether something else nests directly under it.
    is_stem_only = {
        label: any(other.startswith(f"{label}(") for other in qp_parts)
        for label in qp_parts
    }

    for label in sorted(qp_parts, key=sort_key):
        question = qp_parts[label]
        ms = ms_entries.get(label)
        out.append(f"## Question {label}")
        out.append("")
        out.append(f"**Question:** {question}")
        out.append("")
        if ms:
            marks_suffix = f" ({ms['marks']} mark{'s' if ms['marks'] != '1' else ''})" if ms["marks"] else ""
            out.append(f"**Mark scheme{marks_suffix}:**")
            out.append("")
            out.append(ms["answer"] if ms["answer"] else "% TODO: Insufficient source content")
            if len(PUA_GLYPH_RE.findall(question)) >= 2 or len(PUA_GLYPH_RE.findall(ms["answer"])) >= 2:
                out.append("")
                out.append(
                    "_Note: this question uses a symbol-font glyph that didn't extract "
                    "as normal text (e.g. a tick-box checkmark, or a pseudocode "
                    "assignment arrow `<-`) -- some detail may be lost above, verify "
                    "against the source PDF before using this as a complete answer._"
                )
        elif is_stem_only[label]:
            out.append("_(Scenario introduction for the parts below -- not individually marked.)_")
        else:
            out.append("**Mark scheme:** % TODO: Insufficient source content -- no matching MS entry found")
        out.append("")

    unmatched = sorted(set(ms_entries) - set(qp_parts), key=sort_key)
    if unmatched:
        out.append("## Unmatched Mark Scheme Entries (no corresponding QP part found)")
        out.append("")
        for label in unmatched:
            out.append(f"- {label}: {ms_entries[label]['answer']}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qp_pdf", type=Path)
    parser.add_argument("ms_pdf", type=Path)
    parser.add_argument("--code", required=True, help="Paper code for the output filename, e.g. 0478_s20_11")
    args = parser.parse_args()

    qp_pdf = args.qp_pdf.resolve()
    ms_pdf = args.ms_pdf.resolve()
    for path in (qp_pdf, ms_pdf):
        try:
            path.relative_to(RAW_SOURCES_DIR.resolve())
        except ValueError:
            print(f"FAIL: input must be under {RAW_SOURCES_DIR} (got {path})", file=sys.stderr)
            return 1
        if not path.is_file():
            print(f"FAIL: {path} does not exist.", file=sys.stderr)
            return 1

    qp_lines = extract_lines(qp_pdf)
    qp_parts = parse_qp(qp_lines)
    ms_entries = parse_ms(ms_pdf)

    if not qp_parts:
        print(f"FAIL: no question parts detected in {qp_pdf}.", file=sys.stderr)
        return 1

    markdown = to_markdown(args.code, qp_parts, ms_entries)

    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = KNOWLEDGE_BASE_DIR / f"PastPaper_{args.code}.md"
    output_path.write_text(markdown, encoding="utf-8")

    matched = sum(1 for label in qp_parts if label in ms_entries)
    print(f"PASS: wrote {output_path} ({len(qp_parts)} question parts, {matched} matched to a mark scheme entry)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
