---
name: paper-deconstructor
description: Deconstruct academic research papers (PDF) into structured Chinese knowledge files — summary, methodology, figures, Q&A, and pseudocode — then sync to Zotero. Use this skill whenever a user asks to analyze, read, process, summarize, understand, extract knowledge from, or deconstruct a research paper or PDF. Also triggers for Chinese equivalents like "帮我读这篇论文", "分析这篇文章", "总结一下这个PDF", or when the user drops/mentions a .pdf file path in the context of academic work. Works for standard research papers, review/survey papers, and simulation/computational papers.
---

# Academic Paper Deconstruction

Extract and organize knowledge from a research PDF into 5 structured files, then sync to Zotero.

**Output language rule**: All files are written in **Chinese**, except `code.md` which uses English code with Chinese comments. Technical terms keep their original English names and abbreviations inline — e.g., "物理信息神经网络 (Physics-Informed Neural Networks, PINNs)".

**Math formatting rule**: Inline variables, symbols, and short expressions always use LaTeX inline format — `$x$`, `$\lambda$`, `$\mathcal{L}_{\text{data}}$` — never backtick code blocks for math. Block equations use `$$ ... $$`. This applies to every output file including summary, method, qa, and picture.

## Prerequisites

Install the required Python libraries before running the workflow:

```bash
python -m pip install pymupdf pyzotero python-dotenv
```

For scanned PDFs, image-only formulas, or low-quality figure captions, install OCR/image helpers as well:

```bash
python -m pip install pytesseract pdf2image pillow
```

OCR also needs system binaries:
- **Tesseract OCR** available on `PATH` (`tesseract --version` should work)
- **Poppler** for `pdf2image` on platforms that require it

Optional sync integrations:
- ChromaDB sync: `python -m pip install chromadb`
- Obsidian sync: no Python package is required; only `OBSIDIAN_VAULT_PATH` in `.env`

Confirm a `.env` file exists at `<skill_dir>/.env` (the directory where this `SKILL.md` lives) with:
- `ZOTERO_USER_ID`
- `ZOTERO_API_KEY`

Optional sync vars (add to the same .env if needed): `OBSIDIAN_VAULT_PATH`, `CHROMADB_PATH`

## Step 1: Extract PDF Content

Find the skill's own directory (where this SKILL.md lives), then run:

```bash
python "<skill_dir>/scripts/extract_pdf.py" "<pdf_path>"
```

This outputs JSON with: `metadata`, `full_text`, `sections`, `figures`, `has_appendix`, `is_review`, `is_computational`.

If the PDF is image-based (scanned) and text extraction yields fewer than 500 characters, **attempt OCR before giving up**. Invoke any available OCR tool, for example:
- `pdf2image` + `pytesseract`: convert each page to an image, then run `pytesseract.image_to_string(page_image)`
- PyMuPDF page rendering + `pytesseract`: render pages with `fitz` at 200-300 DPI, then OCR the image
- System CLI: `tesseract <image_file> stdout -l eng`
- Platform OCR APIs (e.g., Windows OCR, macOS Vision, Google Cloud Vision) if available

If OCR succeeds and yields sufficient text, continue with the normal workflow using the OCR output and note internally which pages came from OCR. If OCR is unavailable or still yields fewer than 500 characters, warn the user: "This appears to be a scanned PDF — text extraction is limited. Results may be incomplete."

## Step 2: Determine Output Directory

Create a folder named after the paper (slugified title or filename stem) **in the same directory as the PDF**:

```
<pdf_parent_dir>/<paper_slug>/
```

Example: `/papers/attention_is_all_you_need.pdf` → `/papers/attention_is_all_you_need/`

Use the title from extracted metadata if available; otherwise use the PDF filename stem.

## Step 2b: Extract Figure Images

Run this immediately after creating the output directory, so images are ready when writing `picture.md`:

```bash
python "<skill_dir>/scripts/extract_figures.py" "<pdf_path>" "<output_dir>/images"
```

This saves each detected figure as `images/figure_N.png` inside the output directory and prints a JSON list:

```json
[{"number": "1", "caption": "...", "path": "figure_1.png", "matched": true}, ...]
```

Keep this list — you'll use it when writing `picture.md`.

