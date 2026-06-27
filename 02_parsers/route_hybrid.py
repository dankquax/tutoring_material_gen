#!/usr/bin/env python3
"""
route_hybrid.py — FEAT-008: Hybrid Topic Router (Embeddings + LLM Metadata).

For each Q&A pair in a _staging/*_linked.json file:
  1. Embed the chunk text via Ollama (nomic-embed-text).
  2. Compute cosine similarity against 10 hardcoded syllabus anchors (numpy).
  3. Route to the highest-scoring Topic_XX_Name folder (math decision, no LLM).
  4. Call llama3.2 ONLY to extract the YAML frontmatter (breadcrumbs + tags).
  5. Append the chunk with RULE 10 YAML metadata to the topic's Past_Papers.md.

Usage:
    python route_hybrid.py <linked_json>
    python route_hybrid.py --batch   (process all *_linked.json in _staging/)
"""

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import ollama

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = REPO_ROOT / "03_knowledge_base"
STAGING_DIR = KB_DIR / "_staging"

DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_LLM_MODEL   = "llama3.2"

# ---------------------------------------------------------------------------
# Syllabus anchor texts (one per Cambridge 0478 topic)
# ---------------------------------------------------------------------------
TOPIC_ANCHORS: dict[str, str] = {
    "Topic_01_Data_Representation": (
        "Number systems: binary, denary, hexadecimal conversion. Binary arithmetic: addition, "
        "overflow, two's complement, sign-and-magnitude. A register in this context stores a "
        "binary numeric value for arithmetic — NOT part of CPU architecture. Text encoding: "
        "ASCII, Unicode. Sound: sampling, sample rate, bit depth. Images: pixels, colour depth, "
        "resolution. Compression: lossy, lossless, run-length encoding."
    ),
    "Topic_02_Data_Transmission": (
        "Data transmission modes: serial vs parallel, simplex, half-duplex, full-duplex. "
        "Physical connectors: USB, Bluetooth. Error detection and correction: parity bits, "
        "checksums, check digits, automatic repeat request (ARQ). Packet switching: packets, "
        "headers, trailers, router paths, IP addresses for routing. Encryption and decryption: "
        "Caesar cipher, Vernam cipher, symmetric key, public/private key."
    ),
    "Topic_03_Hardware": (
        "CPU hardware internals: Von Neumann architecture, fetch-decode-execute (FDE) cycle, "
        "arithmetic/logic unit (ALU), control unit, registers as CPU components (MAR, MDR, PC, "
        "accumulator, CIR). System buses: address bus, data bus, control bus. Primary memory: "
        "RAM, ROM, cache. Secondary storage devices: magnetic (hard disk), optical (CD, DVD, "
        "Blu-ray), solid-state (SSD, flash). Input devices: keyboard, mouse, microphone, "
        "scanner, camera. Output devices: monitor, printer, speaker, actuator. "
        "Does NOT include binary number conversion or binary arithmetic questions."
    ),
    "Topic_04_Software": (
        "System software vs application software. Operating system functions: memory management, "
        "multitasking, scheduling, interrupt handling, device driver management, user interface "
        "(GUI/CLI). High-level vs low-level languages: machine code, assembly language. "
        "Translators: compiler (whole-program, produces executable), interpreter (line-by-line, "
        "stops on error), assembler. Software utilities, open-source vs proprietary licensing."
    ),
    "Topic_05_The_Internet_and_Its_Uses": (
        "Internet and World Wide Web: URLs, HTTP, HTTPS, HTML, DNS resolution, IP addresses, "
        "MAC addresses, web hosting, cookies, e-commerce. Cybersecurity threats: phishing, "
        "pharming, malware (virus, worm, trojan horse, spyware, ransomware), brute-force attack, "
        "SQL injection, DDoS. Countermeasures: firewall, proxy server, antivirus software, "
        "two-factor authentication, biometrics, SSL/TLS encryption. Digital currency, "
        "online banking security, data privacy legislation."
    ),
    "Topic_06_Automated_and_Emerging_Technologies": (
        "Automated systems: sensors, microprocessors, actuators, real-time feedback control loops. "
        "Robotics: industrial robots, autonomous vehicles, advantages and limitations. Artificial "
        "Intelligence: machine learning, neural networks, expert systems, natural language "
        "processing. Emerging technology: quantum computing, biometrics, augmented/virtual reality. "
        "Does NOT cover networking protocols, databases, or programming code syntax."
    ),
    "Topic_07_Algorithm_design_and_problem_solving": (
        "Algorithm design: program development life cycle (PDLC) stages — analysis, design, "
        "coding, testing, evaluation. Flowchart symbols: start/end (oval), process (rectangle), "
        "decision (diamond), input/output (parallelogram). Pseudocode: IF/ELSE/THEN/ENDIF, "
        "WHILE/ENDWHILE, FOR/NEXT, arrays. Standard algorithms: linear search, binary search, "
        "bubble sort, merge sort. Trace tables are used HERE to dry-run and trace pseudocode or "
        "algorithm execution step-by-step — a trace table is an algorithm testing tool, NOT a "
        "database construct. Test data: normal, boundary, erroneous. Validation vs verification."
    ),
    "Topic_08_Programming": (
        "Programming code syntax and constructs: variables, constants, assignment operator. "
        "Data types: integer, real/float, boolean, character, string. Arrays (1D and 2D). "
        "Control flow: IF/ELSE, CASE/OTHERWISE, FOR loops, WHILE loops, REPEAT-UNTIL. "
        "String operations: concatenation, substring, string length, upper/lower case. "
        "Subroutines: procedures, functions, parameters, return values, local vs global scope. "
        "File handling: OPEN, READ, WRITE, CLOSE, EOF. Recursion."
    ),
    "Topic_09_Databases": (
        "Relational databases: tables of records, fields (columns), records (rows), primary key, "
        "foreign key, data types, relationships between tables. SQL queries: SELECT, FROM, WHERE, "
        "AND/OR, ORDER BY, GROUP BY, COUNT, SUM, INNER JOIN, linking tables by key fields. "
        "Database design: entity-relationship diagrams, normalisation. "
        "A database TABLE is a persistent store of records — NOT an algorithm trace table "
        "or a pseudocode array. Does NOT include Boolean logic or truth tables for gates."
    ),
    "Topic_10_Boolean_Logic": (
        "Boolean logic gates and their truth tables: AND gate, OR gate, NOT gate (inverter), "
        "NAND gate, NOR gate, XOR gate. A truth table here lists all input combinations (0/1) "
        "and gate output — this is a LOGIC CIRCUIT tool, NOT a database table or SQL result set. "
        "Boolean expressions, De Morgan's laws, simplification. Logic circuit diagrams combining "
        "multiple gates. Half adder, full adder circuits."
    ),
}

