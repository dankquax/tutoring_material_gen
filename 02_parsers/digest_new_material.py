#!/usr/bin/env python3
"""
digest_new_material.py — Master ingestion orchestrator.

Scans 01_raw_sources/ for unprocessed files and runs the correct pipeline:

  Class notes (PDF / DOCX)
    -> extract_docling.py  (extracts Markdown to _staging/)
    -> Theory.md           (staging file moved/appended into topic KB folder)

  Past papers (QP + MS PDF pairs)
    -> extract_docling.py  (extracts both PDFs to _staging/)
    -> link_qa.py          (regex state-machine links QP/MS chunks -> JSON)
    -> route_hybrid.py     (cosine routing + LLM YAML -> per-topic Past_Papers.md)
    -> staging cleanup     (removes intermediate files after successful route)

State is tracked in 01_raw_sources/.processed_files.json (SHA-256 keyed).
Files already in the state file are skipped.

Usage:
    python digest_new_material.py [--model llama3.2] [--embed-model nomic-embed-text] [--dry-run]

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
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_SOURCES_DIR = REPO_ROOT / "01_raw_sources"
KB_DIR          = REPO_ROOT / "03_knowledge_base"
STAGING_DIR     = KB_DIR / "_staging"
PARSERS_DIR     = REPO_ROOT / "02_parsers"
STATE_FILE      = RAW_SOURCES_DIR / ".processed_files.json"

TOPIC_FOLDER_RE = re.compile(r"^Topic_(\d{2})_(.+)$")
QP_RE = re.compile(r"^(.+)_qp_(\d+)\.pdf$", re.IGNORECASE)
MS_RE = re.compile(r"^(.+)_ms_(\d+)\.pdf$", re.IGNORECASE)

DEFAULT_MODEL       = "llama3.2"
DEFAULT_EMBED_MODEL = "nomic-embed-text"


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
    """Return (file_path, topic_num, topic_name) for all class-note PDFs/DOCXs."""
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


def process_class_notes(state: dict, dry_run: bool) -> tuple[int, int]:
    """Returns (processed, errors)."""
    files = find_class_notes()
    if not files:
        print("  No class notes found under 01_raw_sources/class_notes_docs/")
        return 0, 0

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    processed = errors = 0

    for note_path, topic_num, topic_name in files:
        state_key = f"notes::{note_path.relative_to(RAW_SOURCES_DIR)}::{file_hash(note_path)}"
        if state_key in state:
            print(f"  SKIP (already processed): {note_path.relative_to(RAW_SOURCES_DIR)}")
            continue

        print(f"\n[Class notes] {note_path.relative_to(RAW_SOURCES_DIR)}")
        topic_folder = f"Topic_{topic_num}_{topic_name}"
        staging_md   = STAGING_DIR / f"{note_path.stem}.md"
        theory_out   = KB_DIR / topic_folder / "Theory.md"

        # Step 1 — extract via Docling
        extract_ok = run(
            [sys.executable, str(PARSERS_DIR / "extract_docling.py"), "--file", str(note_path)],
            dry_run=dry_run,
        )
        if not extract_ok:
            errors += 1
            continue

        if not dry_run:
            if not staging_md.is_file():
                print(f"  FAIL: expected staging output {staging_md} not found.", file=sys.stderr)
                errors += 1
                continue

            # Step 2 — move/append into Theory.md
            theory_out.parent.mkdir(parents=True, exist_ok=True)
            extracted_content = staging_md.read_text(encoding="utf-8")
            if theory_out.is_file() and theory_out.stat().st_size > 0:
                with theory_out.open("a", encoding="utf-8") as fh:
                    fh.write(f"\n\n---\n\n{extracted_content}")
                print(f"  Appended to existing {theory_out.relative_to(REPO_ROOT)}")
            else:
                shutil.move(str(staging_md), str(theory_out))
                print(f"  Written to {theory_out.relative_to(REPO_ROOT)}")

            staging_md.unlink(missing_ok=True)
            mark_processed(state, state_key, f"notes pipeline OK (topic {topic_folder})")
            save_state(state)

        processed += 1

    return processed, errors


# ---------------------------------------------------------------------------
# Past papers pipeline
# ---------------------------------------------------------------------------

def find_qp_ms_pairs() -> list[tuple[Path, Path, str]]:
    """Return (qp_path, ms_path, paper_code) for all paired QP/MS PDFs."""
    papers_dir = RAW_SOURCES_DIR / "past_papers"
    if not papers_dir.is_dir():
        return []

    qp_map: dict[str, Path] = {}
    ms_map: dict[str, Path] = {}

    for f in sorted(papers_dir.rglob("*.pdf")):
        m_qp = QP_RE.match(f.name)
        m_ms = MS_RE.match(f.name)
        if m_qp:
            qp_map[f"{m_qp.group(1)}__{m_qp.group(2)}"] = f
        elif m_ms:
            ms_map[f"{m_ms.group(1)}__{m_ms.group(2)}"] = f

    pairs = []
    for code, qp_path in qp_map.items():
        if code in ms_map:
            paper_code = re.sub(r"_qp_(\d+)$", r"_\1", qp_path.stem, flags=re.IGNORECASE)
            pairs.append((qp_path, ms_map[code], paper_code))
        else:
            print(
                f"  WARN: QP found with no matching MS — {qp_path.relative_to(RAW_SOURCES_DIR)}",
                file=sys.stderr,
            )
    return pairs


def process_past_papers(state: dict, model: str, embed_model: str, dry_run: bool) -> tuple[int, int]:
    """Returns (processed, errors)."""
    pairs = find_qp_ms_pairs()
    if not pairs:
        print("  No QP/MS pairs found under 01_raw_sources/past_papers/")
        return 0, 0

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    processed = errors = 0

    for qp_path, ms_path, paper_code in pairs:
        h = hashlib.sha256()
        h.update(qp_path.read_bytes())
        h.update(ms_path.read_bytes())
        state_key = f"pastpaper::{paper_code}::{h.hexdigest()}"

        if state_key in state:
            print(f"  SKIP (already processed): {paper_code}")
            continue

        print(f"\n[Past paper] {paper_code}")

        qp_staging  = STAGING_DIR / f"{qp_path.stem}.md"
        ms_staging  = STAGING_DIR / f"{ms_path.stem}.md"
        linked_json = STAGING_DIR / f"{paper_code}_linked.json"

        # Step 1 — extract QP via Docling
        if not run(
            [sys.executable, str(PARSERS_DIR / "extract_docling.py"), "--file", str(qp_path)],
            dry_run=dry_run,
        ):
            errors += 1
            continue

        # Step 2 — extract MS via Docling
        if not run(
            [sys.executable, str(PARSERS_DIR / "extract_docling.py"), "--file", str(ms_path)],
            dry_run=dry_run,
        ):
            errors += 1
            continue

        # Step 3 — link QP + MS chunks -> JSON
        if not run(
            [
                sys.executable, str(PARSERS_DIR / "link_qa.py"),
                str(qp_staging), str(ms_staging),
                "--out", str(linked_json),
            ],
            dry_run=dry_run,
        ):
            errors += 1
            continue

        # Step 4 — hybrid route -> per-topic Past_Papers.md
        if not run(
            [
                sys.executable, str(PARSERS_DIR / "route_hybrid.py"),
                str(linked_json),
                "--model", model,
                "--embed-model", embed_model,
            ],
            dry_run=dry_run,
        ):
            errors += 1
            continue

        # Cleanup staging files for this pair
        if not dry_run:
            for staging_file in (qp_staging, ms_staging, linked_json):
                staging_file.unlink(missing_ok=True)
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
        help=f"Ollama LLM model for YAML metadata generation (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--embed-model",
        default=DEFAULT_EMBED_MODEL,
        help=f"Ollama embedding model for topic routing (default: {DEFAULT_EMBED_MODEL})",
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
    cn_processed, cn_errors = process_class_notes(state, args.dry_run)

    print("\n--- Past papers pipeline ---")
    pp_processed, pp_errors = process_past_papers(state, args.model, args.embed_model, args.dry_run)

    total_processed = cn_processed + pp_processed
    total_errors    = cn_errors    + pp_errors

    print(f"\n{'='*60}")
    print(f"Done.  Processed: {total_processed}  |  Errors: {total_errors}")
    if total_errors:
        print("Re-run after fixing errors; processed files will be skipped.", file=sys.stderr)
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