After the script runs, verify the images rather than assuming extraction succeeded:
- Check that every returned `path` exists under `<output_dir>/images`.
- If important figures are missing, rerun with higher DPI (`--dpi 200` or `--dpi 300`) and use screenshot fallbacks from the relevant PDF page regions.
- If captions are missing or garbled, OCR the rendered page/region to recover the figure number and caption.
- For vector diagrams, plots, multi-panel figures, or formulas embedded as images, prefer a page-region screenshot over a broken or empty crop.
- Do not finish `picture.md` until each detected figure/table caption is either backed by a saved image or explicitly marked as extraction failed after OCR/screenshot attempts.

## Step 3: Read and Analyze the Content

Before writing any files, read the full extracted text carefully and reason paragraph by paragraph. Do a private reading pass that tracks what each paragraph contributes: problem setup, assumption, derivation, method step, experiment detail, result, limitation, or related work. Do not rely only on the abstract, captions, or section headings. Re-read paragraphs that contain formulas, definitions, algorithm steps, or claims that later sections depend on.

Identify:
- The core research problem being addressed
- The proposed method or framework
- Key results and their significance
- Whether it's a **review paper** (surveys existing work) or **original research**
- Whether it involves **simulation, algorithms, or numerical computation**

For long papers (>40 pages), still perform a paragraph-level pass over the method, results, figures, conclusion, and appendix. You may compress routine related-work and repetitive experiment paragraphs, but do not skip derivations, assumptions, equations, figure explanations, or result paragraphs that support the paper's claims.

## Step 4: Generate the 5 Output Files

See `references/output_formats.md` for exact templates. Generate all files into the output directory from Step 2.

### summary.md — 全文概述

Cover in order:
1. **研究背景与问题** — What problem does this paper address and why does it matter?
2. **核心创新点** — What are the key innovations? What specifically is new compared to prior work?
3. **与现有工作的对比** — How does this work differ from / improve upon previous methods?
4. **主要结论与贡献** — What are the main findings and contributions?
5. **局限性与不足** — Acknowledged limitations or weaknesses
6. **未来展望** — Suggested future directions

### method.md — 方法详解

**Read the algorithm/method section paragraph by paragraph** — don't skim. Every formula, assumption, and design decision matters. Go back and re-read any paragraph you're unsure about before writing.

Cover in order:
1. **理论基础** — The physical, mathematical, or computational theory this method is grounded in; governing equations it derives from
2. **核心假设** — Every explicit and implicit assumption the method makes (geometry, physical regime, data properties, scale constraints)
3. **模型/框架结构** — Architecture, components, and data/information flow between them
4. **数学公式** — Every important equation in LaTeX block format (`$$ ... $$`); define each symbol and explain what the equation represents
5. **计算流程** — Step-by-step walkthrough of how the method executes: inputs → intermediate stages → outputs
6. **细节设置** — Hyperparameters, mesh/time-step settings, convergence criteria, loss term weights, initialization strategies, training tricks
7. **适用范围** — Scope: 2D vs 3D, problem types (steady/transient, linear/nonlinear), model size requirements, hardware constraints
8. **方法缺陷** — Where the method fails or degrades; think critically beyond what the authors themselves acknowledge
9. **附录方法** (if `has_appendix` is true) — Additional methodology, derivations, or equations from the appendix

Formula verification is mandatory before finalizing `method.md`:
- Cross-check each important equation against the extracted text, the PDF page image, or OCR output.
- Verify subscripts, superscripts, Greek letters, operators, equation numbers, and symbol definitions.
- Check dimensional/semantic consistency when possible: left and right sides should describe the same quantity, and loss/objective terms should have sensible signs and weights.
- If an equation is ambiguous because extraction mangled it, inspect a screenshot of the source page/region and transcribe from the image. Mark uncertainty explicitly instead of inventing missing terms.

**For review papers**, add a section at the end:

```markdown
## 方法对比分析

| 方法 | 计算方式 | 适用场景 | 优点 | 局限 |
|------|---------|---------|------|------|
| ...  | ...     | ...     | ...  | ...  |
```

### picture.md — 图表解析

Use the figure list from Step 2b. Write one section per figure, **in ascending figure-number order**. For each figure:

