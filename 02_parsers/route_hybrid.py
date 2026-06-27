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
        "Does NOT include binary number conversion or binary arithmetic questions. "
        "Does NOT include data transmission modes (serial, parallel, simplex, half-duplex, "
        "full-duplex) — those are Topic 02."
    ),
    "Topic_04_Software": (
        "System software vs application software. Operating system functions: memory management, "
        "multitasking, scheduling, interrupt handling, device driver management, user interface "
        "(GUI/CLI). High-level vs low-level languages: machine code, assembly language. "
        "Translators: compiler (whole-program, produces executable), interpreter (line-by-line, "
        "stops on error), assembler. Software utilities, open-source vs proprietary licensing."
    ),
    "Topic_05_The_Internet_and_Its_Uses": (
        "Internet and World Wide Web: URL, web address, website parts (domain, path, protocol), "
        "HTTP, HTTPS, HTML, DNS resolution, IP addresses, MAC addresses, web hosting, cookies, "
        "e-commerce. Cybersecurity threats: phishing, pharming, malware (virus, worm, trojan horse, "
        "spyware, ransomware), brute-force attack, SQL injection, DDoS. Countermeasures: firewall, "
        "proxy server, antivirus software, two-factor authentication, biometrics, SSL/TLS encryption. "
        "Digital currency, online banking security, data privacy legislation."
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
        "or a pseudocode array. Does NOT include Boolean logic or truth tables for gates. "
        "Does NOT include URLs, web addresses, or website structure — those are Topic 05."
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
# Python-driven YAML construction (Phase 3 hardening)
# ---------------------------------------------------------------------------

# Hardcoded breadcrumbs per topic — Python dictates, LLM never touches these.
TOPIC_BREADCRUMBS: dict[str, str] = {
    "Topic_01_Data_Representation":              "Topic 01: Data Representation",
    "Topic_02_Data_Transmission":                "Topic 02: Data Transmission",
    "Topic_03_Hardware":                         "Topic 03: Hardware",
    "Topic_04_Software":                         "Topic 04: Software",
    "Topic_05_The_Internet_and_Its_Uses":        "Topic 05: The Internet and Its Uses",
    "Topic_06_Automated_and_Emerging_Technologies": "Topic 06: Automated and Emerging Technologies",
    "Topic_07_Algorithm_design_and_problem_solving": "Topic 07: Algorithm Design and Problem Solving",
    "Topic_08_Programming":                      "Topic 08: Programming",
    "Topic_09_Databases":                        "Topic 09: Databases",
    "Topic_10_Boolean_Logic":                    "Topic 10: Boolean Logic",
}

# Regex to extract mark values from [N] or [N marks] / [N mark] tokens.
_MARKS_RE = re.compile(r'\[(\d+)\s*(?:marks?)?\]', re.IGNORECASE)


def extract_total_marks(text: str) -> int:
    """Sum all [N] / [N marks] markers in the Q&A text. Pure Python, no LLM."""
    return sum(int(m) for m in _MARKS_RE.findall(text))


def extract_tags_from_llm(chunk_text: str, llm_model: str) -> list[str]:
    """Ask the LLM for 3–5 comma-separated keywords only. Returns a clean list."""
    prompt = (
        "Read this computer science question. "
        "Output ONLY a single comma-separated list of 3 to 5 keywords. "
        "Do not use markdown. Do not write sentences."
    )
    try:
        resp = ollama.chat(
            model=llm_model,
            messages=[{"role": "user", "content": f"{prompt}\n\n{chunk_text}"}],
        )
        raw = resp["message"]["content"].strip()
        tags = [t.strip().strip("\"'") for t in raw.split(",") if t.strip()]
        tags = [t for t in tags if t][:5]   # cap at 5
        if len(tags) < 3:
            tags += ["computer science"] * (3 - len(tags))
        return tags
    except Exception as exc:
        print(f"  WARN: LLM tags call failed ({exc}); using stub.", file=sys.stderr)
        return ["computer science", "IGCSE", "0478"]


def build_yaml_metadata(
    topic_folder: str,
    source_file: str,
    total_marks: int,
    tags: list[str],
) -> str:
    """Construct RULE 10-compliant YAML using an f-string. No LLM involved."""
    breadcrumbs = TOPIC_BREADCRUMBS.get(topic_folder, topic_folder)
    tags_yaml = "\n".join(f'  - "{t}"' for t in tags)
    return (
        f'breadcrumbs: "{breadcrumbs}"\n'
        f'source_file: "{source_file}"\n'
        f'total_marks: {total_marks}\n'
        f'tags:\n'
        f'{tags_yaml}'
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

        # Step 2 — Python extracts marks + breadcrumbs; LLM supplies keywords only.
        total_marks = extract_total_marks(chunk_text)
        tags        = extract_tags_from_llm(chunk_text, llm_model)
        yaml_meta   = build_yaml_metadata(topic_folder, source_file, total_marks, tags)

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