VALID_TOPICS: frozenset[str] = frozenset(TOPIC_ANCHORS.keys())

# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _embed(text: str, model: str) -> np.ndarray:
    """Return a float32 vector for text using Ollama."""
    try:
        # ollama >= 0.3 API
        resp = ollama.embed(model=model, input=text)
        vec = resp.embeddings[0]
    except AttributeError:
        # fallback for older ollama library
        resp = ollama.embeddings(model=model, prompt=text)
        vec = resp["embedding"]
    return np.array(vec, dtype=np.float32)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def build_anchor_embeddings(embed_model: str) -> dict[str, np.ndarray]:
    """Pre-compute embeddings for all 10 topic anchors (once per run)."""
    print(f"Building anchor embeddings with '{embed_model}' (once per run)...")
    result = {}
    for topic, anchor_text in TOPIC_ANCHORS.items():
        result[topic] = _embed(anchor_text, embed_model)
        print(f"  embedded: {topic}")
    return result


def route_topic(chunk_text: str, anchor_embeddings: dict[str, np.ndarray], embed_model: str) -> str:
    """Return the topic folder name with the highest cosine similarity to the chunk."""
    chunk_vec = _embed(chunk_text, embed_model)
    return max(anchor_embeddings, key=lambda t: _cosine(chunk_vec, anchor_embeddings[t]))


