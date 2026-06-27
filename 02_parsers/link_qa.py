#!/usr/bin/env python3
"""
link_qa.py — FEAT-007: Regex Q&A Sorter & Linker.

Reads staged QP and MS Markdown files from 03_knowledge_base/_staging/,
splits them by Cambridge numbering using a regex state machine
(1 / (a) / (i)), links matching QP chunks to MS chunks, and writes a
structured JSON of paired Q&A blocks to _staging/.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = REPO_ROOT / "03_knowledge_base" / "_staging"

# Cambridge numbering state-machine patterns.
# [1-9]\d? (not \d{1,2}) intentionally excludes zero-padded pseudocode line
# numbers like "01 DECLARE..." that would otherwise trigger false question matches.
MAIN_Q_RE      = re.compile(r"^(?:-\s+)?([1-9]\d?)(?=\s+[A-Za-z])")
# Catches "- 4 (a) Text" where question number and first sub-part share a line
MAIN_PART_RE   = re.compile(r"^(?:-\s+)?([1-9]\d?)\s+\(([a-z])\)(?:\s|$)")
PART_RE        = re.compile(r"^(?:-\s+)?\(([a-z])\)(?:\s|$)")
# Restricted to ivx so alphabetic parts (c, d, etc.) never match here
SUBPART_RE     = re.compile(r"^(?:-\s+)?\(([ivx]+)\)(?:\s|$)")

# Lines to skip unconditionally (HTML comments, MS section headers, comma padding)
_SKIP_LINE_RE = re.compile(
    r"^<!--.*-->$"                  # Docling image placeholders
    r"|^#{1,6}\s+Cambridge\s+IGCSE" # MS inter-table section headers
    r"|^#{1,6}\s*[,\s]+$"           # Docling-prefixed comma padding e.g. "## ,   ,"
    r"|^[,\s]+$",                   # Bare comma padding e.g. ",             ,"
    re.IGNORECASE,
)

# Roman numeral → integer for hierarchical sort
_ROMAN = {r: i + 1 for i, r in enumerate(
    ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"]
)}


def _is_garbage(line: str) -> bool:
    """Lines where >40% of chars are non-ASCII are printer/barcode watermarks."""
    if not line:
        return False
    return sum(1 for c in line if ord(c) > 127) / len(line) > 0.40


def _label(main: int, part: str = "", subpart: str = "") -> str:
    s = str(main)
    if part:
        s += f"({part})"
    if subpart:
        s += f"({subpart})"
    return s


def _sort_key(label: str) -> tuple:
    """Hierarchical sort: (main_num, part_ordinal, subpart_roman_value)."""
    m = re.match(r"^(\d+)(?:\(([a-z]+)\)(?:\(([ivx]+)\))?)?$", label)
    if not m:
        return (0, 0, 0)
    main = int(m.group(1))
    part_val = (ord(m.group(2)[0]) - ord("a") + 1) if m.group(2) else 0
    sub_val = _ROMAN.get(m.group(3) or "", 0)
    return (main, part_val, sub_val)


def _clean_body(lines: list[str]) -> str:
    """Join lines, strip whitespace, then remove trailing page-number artifacts.

    Page-corner numbers (e.g. "4", "10") only accumulate when there is
    substantial preceding content (multiple lines), so we only strip when
    len > 1.  This preserves short numeric MS answers like "11" or "66"
    which are the entire single-line body of their table cell.
    """
    lines = list(lines)  # work on a copy
    # Strip trailing blanks
    while lines and not lines[-1].strip():
        lines.pop()
    # Only strip trailing lone numerals when there is preceding content.
    if len(lines) > 1:
        while lines and re.match(r"^\d{1,2}$", lines[-1].strip()):
            lines.pop()
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def split_into_chunks(text: str, is_ms: bool = False, debug: bool = False) -> dict[str, str]:
    """
    State-machine splitter. Accumulates lines under each Cambridge-numbered
    label. Returns dict mapping label -> body text.

    is_ms=True enables label extraction from pipe-delimited mark-scheme tables.
    is_ms=False (QP mode) preserves table rows as raw content instead, so data
    tables (truth tables, trace tables) do not corrupt the label state machine.
    """
    chunks: dict[str, str] = {}
    current_label: str = "__preamble__"
    current_lines: list[str] = []
    main_q = 0
    part = ""
    subpart = ""
    in_fence = False  # True while inside a fenced code block (``` ... ```)

    def flush() -> None:
        if current_label and current_lines:
            body = _clean_body(current_lines)
            if body and current_label != "__preamble__":
                if current_label in chunks:
                    chunks[current_label] += "\n" + body
                else:
                    chunks[current_label] = body

    for raw_line in text.splitlines():
        stripped = raw_line.strip()

        # Skip margin warnings
        if "DO NOT WRITE IN THIS MARGIN" in stripped:
            continue

        # Skip garbage watermark lines (high non-ASCII density)
        if stripped and _is_garbage(stripped):
            if debug:
                print(f"  [GARBAGE] {stripped[:50]!r}")
            continue

        # Skip noise-only lines (HTML comments, MS headers, comma padding)
        if stripped and _SKIP_LINE_RE.match(stripped):
            if debug:
                print(f"  [SKIP]    {stripped[:60]!r}")
            continue

        # --- Table rows ---
        if stripped.startswith("|"):
            if is_ms:
                # MS mode: extract label from first cell of mark-scheme tables
                cells = [c.strip() for c in stripped.split("|") if c.strip()]
                # Skip separator rows like |---|---|
                if len(cells) >= 2 and not re.match(r"^[-:]+$", cells[0]):
                    q_val_clean = cells[0].replace(" ", "")
                    if re.match(r"^\d+(?:\([a-z]+\))?(?:\([ivx]+\))?$", q_val_clean):
                        flush()
                        current_label = q_val_clean
                        current_lines = [cells[1].strip()]
                        if debug:
                            print(f"  [TABLE]   label={current_label!r} content={cells[1][:40]!r}")
            else:
                # QP mode: preserve table rows as content (truth tables, trace tables,
                # database tables are part of the question, not label boundaries)
                current_lines.append(stripped)
                if debug:
                    print(f"  [TABLE]   (QP content) {stripped[:60]!r}")
            continue

        # --- Blank lines ---
        if not stripped:
            current_lines.append("")
            continue

        # --- State machine ---
        m_main      = MAIN_Q_RE.match(stripped)
        m_main_part = MAIN_PART_RE.match(stripped)
        m_part      = PART_RE.match(stripped)
        m_sub       = SUBPART_RE.match(stripped)

        if m_sub and main_q and part:
            flush()
            subpart = m_sub.group(1)
            current_label = _label(main_q, part, subpart)
            current_lines = [stripped[len(m_sub.group(0)):]]
            if debug:
                print(f"  [SUBPART] {current_label!r}")
        elif m_part and main_q:
            flush()
            part = m_part.group(1)
            subpart = ""
            current_label = _label(main_q, part)
            current_lines = [stripped[len(m_part.group(0)):]]
            if debug:
                print(f"  [PART]    {current_label!r}")
        elif m_main_part:
            # "- N (a) text" — question number and first sub-part on same line
            flush()
            main_q = int(m_main_part.group(1))
            part = m_main_part.group(2)
            subpart = ""
            current_label = _label(main_q, part)
            current_lines = [stripped[len(m_main_part.group(0)):]]
            if debug:
                print(f"  [MAIN+PT] {current_label!r}")
        elif m_main:
            flush()
            main_q = int(m_main.group(1))
            part = ""
            subpart = ""
            current_label = _label(main_q)
            current_lines = [stripped[len(m_main.group(0)):]]
            if debug:
                print(f"  [MAIN]    {current_label!r}")
        else:
            current_lines.append(stripped)

    flush()
    return chunks


def link_qa(qp_md: Path, ms_md: Path, debug: bool = False) -> list[dict]:
    qp_chunks = split_into_chunks(qp_md.read_text(encoding="utf-8"), is_ms=False, debug=debug)
    ms_chunks = split_into_chunks(ms_md.read_text(encoding="utf-8"), is_ms=True,  debug=debug)

    all_labels = sorted(set(qp_chunks) | set(ms_chunks), key=_sort_key)
    return [
        {
            "label": label,
            "question": qp_chunks.get(label, ""),
            "mark_scheme": ms_chunks.get(label, ""),
        }
        for label in all_labels
    ]


def validate_pairs(pairs: list[dict]) -> list[str]:
    """
    Scan linked pairs for structural anomalies.
    Returns a list of anomaly strings; empty list = clean.
    """
    anomalies = []
    label_set = {p["label"] for p in pairs}

    # Check for preamble leakage
    if "__preamble__" in label_set:
        anomalies.append("PREAMBLE_LEAK: __preamble__ key found in output pairs")

    for entry in pairs:
        label = entry["label"]
        q  = entry["question"].strip()
        ms = entry["mark_scheme"].strip()

        # A label is a leaf if no other label starts with label + "("
        prefix = label + "("
        is_leaf = not any(other.startswith(prefix) for other in label_set if other != label)

        if is_leaf:
            if q and not ms:
                anomalies.append(f"MISSING_MS  [{label}]: question present, mark scheme empty")
            if ms and not q:
                anomalies.append(f"MISSING_Q   [{label}]: mark scheme present, question empty")

    # Check sequential ordering of main question numbers
    main_nums = sorted(
        int(re.match(r"^(\d+)$", p["label"]).group(1))
        for p in pairs
        if re.match(r"^(\d+)$", p["label"])
    )
    for i in range(1, len(main_nums)):
        if main_nums[i] != main_nums[i - 1] + 1:
            anomalies.append(
                f"SEQ_GAP: Q{main_nums[i-1]} followed by Q{main_nums[i]} "
                f"(expected Q{main_nums[i-1]+1})"
            )

    return anomalies


def find_pairs(staging_dir: Path) -> list[tuple[Path, Path, str]]:
    qp_re = re.compile(r"^(.+)_qp_(\d+)\.md$", re.IGNORECASE)
    ms_re = re.compile(r"^(.+)_ms_(\d+)\.md$", re.IGNORECASE)

    qp_map: dict[str, Path] = {}
    ms_map: dict[str, Path] = {}
    for f in sorted(staging_dir.glob("*.md")):
        m_qp = qp_re.match(f.name)
        m_ms = ms_re.match(f.name)
        if m_qp:
            key = f"{m_qp.group(1)}__{m_qp.group(2)}"
            qp_map[key] = f
        elif m_ms:
            key = f"{m_ms.group(1)}__{m_ms.group(2)}"
            ms_map[key] = f

    pairs = []
    all_qp_keys = set(qp_map)
    all_ms_keys = set(ms_map)

    for key, qp_path in qp_map.items():
        if key in ms_map:
            paper_code = re.sub(r"_qp_(\d+)$", r"_\1", qp_path.stem, flags=re.IGNORECASE)
            pairs.append((qp_path, ms_map[key], paper_code))
        else:
            print(f"WARNING: QP without matching MS skipped: {qp_path.name}")

    for key in all_ms_keys - all_qp_keys:
        print(f"WARNING: MS without matching QP skipped: {ms_map[key].name}")

    return pairs


def write_linked_json(pairs: list[dict], source: str, out_path: Path) -> None:
    out_path.write_text(
        json.dumps({"source": source, "pairs": pairs}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qp_md", nargs="?", help="Path to QP Markdown file")
    parser.add_argument("ms_md", nargs="?", help="Path to MS Markdown file")
    parser.add_argument("--out", help="Output JSON path")
    parser.add_argument("--batch", action="store_true", help="Batch processing mode")
    parser.add_argument("--debug", action="store_true", help="Verbose state-machine trace")
    args = parser.parse_args()

    if args.batch:
        pairs_found = find_pairs(STAGING_DIR)
        if not pairs_found:
            print(f"No valid QP/MS pairs found in: {STAGING_DIR}")
            return 0

        total_anomalies = 0
        for qp_path, ms_path, paper_code in pairs_found:
            linked = link_qa(qp_path, ms_path, debug=args.debug)
            anomalies = validate_pairs(linked)
            out = STAGING_DIR / f"{paper_code}_linked.json"
            write_linked_json(linked, paper_code, out)
            status = f"PASS ({len(linked)} pairs)" if not anomalies else f"WARN ({len(anomalies)} anomalies)"
            print(f"[{status}] {out.name}")
            for a in anomalies:
                print(f"  ! {a}")
            total_anomalies += len(anomalies)

        if total_anomalies:
            print(f"\nBatch complete — {total_anomalies} anomaly(s) require review.")
            return 1
        print(f"\nBatch complete — all pairs verified clean.")
        return 0

    if not args.qp_md or not args.ms_md:
        parser.print_help()
        return 1

    qp_path = Path(args.qp_md)
    ms_path = Path(args.ms_md)

    if args.debug:
        print(f"\n=== QP: {qp_path.name} ===")
        split_into_chunks(qp_path.read_text(encoding="utf-8"), is_ms=False, debug=True)
        print(f"\n=== MS: {ms_path.name} ===")
        split_into_chunks(ms_path.read_text(encoding="utf-8"), is_ms=True, debug=True)

    paper_code = re.sub(r"_qp_(\d+)$", r"_\1", qp_path.stem, flags=re.IGNORECASE)
    out_path = Path(args.out) if args.out else STAGING_DIR / f"{paper_code}_linked.json"

    linked = link_qa(qp_path, ms_path, debug=args.debug)
    anomalies = validate_pairs(linked)
    write_linked_json(linked, paper_code, out_path)

    print(f"SUCCESS: {len(linked)} pairs -> {out_path.name}")
    if anomalies:
        print(f"VALIDATION — {len(anomalies)} anomaly(s):")
        for a in anomalies:
            print(f"  ! {a}")
        return 1

    print(f"VALIDATION — clean (0 anomalies)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
