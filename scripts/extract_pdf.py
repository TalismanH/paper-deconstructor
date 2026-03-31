#!/usr/bin/env python3
"""Extract structured content from academic PDF papers using PyMuPDF (fitz)."""

import sys
import json
import re
import argparse
from pathlib import Path


def extract_sections(text: str) -> dict:
    """Attempt to split paper text into named sections by common academic headings."""
    section_headers = re.compile(
        r'^(?:\d+\.?\s+)?('
        r'abstract|introduction|related work|background|literature review|'
        r'method|methods|methodology|approach|framework|model|formulation|'
        r'experiment|experiments|experimental setup|experimental results|evaluation|'
        r'results?|findings|analysis|discussion|conclusion|conclusions|'
        r'concluding remarks|references|bibliography|appendix|supplementary|'
        r'acknowledgements?|acknowledgments?'
        r')\b.*$',
        re.IGNORECASE | re.MULTILINE,
    )

    sections = {}
    current_name = "preamble"
    current_lines = []

    for line in text.splitlines():
        m = section_headers.match(line.strip())
        if m and len(line.strip()) < 80:
            sections[current_name] = "\n".join(current_lines).strip()
            current_name = m.group(1).lower()
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_name] = "\n".join(current_lines).strip()
    return {k: v for k, v in sections.items() if v}


def extract_figure_captions(text: str) -> list:
    """Extract figure/table captions with their numbers."""
    pattern = re.compile(
        r'(?:Figure|Fig\.?|TABLE|Table)\s*(\d+[a-zA-Z]?)[\.:][ \t]*([^\n]+(?:\n(?![\n\s*Figure\s*Fig\s*TABLE\s*Table])[^\n]+){0,3})',
        re.IGNORECASE,
    )
    captions = []
    seen = set()
    for m in pattern.finditer(text):
        num = m.group(1)
        caption = re.sub(r'\s+', ' ', m.group(2)).strip()
        if num not in seen and len(caption) > 5:
            captions.append({"number": num, "caption": caption})
            seen.add(num)
    return captions


def extract_formulas(text: str) -> list:
    """Heuristically identify lines that look like mathematical expressions."""
    formula_pattern = re.compile(
        r'(?:(?:[A-Za-z]\s*[=+\-\*/^]\s*)|(?:\\[a-zA-Z]+\{)|\bEq\b|\bEquation\b)'
        r'.{5,120}'
    )
    found = []
    for line in text.splitlines():
        stripped = line.strip()
        if formula_pattern.search(stripped) and len(stripped) < 200:
            found.append(stripped)
    return found[:50]  # cap to avoid noise


def classify_paper(metadata: dict, text: str) -> dict:
    """Classify paper type based on title and first 3000 characters."""
    sample = (metadata.get("title", "") + " " + text[:3000]).lower()

    is_review = bool(re.search(
        r'\b(review|survey|overview|systematic review|literature review|meta.analysis)\b',
        sample,
    ))

    is_computational = bool(re.search(
        r'\b(simulation|numerical|algorithm|computational|implementation|'
        r'python|matlab|pseudocode|source code|open.source|github|'
        r'finite element|finite difference|monte carlo|neural network|'
        r'deep learning|machine learning|training|inference)\b',
        sample,
    ))

    has_appendix = bool(re.search(r'\bappendix\b', text, re.IGNORECASE))

    return {
        "is_review": is_review,
        "is_computational": is_computational,
        "has_appendix": has_appendix,
    }


def extract_paper(pdf_path: str) -> dict:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return {"error": "PyMuPDF not installed. Run: pip install pymupdf"}

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": f"Cannot open PDF: {e}"}

    # --- Metadata ---
    raw_meta = doc.metadata or {}
    metadata = {
        "title": raw_meta.get("title", "").strip(),
        "author": raw_meta.get("author", "").strip(),
        "subject": raw_meta.get("subject", "").strip(),
        "keywords": raw_meta.get("keywords", "").strip(),
        "creator": raw_meta.get("creator", "").strip(),
        "total_pages": len(doc),
    }

    # --- Full text ---
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    full_text = "\n".join(pages_text)

    doc.close()

    # Quality check for scanned PDFs
    char_count = len(full_text.strip())

    sections = extract_sections(full_text)
    figures = extract_figure_captions(full_text)
    formulas = extract_formulas(full_text)
    paper_type = classify_paper(metadata, full_text)

    return {
        "metadata": metadata,
        "full_text": full_text,
        "char_count": char_count,
        "sections": sections,
        "figures": figures,
        "formulas_sample": formulas,
        "has_appendix": paper_type["has_appendix"],
        "is_review": paper_type["is_review"],
        "is_computational": paper_type["is_computational"],
        "scanned_warning": char_count < 500,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract content from a research PDF.")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--output", "-o", default="-",
        help="Output file path for JSON (default: stdout)",
    )
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(json.dumps({"error": f"File not found: {args.pdf_path}"}))
        sys.exit(1)

    result = extract_paper(args.pdf_path)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(output_json)
    else:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Extraction saved to {args.output}", file=sys.stderr)
