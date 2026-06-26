#!/usr/bin/env python3
"""
split_syllabus.py — Deterministically localizes Syllabus_Routing_Keywords.md
into per-topic Syllabus.md stubs under 03_knowledge_base/<Topic_XX_Name>/.

Usage:
    python split_syllabus.py [path/to/Syllabus_Routing_Keywords.md]

Reads:  00_syllabus/Syllabus_Routing_Keywords.md  (or the path you supply)
Writes: 03_knowledge_base/<Topic_XX_Name>/Syllabus.md  (one file per topic)

No LLM is used — parsing is purely regex/string-based since the source
document follows a perfectly regular `### Topic N: Name` heading structure.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SYLLABUS = REPO_ROOT / "00_syllabus" / "Syllabus_Routing_Keywords.md"
KB_DIR = REPO_ROOT / "03_knowledge_base"

# Matches lines like:  ### Topic 1: Data representation
TOPIC_HEADER_RE = re.compile(r"^### Topic (\d+): (.+)$", re.MULTILINE)


def slugify_name(name: str) -> str:
    """'Data representation' → 'Data_Representation' (title-case, underscored)."""
    cleaned = re.sub(r"[^\w\s]", "", name)
    return "_".join(word.capitalize() for word in cleaned.split())


def extract_topics(text: str) -> list[dict]:
    """
    Returns a list of dicts: {"number": 1, "name": "Data_Representation", "text": "..."}
    The text chunk spans from the ### heading to just before the next ### heading.
    """
    matches = list(TOPIC_HEADER_RE.finditer(text))
    if not matches:
        return []

    topics = []
    for i, m in enumerate(matches):
        number = int(m.group(1))
        name = slugify_name(m.group(2).strip())
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        topics.append({"number": number, "name": name, "text": chunk})

    return topics


def find_existing_topic_dir(num: int) -> Path | None:
    """Returns any existing Topic_XX_* folder for this topic number, if one exists."""
    prefix = f"Topic_{num:02d}_"
    if KB_DIR.is_dir():
        for d in KB_DIR.iterdir():
            if d.is_dir() and d.name.startswith(prefix):
                return d
    return None


def main(source: Path = DEFAULT_SYLLABUS) -> int:
    if not source.is_file():
        print(f"FAIL: source file not found: {source}", file=sys.stderr)
        return 1

    text = source.read_text(encoding="utf-8")
    topics = extract_topics(text)

    if not topics:
        print(
            f"FAIL: no '### Topic N: Name' headers found in {source}\n"
            "Check that the source document uses exactly that heading format.",
            file=sys.stderr,
        )
        return 1

    written = 0
    for topic in topics:
        existing = find_existing_topic_dir(topic["number"])
        if existing:
            topic_dir = existing
        else:
            folder_name = f"Topic_{topic['number']:02d}_{topic['name']}"
            topic_dir = KB_DIR / folder_name
        topic_dir.mkdir(parents=True, exist_ok=True)

        out_file = topic_dir / "Syllabus.md"
        out_file.write_text(topic["text"], encoding="utf-8")
        print(f"  Written: {out_file.relative_to(REPO_ROOT)}")
        written += 1

    print(f"\nDone. {written} topic Syllabus.md file(s) created under {KB_DIR.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SYLLABUS
    raise SystemExit(main(source))
