# paper-deconstructor

Deconstruct academic PDFs into Chinese research notes, figure explanations, Q&A, pseudocode, and Zotero/optional knowledge-base sync.

## Required Runtime Libraries

Install the core dependencies:

```bash
python -m pip install pymupdf pyzotero python-dotenv
```

Install OCR/image helpers for scanned PDFs, image-only formulas, and figure caption recovery:

```bash
python -m pip install pytesseract pdf2image pillow
```

OCR also requires system binaries:
- Tesseract OCR on `PATH`
- Poppler when using `pdf2image` on platforms that require it

Optional integrations:
- ChromaDB sync: `python -m pip install chromadb`
- Obsidian sync: no Python package required; configure `OBSIDIAN_VAULT_PATH` in `.env`
