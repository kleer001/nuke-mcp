#!/usr/bin/env python3
"""Ingest Nuke documentation into the BM25 RAG index.

Usage:
    uv run python scripts/ingest_docs.py [--docs-dir /path/to/nuke/docs]

Supports:
    - Nuke Python API HTML docs (from a local Nuke install)
    - Markdown files (facility docs)
    - Plain text files
"""

import argparse
import re
import sys
from pathlib import Path

# Add src to path so we can import nukemcp
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nukemcp.rag import BM25Index, Document


def strip_html(html: str) -> str:
    """Remove HTML tags, leaving plain text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def ingest_directory(index: BM25Index, docs_dir: Path, source: str):
    """Ingest all supported files from a directory into the index."""
    count = 0
    for fp in sorted(docs_dir.rglob("*")):
        if fp.is_dir():
            continue
        suffix = fp.suffix.lower()
        if suffix in (".html", ".htm"):
            content = strip_html(fp.read_text(encoding="utf-8", errors="ignore"))
        elif suffix in (".md", ".txt", ".rst"):
            content = fp.read_text(encoding="utf-8", errors="ignore")
        else:
            continue

        if len(content.strip()) < 50:
            continue  # Skip near-empty files

        doc_id = str(fp.relative_to(docs_dir))
        title = fp.stem.replace("_", " ").replace("-", " ").title()
        index.add_document(Document(id=doc_id, title=title, content=content, source=source))
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Ingest docs into NukeMCP RAG index")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        help="Directory containing Nuke documentation files (HTML, MD, TXT)",
    )
    parser.add_argument(
        "--facility-dir",
        type=Path,
        help="Directory containing facility-specific documentation",
    )
    args = parser.parse_args()

    index = BM25Index()

    # Ingest bundled docs if they exist
    bundled = Path(__file__).parent.parent / "docs" / "nuke_api"
    if bundled.is_dir():
        count = ingest_directory(index, bundled, "nuke_api")
        print(f"Ingested {count} files from bundled docs")

    # Ingest user-specified Nuke docs
    if args.docs_dir and args.docs_dir.is_dir():
        count = ingest_directory(index, args.docs_dir, "nuke_api")
        print(f"Ingested {count} files from {args.docs_dir}")

    # Ingest facility docs
    if args.facility_dir and args.facility_dir.is_dir():
        count = ingest_directory(index, args.facility_dir, "facility")
        print(f"Ingested {count} files from {args.facility_dir}")

    if not index.docs:
        print("No documents ingested. Provide --docs-dir or --facility-dir, or add files to docs/nuke_api/.")
        return

    index.save()
    print(f"Index saved with {len(index.docs)} total documents")


if __name__ == "__main__":
    main()
