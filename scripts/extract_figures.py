#!/usr/bin/env python3
"""
Extract figure images from an academic PDF, matched to their figure numbers.

Strategy:
  1. Scan each page for image blocks (type=1 in PyMuPDF dict output) with their positions.
  2. Scan each page for figure captions ("Figure N" / "Fig. N") with their positions.
  3. Match each caption to the nearest image on the same or adjacent page.
  4. Render and save matched images as figure_N.png in the output directory.
  5. Return JSON list: [{number, caption, path, matched}, ...] sorted by figure number.
"""

import sys
import json
import re
import argparse
from pathlib import Path


def _parse_fig_num(n: str):
    """Sort key: ('1', '') < ('2', '') < ('10', '') < ('10', 'a')."""
    m = re.match(r"(\d+)([a-zA-Z]?)", n)
    return (int(m.group(1)), m.group(2).lower()) if m else (0, "")


def extract_figures(pdf_path: str, output_dir: str, dpi: int = 150) -> list:
    """
    Extract and save figure images from *pdf_path* into *output_dir*.

    Returns a list of dicts (sorted by figure number):
        {
          "number":  "1",
          "caption": "Overview of the proposed framework.",
          "path":    "figure_1.png",   # relative to output_dir; None if unmatched
          "matched": True
        }
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(json.dumps({"error": "PyMuPDF not installed. Run: pip install pymupdf"}))
        sys.exit(1)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(json.dumps({"error": f"Cannot open PDF: {e}"}))
        sys.exit(1)

    # ----------------------------------------------------------------
    # Step 1 – collect image blocks with page index and bounding box
    # ----------------------------------------------------------------
    MIN_AREA = 2000  # px² — skip tiny decorative images / icons

    image_blocks = []  # list of {page, bbox, area}
    for page_idx, page in enumerate(doc):
        for block in page.get_text("dict", flags=0)["blocks"]:
            if block.get("type") != 1:
                continue
            x0, y0, x1, y1 = block["bbox"]
            area = (x1 - x0) * (y1 - y0)
            if area < MIN_AREA:
                continue
            image_blocks.append({"page": page_idx, "bbox": block["bbox"], "area": area})

    # ----------------------------------------------------------------
    # Step 2 – collect figure captions with page index and Y position
    # ----------------------------------------------------------------
    cap_re = re.compile(
        r"(?:Figure|Fig\.?)\s*(\d+[a-zA-Z]?)[\.:\s][ \t]*(.+)",
        re.IGNORECASE,
    )

    caption_locs = []  # list of {page, number, caption, y}
    seen_numbers: set = set()

    for page_idx, page in enumerate(doc):
        for block in page.get_text("dict", flags=0)["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line.get("spans", []))
                m = cap_re.match(text.strip())
                if m:
                    num = m.group(1)
                    if num in seen_numbers:
                        continue
                    seen_numbers.add(num)
                    caption_locs.append({
                        "page": page_idx,
                        "number": num,
                        "caption": re.sub(r"\s+", " ", m.group(2)).strip(),
                        "y": line["bbox"][1],
                    })

    # Sort captions by figure number so output is ordered
    caption_locs.sort(key=lambda c: _parse_fig_num(c["number"]))

    # ----------------------------------------------------------------
    # Step 3 – match each caption to the best nearby image block
    # ----------------------------------------------------------------
    def best_image_for(cap):
        """
        Return the image block most likely depicting *cap*, or None.

        Scoring heuristic:
          - Same page preferred over adjacent page.
          - Image above the caption (dy > 0) is a stronger signal than below.
          - Larger images score slightly higher (figures > decorations).
        """
        best, best_score = None, float("-inf")
        for img in image_blocks:
            page_dist = abs(img["page"] - cap["page"])
            if page_dist > 1:
                continue

            if img["page"] == cap["page"]:
                # dy: positive when image is above caption (normal layout)
                dy = cap["y"] - img["bbox"][3]   # caption_top - image_bottom
                proximity = -abs(dy)              # closer → higher score
                position_bonus = 10 if dy >= 0 else 0  # above caption is canonical
            else:
                proximity = -1000 * page_dist
                position_bonus = 0

            score = proximity + position_bonus + img["area"] * 0.0001
            if score > best_score:
                best_score = score
                best = img
        return best

    used_keys: set = set()
    results = []

    for cap in caption_locs:
        img = best_image_for(cap)

        # Avoid assigning the same image block to two figures
        if img is not None:
            key = (img["page"], img["bbox"][0], img["bbox"][1])
            if key in used_keys:
                img = None
            else:
                used_keys.add(key)

        num = cap["number"]
        if img is not None:
            # Render the image region at the requested DPI
            page = doc[img["page"]]
            rect = fitz.Rect(img["bbox"])
            # Add a small margin so we don't clip anti-aliased edges
            rect.x0 = max(0.0, rect.x0 - 4)
            rect.y0 = max(0.0, rect.y0 - 4)
            rect.x1 = min(float(page.rect.width),  rect.x1 + 4)
            rect.y1 = min(float(page.rect.height), rect.y1 + 4)

            mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
            pix = page.get_pixmap(matrix=mat, clip=rect)
            fname = f"figure_{num}.png"
            pix.save(str(out_path / fname))

            results.append({
                "number":  num,
                "caption": cap["caption"],
                "path":    fname,
                "matched": True,
            })
        else:
            results.append({
                "number":  num,
                "caption": cap["caption"],
                "path":    None,
                "matched": False,
            })

    doc.close()
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract figure images from a research PDF, matched to figure numbers."
    )
    parser.add_argument("pdf_path",    help="Path to the PDF file")
    parser.add_argument("output_dir",  help="Directory to save extracted figure images")
    parser.add_argument("--dpi", type=int, default=150,
                        help="Render resolution in DPI (default: 150)")
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(json.dumps({"error": f"File not found: {args.pdf_path}"}))
        sys.exit(1)

    figures = extract_figures(args.pdf_path, args.output_dir, args.dpi)
    print(json.dumps(figures, ensure_ascii=False, indent=2))