```markdown
## 图 N：<figure caption verbatim>

![图 N](images/figure_N.png)

**解析**：<What does this figure show? What insight does it convey, and why did the authors include it?>
```

The figure list now includes a `screenshot` field:
- `matched: true, screenshot: false` — discrete image block extracted cleanly. Embed normally.
- `matched: true, screenshot: true` — vector graphic or complex figure; a page-region screenshot was captured as fallback. Embed the image but add a small note `（页面截图）` after the caption line so the reader knows it may include surrounding whitespace or adjacent text.
- `matched: false` — extraction failed entirely (rare). Omit the `![]()` line and add `（图片提取失败，仅文字描述）` at the start of the analysis.

If Step 2b returned no figures at all, fall back to scanning the full text for "Figure N" / "Fig. N" patterns manually and write text-only entries.

When a figure contains embedded formulas, axes, legends, or small labels, inspect the saved image. If labels are unreadable, rerender that region at higher DPI and/or OCR the image so the explanation reflects the actual visual content.

### qa.md — 知识问答

Generate 8–12 Q&A pairs. The goal is to force deep engagement with the paper — questions a researcher would ask after reading carefully, not a student skimming the abstract. Avoid surface-level lookups ("What does X stand for?"). Instead, aim for questions that require reasoning, synthesis, or critical evaluation:

- **推导类**：某个设计选择背后的数学原因是什么？某公式是如何从基本原理推导出来的？
- **机制类**：方法的某个组件为什么这样设计？去掉它会发生什么？
- **对比类**：与某个具体的已有方法相比，本文方法在哪个假设上做了不同的取舍？
- **失效类**：在什么条件下该方法会失效？作者是否意识到了这一点？
- **延伸类**：如果将该方法应用到论文未测试的场景（不同维度、不同物理问题、更大规模），预期会遇到什么挑战？
- **实验解读类**：某个实验结果说明了什么？它是否充分支持了作者的论断？

Format:
```markdown
**Q1: <question>**
A: <answer>
```

### code.md — 伪代码实现 (conditional)

Only generate if `is_computational` is true OR the paper describes a specific algorithm that could be implemented.

Write Python pseudocode that captures the core algorithm. Comments in Chinese, code in English. Include:
- Main algorithm / training loop
- Key equations as code
- Data flow and processing steps

Wrap all pseudocode in a **single** fenced ` ```python ... ``` ` block. Do not split into multiple blocks unless there are genuinely separate, independent algorithms (e.g., a review paper comparing distinct models — give each its own labeled block).

If it's a review paper with multiple models, write a short pseudocode stub for each main model being compared.

## Step 5: Sync to Zotero

After all files are generated, run:

```bash
python "<skill_dir>/scripts/zotero_sync.py" \
  "<pdf_path>" \
  "<output_dir>" \
  --metadata '<metadata_json>'
```

Where `<metadata_json>` is the JSON object from Step 1's `metadata` field.

Report the Zotero item URL on success, or the error message on failure.

## Step 6: Optional Sync (if configured)

Run only if `.env` contains the relevant variable:

```bash
python "<skill_dir>/scripts/optional_sync.py" \
  "<output_dir>" \
  --title "<paper_title>"
```

The script auto-detects which integrations are enabled and skips silently if vars are absent.

## Step 7: Report to User

After all steps, report:

```
✅ 论文解析完成：<paper_title>

📁 输出目录：<output_dir>
  - summary.md    ✓
  - method.md     ✓
  - picture.md    ✓ (N 张图)
  - qa.md         ✓ (N 组问答)
  - code.md       ✓/— (如适用)

📚 Zotero：<item_url 或 skip/error message>
🔗 Obsidian：<已同步/未配置>
🧠 ChromaDB：<已同步/未配置>
```

## Edge Cases

- **No abstract found**: Use the first paragraph of the introduction as the abstract.
- **No section headers detected**: Process the full text as a continuous flow — don't refuse to generate output just because sections weren't auto-detected.
- **Very short paper (<5 pages)**: This might be a conference abstract or letter — note this in summary.md and generate what's possible.
- **Paper not in English**: Translate technical content into Chinese output as usual; if the source is already Chinese, still produce Chinese output.
