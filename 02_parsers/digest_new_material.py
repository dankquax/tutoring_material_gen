#!/usr/bin/env python3
"""
digest_new_material.py — Master ingestion orchestrator.

Scans 01_raw_sources/ for unprocessed files and runs the correct pipeline:

  Class notes (PDF / DOCX)
    -> parse_class_notes.py  (extracts Markdown to a temp file)
    -> merge_theory_ollama.py  (LLM-merges into Theory.md)

  Past papers (QP + MS PDF pairs)
    -> parse_past_paper.py  (links Q+MS into PastPaper_*.md at KB root)
    -> route_questions_ollama.py  (semantically routes into per-topic Past_Papers.md)

State is tracked in 01_raw_sources/.processed_files.json (SHA-256 keyed).
Files already in the state file are skipped.

Usage:
    python digest_new_material.py [--model llama3] [--dry-run]

Notes on file layout assumptions:
  Class notes: 01_raw_sources/class_notes_docs/<Topic_XX_Name>/<file>.pdf|.docx
               Parent directory name MUST match Topic_XX_Name (e.g. Topic_01_Data_Representation).
  Past papers: 01_raw_sources/past_papers/<year>/<code>_qp_<n>.pdf
                                                  <code>_ms_<n>.pdf
               QP and MS are paired by matching the paper code (everything before _qp/_ms).
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_SOURCES_DIR = REPO_ROOT / "01_raw_sources"
KB_DIR = REPO_ROOT / "03_knowledge_base"
PARSERS_DIR = REPO_ROOT / "02_parsers"
STATE_FILE = RAW_SOURCES_DIR / ".processed_files.json"

# Regex to extract topic number and name from a folder named Topic_XX_Name
TOPIC_FOLDER_RE = re.compile(r"^Topic_(\d{2})_(.+)$")

# QP / MS filename patterns:  <code>_qp_<n>.pdf  /  <code>_ms_<n>.pdf
QP_RE = re.compile(r"^(.+)_qp_(\d+)\.pdf$", re.IGNORECASE)
MS_RE = re.compile(r"^(.+)_ms_(\d+)\.pdf$", re.IGNORECASE)

DEFAULT_MODEL = "llama3.2:latest"


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.is_file():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def mark_processed(state: dict, key: str, note: str) -> None:
    state[key] = {"status": "processed", "note": note}


# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------

def run(cmd: list, dry_run: bool = False) -> bool:
    """Run a subprocess command. Returns True on success (exit 0)."""
    display = " ".join(str(c) for c in cmd)
    if dry_run:
        print(f"  [DRY-RUN] {display}")
        return True
    print(f"  RUN: {display}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print(f"  FAIL (exit {result.returncode}): {display}", file=sys.stderr)
        return False
    return True


# ---------------------------------------------------------------------------
# Class notes pipeline
# ---------------------------------------------------------------------------

def find_class_notes() -> list[tuple[Path, str, str]]:
    """
    Returns list of (file_path, topic_num, topic_name) for all class notes
    PDFs and DOCXs whose parent directory matches Topic_XX_Name.
    """
    notes_dir = RAW_SOURCES_DIR / "class_notes_docs"
    if not notes_dir.is_dir():
        return []

    results = []
    for f in sorted(notes_dir.rglob("*")):
        if f.suffix.lower() not in (".pdf", ".docx"):
            continue
        m = TOPIC_FOLDER_RE.match(f.parent.name)
        if not m:
            print(
                f"  SKIP (class note): {f.relative_to(RAW_SOURCES_DIR)} — "
                "parent directory name does not match Topic_XX_Name pattern.",
                file=sys.stderr,
            )
            continue
        results.append((f, m.group(1), m.group(2)))
    return results


def process_class_notes(state: dict, model: str, dry_run: bool) -> tuple[int, int]:
    """Returns (processed, errors)."""
    files = find_class_notes()
    if not files:
        print("  No class notes found under 01_raw_sources/class_notes_docs/")
        return 0, 0

    processed, errors = 0, 0
    for note_path, topic_num, topic_name in files:
        state_key = f"notes::{note_path.relative_to(RAW_SOURCES_DIR)}"
        h = file_hash(note_path)
        state_key_hash = f"{state_key}::{h}"

        if state_key_hash in state:
            print(f"  SKIP (already processed): {note_path.relative_to(RAW_SOURCES_DIR)}")
            continue

        print(f"\n[Class notes] {note_path.relative_to(RAW_SOURCES_DIR)}")
        topic_folder = f"Topic_{topic_num}_{topic_name}"

        # Step 1: parse_class_notes.py -> writes raw markdown to a temp file
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, prefix=f"parsed_{topic_folder}_"
        ) as tmp:
            tmp_path = Path(tmp.name)

        # parse_class_notes.py normally writes directly to KB, but we need a
        # temp staging file so merge_theory_ollama.py can receive it.
        # Strategy: parse to a dedicated staging path in KB, then merge.
        staging_path = KB_DIR / f"_staging_{topic_folder}.md"

        parse_ok = run(
            [
                sys.executable,
                str(PARSERS_DIR / "parse_class_notes.py"),
                str(note_path),
                "--topic", topic_num,
                "--name", topic_name,
            ],
            dry_run=dry_run,
        )

        if not parse_ok:
            errors += 1
            tmp_path.unlink(missing_ok=True)
            continue

        # parse_class_notes.py wrote to 03_knowledge_base/Topic_XX_Name.md (flat)
        # or to the per-folder Theory.md depending on which version is installed.
        # Check both locations for the freshly written content.
        flat_out = KB_DIR / f"Topic_{topic_num}_{topic_name}.md"
        theory_out = KB_DIR / topic_folder / "Theory.md"

        if flat_out.is_file() and flat_out.stat().st_size > 0:
            source_for_merge = flat_out
        elif theory_out.is_file() and theory_out.stat().st_size > 0:
            # Already in the right place; merge from a copy so the LLM sees
            # "new" vs "existing" correctly.  If Theory.md IS the target and
            # the parse wrote directly into it, skip the merge step.
            print(
                f"  INFO: parse_class_notes.py wrote directly to Theory.md — "
                "skipping merge_theory_ollama (content already integrated)."
            )
            mark_processed(state, state_key_hash, f"parse-only (direct write to {theory_out.relative_to(REPO_ROOT)})")
            save_state(state)
            processed += 1
            tmp_path.unlink(missing_ok=True)
            continue
        else:
            print(
                f"  FAIL: parse_class_notes.py succeeded but output not found at "
                f"{flat_out} or {theory_out}",
                file=sys.stderr,
            )
            errors += 1
            tmp_path.unlink(missing_ok=True)
            continue

        # Step 2: merge_theory_ollama.py
        merge_ok = run(
            [
                sys.executable,
                str(PARSERS_DIR / "merge_theory_ollama.py"),
                str(source_for_merge),
                topic_folder,
                "--model", model,
            ],
            dry_run=dry_run,
        )

        # Clean up flat staging file after merge (KB should now hold per-folder Theory.md)
        if source_for_merge == flat_out and not dry_run:
            flat_out.unlink(missing_ok=True)
        tmp_path.unlink(missing_ok=True)

        if not merge_ok:
            errors += 1
            continue

        mark_processed(state, state_key_hash, f"notes pipeline OK (topic {topic_folder})")
        save_state(state)
        processed += 1

    return processed, errors


# ---------------------------------------------------------------------------
# Past papers pipeline
# ---------------------------------------------------------------------------

def find_qp_ms_pairs() -> list[tuple[Path, Path, str]]:
    """
    Returns list of (qp_path, ms_path, paper_code) for unmatched QP/MS pairs
    found anywhere under 01_raw_sources/past_papers/.
    """
    papers_dir = RAW_SOURCES_DIR / "past_papers"
    if not papers_dir.is_dir():
        return []

    qp_map: dict[str, Path] = {}
    ms_map: dict[str, Path] = {}

    for f in sorted(papers_dir.rglob("*.pdf")):
        m_qp = QP_RE.match(f.name)
        m_ms = MS_RE.match(f.name)
        if m_qp:
            code = f"{m_qp.group(1)}__{m_qp.group(2)}"
            qp_map[code] = f
        elif m_ms:
            code = f"{m_ms.group(1)}__{m_ms.group(2)}"
            ms_map[code] = f

    pairs = []
    for code, qp_path in qp_map.items():
        if code in ms_map:
            # Reconstruct clean paper code from filename stem (e.g. 0478_s20_11)
            paper_code = re.sub(r"_qp_(\d+)$", r"_\1", qp_path.stem, flags=re.IGNORECASE)
            pairs.append((qp_path, ms_map[code], paper_code))
        else:
            print(
                f"  WARN: QP found with no matching MS — {qp_path.relative_to(RAW_SOURCES_DIR)}",
                file=sys.stderr,
            )
    return pairs


def process_past_papers(state: dict, model: str, dry_run: bool) -> tuple[int, int]:
    """Returns (processed, errors)."""
    pairs = find_qp_ms_pairs()
    if not pairs:
        print("  No QP/MS pairs found under 01_raw_sources/past_papers/")
        return 0, 0

    processed, errors = 0, 0
    for qp_path, ms_path, paper_code in pairs:
        h = hashlib.sha256()
        h.update(qp_path.read_bytes())
        h.update(ms_path.read_bytes())
        state_key = f"pastpaper::{paper_code}::{h.hexdigest()}"

        if state_key in state:
            print(f"  SKIP (already processed): {paper_code}")
            continue

        print(f"\n[Past paper] {paper_code}")

        # Step 1: parse_past_paper.py
        parse_ok = run(
            [
                sys.executable,
                str(PARSERS_DIR / "parse_past_paper.py"),
                str(qp_path),
                str(ms_path),
                "--code", paper_code,
            ],
            dry_run=dry_run,
        )
        if not parse_ok:
            errors += 1
            continue

        # Step 2: route_questions_ollama.py
        # parse_past_paper.py writes to 03_knowledge_base/PastPaper_<code>.md
        parsed_file = KB_DIR / f"PastPaper_{paper_code}.md"
        if not dry_run and not parsed_file.is_file():
            print(
                f"  FAIL: expected output {parsed_file.relative_to(REPO_ROOT)} not found.",
                file=sys.stderr,
            )
            errors += 1
            continue

        route_ok = run(
            [
                sys.executable,
                str(PARSERS_DIR / "route_questions_ollama.py"),
                str(parsed_file) if not dry_run else str(parsed_file),
                "--model", model,
            ],
            dry_run=dry_run,
        )
        if not route_ok:
            errors += 1
            continue

        mark_processed(state, state_key, f"past-paper pipeline OK ({paper_code})")
        save_state(state)
        processed += 1

    return processed, errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model for LLM steps (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be run without executing anything.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY-RUN MODE — no files will be written ===\n")

    state = load_state()

    print("--- Class notes pipeline ---")
    cn_processed, cn_errors = process_class_notes(state, args.model, args.dry_run)

    print("\n--- Past papers pipeline ---")
    pp_processed, pp_errors = process_past_papers(state, args.model, args.dry_run)

    total_processed = cn_processed + pp_processed
    total_errors = cn_errors + pp_errors

    print(f"\n{'='*60}")
    print(f"Done.  Processed: {total_processed}  |  Errors: {total_errors}")
    if total_errors:
        print("Re-run after fixing errors; processed files will be skipped.", file=sys.stderr)
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
