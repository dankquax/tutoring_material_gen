#!/usr/bin/env python3
"""
route_questions_ollama.py — FEAT-005: Semantic routing of un-tagged past paper
questions into the correct per-topic Past_Papers.md using a local Ollama LLM.

Usage:
    python route_questions_ollama.py <path/to/PastPaper_CODE.md> [--model llama3]

Reads:  03_knowledge_base/PastPaper_*.md  (un-routed output of parse_past_paper.py)
        00_syllabus/Syllabus_Routing_Keywords.md
Writes: 03_knowledge_base/<Topic_XX_Name>/Past_Papers.md
"""

import argparse
import json
import re
import sys
from pathlib import Path

import ollama

REPO_ROOT = Path(__file__).resolve().parent.parent
SYLLABUS_FILE = REPO_ROOT / "00_syllabus" / "keyword_routing.md"
KB_DIR = REPO_ROOT / "03_knowledge_base"

DEFAULT_MODEL = "llama3"

# Canonical topic folder names — guardrail against LLM hallucinations.
# If the LLM returns a topic_folder not in this set, the question is SKIPPED.
VALID_TOPIC_FOLDERS = {
    "Topic_01_Data_Representation",
    "Topic_02_Data_Transmission",
    "Topic_03_Hardware",
    "Topic_04_Software",
    "Topic_05_The_Internet_and_Its_Uses",
    "Topic_06_Automated_and_Emerging_Technologies",
    "Topic_07_Algorithm_design_and_problem_solving",
    "Topic_08_Programming",
    "Topic_09_Databases",
    "Topic_10_Boolean_Logic",
}

QUESTION_BLOCK_RE = re.compile(r"^## Question (.+)$", re.MULTILINE)
MAIN_QNUM_RE = re.compile(r"^(\d+)")
# Strip markdown code fences that some models wrap JSON in despite instructions
CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

# Cap chunk text sent to the LLM to avoid overwhelming the context window.
# The syllabus reference already occupies ~1 500 tokens; 3 000 chars ≈ 750 tokens.
CHUNK_CHAR_LIMIT = 3_000


def load_syllabus_reference() -> str:
    if not SYLLABUS_FILE.is_file():
        raise FileNotFoundError(f"Syllabus routing reference not found: {SYLLABUS_FILE}")
    return SYLLABUS_FILE.read_text(encoding="utf-8")


