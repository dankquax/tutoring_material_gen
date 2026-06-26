#!/usr/bin/env python3
"""
bootstrap_state.py — One-shot recovery tool.

Renames class_notes_docs subfolders to Topic_XX_Name format (required by
digest_new_material.py) and writes .processed_files.json to mark all
existing source files as already processed, preventing re-runs from
duplicating KB content after a lost state file.

Run once from repo root:
    py 02_parsers/bootstrap_state.py
"""

import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "01_raw_sources"
NOTES_DIR = RAW_DIR / "class_notes_docs"
PAPERS_DIR = RAW_DIR / "past_papers"
STATE_FILE = RAW_DIR / ".processed_files.json"

# old folder name -> Topic_XX_Name  (multiple sources can map to same target)
RENAMES = [
    ("1.Data Representation",       "Topic_01_Data_Representation"),
    ("2.Data Transmission",          "Topic_02_Data_Transmission"),
    ("3.Hardware 1",                 "Topic_03_Hardware"),
    ("4.Hardware 2",                 "Topic_03_Hardware"),
    ("5.Software",                   "Topic_04_Software"),
    ("6.The Internet and its Uses",  "Topic_05_The_Internet_and_Its_Uses"),
    ("7. Robotics and AI",           "Topic_06_Automated_and_Emerging_Technologies"),
]

QP_RE = re.compile(r"^(.+)_qp_(\d+)\.pdf$", re.IGNORECASE)
MS_RE = re.compile(r"^(.+)_ms_(\d+)\.pdf$", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    state: dict = {}

    # ------------------------------------------------------------------
    # 1. Rename / merge class note folders into Topic_XX_Name layout
    # ------------------------------------------------------------------
    print("=== Step 1: Rename class_notes_docs subfolders ===")
    for old_name, new_name in RENAMES:
        old_path = NOTES_DIR / old_name
        new_path = NOTES_DIR / new_name
        if not old_path.is_dir():
            print(f"  SKIP (not found): {old_name}")
            continue
        new_path.mkdir(exist_ok=True)
        for f in sorted(old_path.iterdir()):
            if not f.is_file():
                continue
            dest = new_path / f.name
            if dest.exists():
                # Avoid collision when merging two source folders into one target
                stem = old_name.replace(".", "").replace(" ", "_")
                dest = new_path / f"{f.stem}_{stem}{f.suffix}"
            f.rename(dest)
            print(f"    moved: {f.name} -> {dest.name}")
        try:
            old_path.rmdir()
            print(f"  OK: {old_name!r} -> {new_name!r}")
        except OSError:
            print(f"  WARN: could not remove {old_path} (not empty?)")

    # ------------------------------------------------------------------
    # 2. Mark all class notes as processed (using post-rename paths)
    # ------------------------------------------------------------------
    print("\n=== Step 2: Register class notes in state file ===")
    for f in sorted(NOTES_DIR.rglob("*")):
        if f.suffix.lower() not in (".pdf", ".docx"):
            continue
        rel = f.relative_to(RAW_DIR)
        h = sha256_file(f)
        key = f"notes::{rel}::{h}"
        state[key] = {"status": "processed", "note": "bootstrapped — pre-existing content in KB"}
        print(f"  NOTED: {rel}")

    # ------------------------------------------------------------------
    # 3. Mark all QP/MS pairs as processed
    # ------------------------------------------------------------------
    print("\n=== Step 3: Register past paper pairs in state file ===")
    qp_map: dict[str, Path] = {}
    ms_map: dict[str, Path] = {}
    for f in sorted(PAPERS_DIR.rglob("*.pdf")):
        m = QP_RE.match(f.name)
        if m:
            qp_map[f"{m.group(1)}__{m.group(2)}"] = f
            continue
        m = MS_RE.match(f.name)
        if m:
            ms_map[f"{m.group(1)}__{m.group(2)}"] = f

    for code, qp in sorted(qp_map.items()):
        if code not in ms_map:
            print(f"  WARN: no MS found for {qp.name}")
            continue
        ms = ms_map[code]
        h = hashlib.sha256()
        h.update(qp.read_bytes())
        h.update(ms.read_bytes())
        paper_code = re.sub(r"_qp_(\d+)$", r"_\1", qp.stem, flags=re.IGNORECASE)
        key = f"pastpaper::{paper_code}::{h.hexdigest()}"
        state[key] = {"status": "processed", "note": "bootstrapped — pre-existing content in KB"}
        print(f"  NOTED: {paper_code}")

    # ------------------------------------------------------------------
    # 4. Write state file
    # ------------------------------------------------------------------
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"\n=== Done: wrote {len(state)} entries to {STATE_FILE} ===")


if __name__ == "__main__":
    main()
