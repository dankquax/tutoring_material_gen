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

DEFAULT_MODEL = "llama3.2:latest"

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
        "You are a highly precise Expert Syllabus Routing Agent for IGCSE Computer "
        "Science (0478). Your sole task is to analyse a past-paper Exam Question + "
        "Mark Scheme chunk and classify it into its exact topic folder based on the "
        "primary curriculum intent.\n\n"
        "### COMPLETE TOPIC ROUTING MAP\n"
        "Classify the question based on the core concept it tests. "
        "Follow these rules and absolute constraints:\n\n"
        "- Topic 01 (Data_Representation): Binary, denary, hexadecimal, overflow, "
        "two's complement. Text/sound/image representation (ASCII, Unicode, pixels, "
        "sample rate). Storage units (bits to exbibytes). Compression (lossy, "
        "lossless, RLE).\n"
        "- Topic 02 (Data_Transmission): Packets, packet switching, serial/parallel, "
        "simplex/duplex, USB. Error detection (parity, checksum, echo, check digit, "
        "ARQ). Encryption (symmetric, asymmetric). "
        "*CONSTRAINT: Never route to Topic 03 just because it mentions hardware "
        "like a router or cable.*\n"
        "- Topic 03 (Hardware): CPU architecture, Von Neumann, Fetch-Decode-Execute, "
        "registers, buses, cache, cores. Standard Input/Output devices (keyboards, "
        "screens, printers, basic scanners). Storage mediums (HDD, SSD, optical). "
        "MAC/IP addresses. "
        "*CONSTRAINT: Do not route sensors, actuators, or automated systems here.*\n"
        "- Topic 04 (Software): System vs. Application software, Operating Systems, "
        "interrupts. High/low-level languages, assembly, compilers, interpreters, IDEs.\n"
        "- Topic 05 (The_Internet_and_Its_Uses): WWW, URLs, HTTP/HTTPS, DNS, web "
        "browsers, cookies. Digital currency/blockchain. Cybersecurity (malware, "
        "phishing, hacking, firewalls, SSL).\n"
        "- Topic 06 (Automated_and_Emerging_Technologies): Sensors (light, acoustic, "
        "etc.), actuators, automated loops. Robotics. Artificial Intelligence "
        "(expert systems, machine learning). "
        "*CONSTRAINT: Must go here, NEVER Topic 03.*\n"
        "- Topic 07 (Algorithm_design_and_problem_solving): Program development life "
        "cycle, flowcharts, pseudocode logic. Linear search, bubble sort. "
        "Validation/verification checks, test data types, trace tables.\n"
        "- Topic 08 (Programming): Coding syntax/constructs: variables, constants, "
        "arrays (1D/2D), loops (FOR, WHILE, REPEAT), IF/CASE statements. "
        "String handling, functions, procedures. File handling (read/write lines).\n"
        "- Topic 09 (Databases): Single-table databases, fields, records, primary "
        "keys. SQL scripting (SELECT, FROM, WHERE, ORDER BY, SUM, COUNT).\n"
        "- Topic 10 (Boolean_Logic): Logic gates (AND, OR, NOT, NAND, NOR, XOR), "
        "truth tables, logic circuits, logic expressions.\n\n"
        "### OUTPUT FORMAT\n"
        "You must respond ONLY with a valid JSON object. "
        "Do not include any conversational text or markdown fences.\n"
        "{\n"
        "  \"topic_folder\": \"<exact folder name from the list below>\",\n"
        "  \"breadcrumbs\": \"X.X Sub-topic Name\",\n"
        "  \"total_marks\": 0,\n"
        "  \"tags\": [\"tag1\", \"tag2\", \"tag3\"]\n"
        "}\n\n"
        "EXACT VALID topic_folder VALUES (copy exactly, case-sensitive):\n"
        "Topic_01_Data_Representation, Topic_02_Data_Transmission, Topic_03_Hardware, "
        "Topic_04_Software, Topic_05_The_Internet_and_Its_Uses, "
        "Topic_06_Automated_and_Emerging_Technologies, "
        "Topic_07_Algorithm_design_and_problem_solving, Topic_08_Programming, "
        "Topic_09_Databases, Topic_10_Boolean_Logic"
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
    try:
        # Fast path: response starts with valid JSON
        obj, _ = json.JSONDecoder().raw_decode(raw)
        return obj
    except json.JSONDecodeError:
        pass

    # Fallback A: model wrapped JSON in prose — locate any {...} block
    json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if json_match:
        candidate = json_match.group()
        # Fallback B: small models emit unquoted string values like
        #   "topic_folder": Topic_03_Hardware  →  quote them
        candidate = re.sub(
            r'("(?:topic_folder|breadcrumbs)"\s*:\s*)([A-Za-z][^,\n\]}"]*)',
            lambda m: m.group(1) + '"' + m.group(2).rstrip() + '"',
            candidate,
        )
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Fallback C: regex-extract individual fields from whatever the model wrote
    topic_m = re.search(r'"?topic_folder"?\s*:\s*"?([A-Za-z0-9_]+)"?', raw)
    bc_m = re.search(r'"?breadcrumbs"?\s*:\s*"([^"]*)"', raw)
    marks_m = re.search(r'"?total_marks"?\s*:\s*(\d+)', raw)
    tags_m = re.search(r'"?tags"?\s*:\s*\[([^\]]*)\]', raw, re.DOTALL)
    if topic_m:
        return {
            "topic_folder": topic_m.group(1).strip(),
            "breadcrumbs": bc_m.group(1) if bc_m else "",
            "total_marks": int(marks_m.group(1)) if marks_m else 0,
            "tags": re.findall(r'"([^"]+)"', tags_m.group(1)) if tags_m else [],
        }

    raise json.JSONDecodeError("LLM response contained no parseable JSON", raw, 0)


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