def split_into_main_question_groups(md_text: str) -> list[dict]:
    """
    Groups all sub-parts (e.g. 3(a), 3(a)(i)) under their parent question
    number so that a single Ollama call classifies the entire scenario.

    Returns a list of dicts: {"main_q": "3", "text": "<combined markdown>"}
    """
    matches = list(QUESTION_BLOCK_RE.finditer(md_text))
    if not matches:
        return []

    raw_blocks: list[dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        label = m.group(1).strip()
        raw_blocks.append({"label": label, "text": md_text[start:end].rstrip()})

    groups: dict[str, list[str]] = {}
    order: list[str] = []
    for block in raw_blocks:
        main_match = MAIN_QNUM_RE.match(block["label"])
        main_q = main_match.group(1) if main_match else block["label"]
        if main_q not in groups:
            groups[main_q] = []
            order.append(main_q)
        groups[main_q].append(block["text"])

    return [
        {"main_q": q, "text": "\n\n".join(groups[q])}
        for q in order
    ]


def classify_chunk(chunk_text: str, syllabus_ref: str, model: str) -> dict:
    """
    Sends a Q+MS chunk to Ollama for topic classification.

    Expected JSON response keys:
        topic_folder  (str)   e.g. "Topic_03_Hardware"
        breadcrumbs   (str)   e.g. "3.2 Input and output devices"
        tags          (list)  3–5 keyword strings from the syllabus
        total_marks   (int)   sum of all marks in this question group
    """
    system_prompt = (
        "You are a Cambridge IGCSE Computer Science (0478) expert classifier. "
        "Given a past-paper question group and a syllabus keyword reference, "
        "identify the best-matching topic and sub-topic.\n\n"
        "Return ONLY a valid JSON object — no markdown, no prose — with exactly "
        "these four keys:\n"
        "  \"topic_folder\"  : string matching one of the Topic_XX_Name folders "
        "implied by the syllabus (e.g. \"Topic_03_Hardware\")\n"
        "  \"breadcrumbs\"   : string — the most specific sub-topic "
        "(e.g. \"3.2 Input and output devices\")\n"
        "  \"tags\"          : array of 3–5 keyword strings drawn verbatim from "
        "the syllabus reference below\n"
        "  \"total_marks\"   : integer — sum of all marks awarded in this group\n\n"
        "SYLLABUS REFERENCE:\n"
        f"{syllabus_ref}"
    )
    user_prompt = (
        "Classify the following past-paper question group and return JSON only:\n\n"
        f"{chunk_text[:CHUNK_CHAR_LIMIT]}"
    )

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response["message"]["content"].strip()
    raw = CODE_FENCE_RE.sub("", raw).strip()
    # raw_decode parses only the first JSON object and ignores trailing text/extra
    # objects — handles models that append explanation prose after the JSON.
    obj, _ = json.JSONDecoder().raw_decode(raw)
    return obj


def make_frontmatter(meta: dict, source_file: str) -> str:
    tags_yaml = json.dumps(meta.get("tags", []))
    return (
        "---\n"
        f"breadcrumbs: \"{meta.get('breadcrumbs', '')}\"\n"
        f"source_file: \"{source_file}\"\n"
        f"total_marks: {int(meta.get('total_marks', 0))}\n"
        f"tags: {tags_yaml}\n"
        "---"
    )


def append_to_topic(topic_folder: str, frontmatter: str, chunk_text: str) -> Path:
    topic_dir = KB_DIR / topic_folder
    topic_dir.mkdir(parents=True, exist_ok=True)
    out_file = topic_dir / "Past_Papers.md"

    separator = "\n\n" if out_file.is_file() and out_file.stat().st_size > 0 else ""
    with out_file.open("a", encoding="utf-8") as f:
        f.write(f"{separator}{frontmatter}\n\n{chunk_text}\n")

    return out_file


def route_file(input_file: Path, syllabus_ref: str, model: str) -> tuple[int, int]:
    """Routes one PastPaper_*.md file. Returns (routed, errors)."""
    md_text = input_file.read_text(encoding="utf-8")
    groups = split_into_main_question_groups(md_text)

    if not groups:
        print(f"  WARN: no '## Question' blocks in {input_file.name} — skipped.")
        return 0, 0

    print(f"\n[{input_file.name}] {len(groups)} question group(s) found.")
    routed, errors = 0, 0
    for group in groups:
        q_label = f"Q{group['main_q']}"
        try:
            meta = classify_chunk(group["text"], syllabus_ref, model)
        except json.JSONDecodeError as exc:
            print(f"  SKIP {q_label}: LLM returned invalid JSON — {exc}", file=sys.stderr)
            errors += 1
            continue
        except Exception as exc:
            print(f"  SKIP {q_label}: Ollama error — {exc}", file=sys.stderr)
            errors += 1
            continue

        topic_folder = meta.get("topic_folder", "").strip()
        if not topic_folder:
            print(f"  SKIP {q_label}: LLM returned empty topic_folder.", file=sys.stderr)
            errors += 1
            continue

        if topic_folder not in VALID_TOPIC_FOLDERS:
            # Case-insensitive fallback: accept the LLM's name if it matches a canonical
            # folder when lowercased (catches e.g. wrong-case "emerging_technologies").
            _lower = topic_folder.lower()
            _match = next((f for f in VALID_TOPIC_FOLDERS if f.lower() == _lower), None)
            if _match:
                topic_folder = _match
            else:
                print(f"  SKIP {q_label}: LLM returned unrecognised topic_folder '{topic_folder}'.", file=sys.stderr)
                errors += 1
                continue

        try:
            frontmatter = make_frontmatter(meta, input_file.name)
            out_path = append_to_topic(topic_folder, frontmatter, group["text"])
        except Exception as exc:
            print(f"  SKIP {q_label}: write error — {exc}", file=sys.stderr)
            errors += 1
            continue

        print(f"  OK  {q_label} -> {out_path.relative_to(REPO_ROOT)}")
        routed += 1

    return routed, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_files", nargs="*", type=Path,
        help="PastPaper_*.md file(s) to route. Omit to batch-process ALL "
             "PastPaper_*.md files found in 03_knowledge_base/."
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Ollama model name (default: {DEFAULT_MODEL})"
    )
    args = parser.parse_args()

    # Resolve target files: explicit list OR auto-glob from KB root
    if args.input_files:
        files: list[Path] = [f.resolve() for f in args.input_files]
        missing = [f for f in files if not f.is_file()]
        if missing:
            for f in missing:
                print(f"FAIL: {f} does not exist.", file=sys.stderr)
            return 1
    else:
        files = sorted(KB_DIR.glob("PastPaper_*.md"))
        if not files:
            print(f"FAIL: no PastPaper_*.md files found in {KB_DIR}.", file=sys.stderr)
            return 1
        print(f"Batch mode: found {len(files)} PastPaper_*.md file(s) in {KB_DIR.relative_to(REPO_ROOT)}")

    try:
        syllabus_ref = load_syllabus_reference()
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"Model: {args.model}\n")

    total_routed, total_errors = 0, 0
    for f in files:
        r, e = route_file(f, syllabus_ref, args.model)
        total_routed += r
        total_errors += e

    status = f"{total_errors} error(s)" if total_errors else "all OK"
    print(f"\n{'='*60}")
    print(f"Done. {total_routed} group(s) routed, {total_errors} skipped ({status}).")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
