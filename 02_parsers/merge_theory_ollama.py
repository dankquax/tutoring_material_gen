#!/usr/bin/env python3
"""
merge_theory_ollama.py — Intelligently merges freshly parsed class notes into
an existing Theory.md using a local Ollama LLM.

Usage:
    python merge_theory_ollama.py <new_notes.md> <Topic_XX_Name> [--model llama3]

Reads:  <new_notes.md>  (freshly parsed Markdown from parse_class_notes.py)
        03_knowledge_base/<Topic_XX_Name>/Theory.md  (existing KB file, if any)
Writes: 03_knowledge_base/<Topic_XX_Name>/Theory.md  (consolidated output)

If Theory.md does not exist yet, the new notes are written as-is (no merge
needed). If it does exist, the LLM is asked to integrate the new content into
the correct sub-headings without duplicating concepts.
"""

import argparse
import sys
from pathlib import Path

import ollama

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = REPO_ROOT / "03_knowledge_base"

DEFAULT_MODEL = "llama3"

# Keep prompt + both documents under roughly 6 000 chars to stay comfortably
# within small-model context windows (~4 096 tokens).  Content beyond this
# limit is truncated — a warning is printed so the caller knows.
MAX_CONTENT_CHARS = 6_000

SYSTEM_PROMPT = """\
You are an expert educational content editor for IGCSE Computer Science (0478).

Your task is to merge two Markdown documents into one consolidated Theory.md file:
  1. EXISTING_THEORY — the current knowledge-base file for this topic.
  2. NEW_NOTES — freshly parsed class notes that may add or clarify content.

Rules you MUST follow:
- Preserve the Markdown heading hierarchy of EXISTING_THEORY exactly.
- Find the correct sub-heading(s) in EXISTING_THEORY where each piece of
  NEW_NOTES content belongs and insert it there.
- Do NOT duplicate any concept that is already present in EXISTING_THEORY.
- Do NOT invent, paraphrase, or summarise — copy text verbatim from the source
  documents only.
- If NEW_NOTES introduces a concept with no matching heading in EXISTING_THEORY,
  create a new sub-heading at the appropriate level.
- Output ONLY the final consolidated Markdown — no preamble, no commentary,
  no code fences wrapping the whole document.
"""


def merge_via_llm(existing_text: str, new_notes_text: str, model: str) -> str:
    existing_chars = len(existing_text)
    new_chars = len(new_notes_text)
    total = existing_chars + new_chars

    if total > MAX_CONTENT_CHARS:
        # Distribute the budget proportionally; always keep at least 500 chars of each.
        existing_budget = max(500, int(MAX_CONTENT_CHARS * existing_chars / total))
        new_budget = max(500, MAX_CONTENT_CHARS - existing_budget)
        if existing_chars > existing_budget or new_chars > new_budget:
            print(
                f"  WARN: combined document size ({total} chars) exceeds {MAX_CONTENT_CHARS}-char "
                f"limit — truncating (existing: {existing_budget}, new: {new_budget}). "
                "Consider upgrading to a larger model for full context.",
                file=sys.stderr,
            )
        existing_text = existing_text[:existing_budget]
        new_notes_text = new_notes_text[:new_budget]

    user_prompt = (
        "Merge the following two documents into one consolidated Theory.md.\n\n"
        "=== EXISTING_THEORY ===\n"
        f"{existing_text}\n\n"
        "=== NEW_NOTES ===\n"
        f"{new_notes_text}\n\n"
        "Return ONLY the merged Markdown content."
    )

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "new_notes",
        type=Path,
        help="Path to the freshly parsed Markdown file (e.g. a temp file from parse_class_notes.py)",
    )
    parser.add_argument(
        "topic_folder",
        help="Canonical topic folder name, e.g. Topic_01_Data_Representation",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model name (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    new_notes_path = args.new_notes.resolve()
    if not new_notes_path.is_file():
        print(f"FAIL: new_notes file not found: {new_notes_path}", file=sys.stderr)
        return 1

    topic_dir = KB_DIR / args.topic_folder
    theory_path = topic_dir / "Theory.md"

    new_notes_text = new_notes_path.read_text(encoding="utf-8").strip()
    if not new_notes_text:
        print(f"FAIL: new_notes file is empty: {new_notes_path}", file=sys.stderr)
        return 1

    # If no existing Theory.md, just write the new notes directly — no merge needed.
    if not theory_path.is_file():
        topic_dir.mkdir(parents=True, exist_ok=True)
        theory_path.write_text(new_notes_text + "\n", encoding="utf-8")
        print(f"PASS: created {theory_path.relative_to(REPO_ROOT)} ({len(new_notes_text)} chars, no prior content to merge)")
        return 0

    existing_text = theory_path.read_text(encoding="utf-8").strip()
    if not existing_text:
        # File exists but is empty — treat same as not existing.
        theory_path.write_text(new_notes_text + "\n", encoding="utf-8")
        print(f"PASS: wrote {theory_path.relative_to(REPO_ROOT)} (existing file was empty)")
        return 0

    print(f"Merging into {theory_path.relative_to(REPO_ROOT)} via {args.model} ...")
    try:
        merged = merge_via_llm(existing_text, new_notes_text, args.model)
    except Exception as exc:
        print(f"FAIL: Ollama error during merge — {exc}", file=sys.stderr)
        return 1

    if not merged:
        print("FAIL: LLM returned empty content — Theory.md NOT overwritten.", file=sys.stderr)
        return 1

    theory_path.write_text(merged + "\n", encoding="utf-8")
    print(f"PASS: merged {theory_path.relative_to(REPO_ROOT)} ({len(existing_text)} -> {len(merged)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