# ---------------------------------------------------------------------------
# LLM metadata extraction
# ---------------------------------------------------------------------------

_YAML_SYSTEM = """\
You are a metadata extractor for IGCSE Computer Science (0478) past paper questions.
Given a Q&A chunk, output ONLY a YAML block with these exact four fields and nothing else:

breadcrumbs: "<most specific Cambridge 0478 sub-topic, e.g. '3.2 Input and output devices'>"
source_file: "<paper code passed in the user message>"
total_marks: <integer — sum of all marks from [N] or [N marks] markers in the chunk>
tags:
  - "<keyword 1 from Cambridge 0478 vocabulary>"
  - "<keyword 2>"
  - "<keyword 3>"

Rules:
- breadcrumbs must be the exact Cambridge 0478 sub-topic string (e.g. "1.3 Two's complement").
- total_marks: parse all [N] or [N marks] tokens; sum them to an integer.
- tags: 3–5 keyword strings drawn strictly from the syllabus vocabulary.
- Output ONLY the YAML block. No preamble, no explanation, no code fences.
"""


def extract_yaml_metadata(chunk_text: str, source_file: str, llm_model: str) -> str:
    """Call local LLM to extract YAML frontmatter. Returns a raw YAML string."""
    prompt = f"source_file: {source_file}\n\n{chunk_text}"
    try:
        resp = ollama.chat(
            model=llm_model,
            messages=[
                {"role": "system", "content": _YAML_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
        )
        raw = resp["message"]["content"].strip()
        # Strip any accidental fenced code block wrappers (yaml, yml, or bare ```)
        raw = re.sub(r"^```(?:ya?ml)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "",             raw, flags=re.IGNORECASE)
        # Strip stray language-tag lines left when LLM uses ```yml fences
        raw = re.sub(r"(?m)^ya?ml\s*\n?", "", raw)
        raw = raw.strip()
        # RULE 10: guarantee source_file is always present
        if "source_file:" not in raw:
            # Insert after breadcrumbs line (first line) if present, else prepend
            lines = raw.splitlines()
            if lines:
                raw = lines[0] + f'\nsource_file: "{source_file}"\n' + "\n".join(lines[1:])
            else:
                raw = f'source_file: "{source_file}"'
        return raw
    except Exception as exc:
        print(f"  WARN: LLM metadata call failed ({exc}); using stub.", file=sys.stderr)
        return (
            f'breadcrumbs: "Unknown"\n'
            f'source_file: "{source_file}"\n'
            f"total_marks: 0\n"
            f"tags:\n"
            f'  - "{source_file}"'
        )


# ---------------------------------------------------------------------------
# Knowledge-base writer
# ---------------------------------------------------------------------------

def append_to_past_papers(topic_folder: str, yaml_meta: str, pair: dict) -> None:
    """Append one Q&A block with RULE 10 frontmatter to the topic's Past_Papers.md."""
    topic_dir = KB_DIR / topic_folder
    topic_dir.mkdir(parents=True, exist_ok=True)
    out_path = topic_dir / "Past_Papers.md"

    label       = pair["label"]
    question    = pair["question"].strip()
    mark_scheme = pair["mark_scheme"].strip()

    block = (
        f"\n---\n"
        f"{yaml_meta}\n"
        f"---\n\n"
        f"**Question {label}**\n\n"
        f"{question}\n\n"
        f"**Mark Scheme**\n\n"
        f"{mark_scheme}\n"
    )

    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(block)


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

# Minimum question length below which we prepend parent context for embedding
_PREAMBLE_SHORT_THRESHOLD = 60


def _parent_label(label: str) -> str | None:
    """Return the immediate parent label, or None if already at the root level."""
    if "(" not in label:
        return None
    return label[: label.rfind("(")]


def _build_embed_text(
    label: str,
    question: str,
    mark_scheme: str,
    question_map: dict[str, str],
) -> str:
    """
    Build the text string to embed for routing.

    If the question text is very short (e.g. just a number like "11"), its
    embedding vector will be dominated by noise.  In that case we walk up the
    label hierarchy to find the nearest ancestor whose question text is long
    enough to provide meaningful topic context, then prepend it.

    The prepended context is ONLY used for the cosine-similarity calculation —
    it is never written to the knowledge base.
    """
    base = f"Question {label}:\n{question}\n\nMark Scheme:\n{mark_scheme}"

    if len(question) >= _PREAMBLE_SHORT_THRESHOLD:
        return base

    # Walk up: 1(a)(i) -> 1(a) -> 1
    parent = _parent_label(label)
    while parent is not None:
        parent_q = question_map.get(parent, "").strip()
        if len(parent_q) >= _PREAMBLE_SHORT_THRESHOLD:
            return f"Context: {parent_q}\n\n{base}"
        parent = _parent_label(parent)

    return base  # no useful ancestor found; embed as-is


def process_linked_json(
    json_path: Path,
    anchor_embeddings: dict[str, np.ndarray],
    embed_model: str,
    llm_model: str,
) -> tuple[int, int]:
    """Route all Q&A pairs in one linked JSON. Returns (routed, skipped)."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    source_file = data.get("source", json_path.stem)
    pairs = data.get("pairs", [])

    # Build label → question text map for preamble context injection (Phase 3).
    # Includes preamble-only rows (empty mark_scheme) because their text is
    # the scenario context we need — they are NOT written to the KB.
    question_map: dict[str, str] = {
        p.get("label", ""): p.get("question", "").strip()
        for p in pairs
        if p.get("question", "").strip()
    }

    routed = skipped = 0
    for pair in pairs:
        label       = pair.get("label", "?")
        question    = pair.get("question", "").strip()
        mark_scheme = pair.get("mark_scheme", "").strip()

        if not mark_scheme.strip() or not question.strip():
            # Preamble/context row (no answer) or artifact (no question) — skip
            skipped += 1
            continue

        # Build embedding text: injects parent context for short sub-questions.
        # This enriched string is used ONLY for cosine routing — not stored.
        embed_text = _build_embed_text(label, question, mark_scheme, question_map)

        # The canonical chunk text (written to KB) contains only the pair itself.
        chunk_text = f"Question {label}:\n{question}\n\nMark Scheme:\n{mark_scheme}"

        # Step 1 — embed + route (math, deterministic)
        topic_folder = route_topic(embed_text, anchor_embeddings, embed_model)
        print(f"  {label} -> {topic_folder}")

        # Step 2 — LLM metadata only (uses canonical chunk_text, not enriched)
        yaml_meta = extract_yaml_metadata(chunk_text, source_file, llm_model)

        # Step 3 — append to KB
        append_to_past_papers(topic_folder, yaml_meta, pair)
        routed += 1

    return routed, skipped


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("linked_json", nargs="?", help="Path to a *_linked.json file")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all *_linked.json files in _staging/ in one pass.",
    )
    parser.add_argument(
        "--embed-model",
        default=DEFAULT_EMBED_MODEL,
        help=f"Ollama embedding model (default: {DEFAULT_EMBED_MODEL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_LLM_MODEL,
        help=f"Ollama LLM model for YAML metadata (default: {DEFAULT_LLM_MODEL})",
    )
    args = parser.parse_args()

    anchor_embeddings = build_anchor_embeddings(args.embed_model)

    if args.batch:
        json_files = sorted(STAGING_DIR.glob("*_linked.json"))
        if not json_files:
            print("No *_linked.json files found in _staging/")
            return 0
        total_routed = total_skipped = 0
        for jf in json_files:
            print(f"\nProcessing: {jf.name}")
            r, s = process_linked_json(jf, anchor_embeddings, args.embed_model, args.model)
            total_routed  += r
            total_skipped += s
        print(f"\nDone.  Routed: {total_routed}  |  Skipped: {total_skipped}")
        return 0

    if not args.linked_json:
        parser.print_help()
        return 1

    json_path = Path(args.linked_json)
    if not json_path.is_file():
        print(f"ERROR: File not found: {json_path}", file=sys.stderr)
        return 1

    routed, skipped = process_linked_json(
        json_path, anchor_embeddings, args.embed_model, args.model
    )
    print(f"\nDone.  Routed: {routed}  |  Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
