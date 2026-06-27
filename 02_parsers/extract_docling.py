#!/usr/bin/env python3
"""
extract_docling.py — FEAT-006: Docling Universal Extraction Engine.

Scans 01_raw_sources/ for PDF/DOCX documents, extracts layout and tables
natively via Docling's DocumentConverter, and saves clean Markdown files
to 03_knowledge_base/_staging/ ready for link_qa.py.

Usage:
    python extract_docling.py                        # scan all of 01_raw_sources/
    python extract_docling.py --file <path>          # single file
    python extract_docling.py --source-dir <path>    # alternate source root
    python extract_docling.py --staging-dir <path>   # alternate staging output
"""

import argparse
import sys
from pathlib import Path

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_SOURCES_DIR = REPO_ROOT / "01_raw_sources"
STAGING_DIR = REPO_ROOT / "03_knowledge_base" / "_staging"

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def extract_file(converter: DocumentConverter, source_path: Path, output_dir: Path) -> bool:
    """Convert a single file to Markdown in output_dir. Returns True on success."""
    out_path = output_dir / f"{source_path.stem}.md"
    print(f"  Extracting: {source_path.name} -> {out_path.relative_to(REPO_ROOT)}")
    try:
        result = converter.convert(str(source_path))
        md_content = result.document.export_to_markdown()
        out_path.write_text(md_content, encoding="utf-8")
        print(f"  OK: {len(md_content):,} chars written")
        return True
    except Exception as exc:
        print(f"  FAIL: {exc}", file=sys.stderr)
        return False


def scan_source_dir(source_dir: Path) -> list[Path]:
    return [
        f for f in sorted(source_dir.rglob("*"))
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        help="Convert a single file instead of scanning the source directory.",
    )
    parser.add_argument(
        "--source-dir",
        default=str(RAW_SOURCES_DIR),
        help="Root directory to scan (default: 01_raw_sources/).",
    )
    parser.add_argument(
        "--staging-dir",
        default=str(STAGING_DIR),
        help="Output directory for staged Markdown (default: 03_knowledge_base/_staging/).",
    )
    args = parser.parse_args()

    staging_dir = Path(args.staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Configure PDF Pipeline Options to drop OCR for native digital files
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False  # Bypasses RapidOCR crash, runs significantly faster

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    if args.file:
        file_path = Path(args.file)
        if not file_path.is_file():
            print(f"ERROR: File not found: {file_path}", file=sys.stderr)
            return 1
        return 0 if extract_file(converter, file_path, staging_dir) else 1

    source_dir = Path(args.source_dir)
    files = scan_source_dir(source_dir)
    if not files:
        print(f"No supported documents found under {source_dir}")
        return 0

    print(f"Found {len(files)} document(s) to extract.\n")
    ok = fail = 0
    for f in files:
        if extract_file(converter, f, staging_dir):
            ok += 1
        else:
            fail += 1

    print(f"\nDone.  OK: {ok}  |  Failed: {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())