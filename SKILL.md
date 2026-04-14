---
name: paper-deconstructor
description: Deconstruct academic research papers (PDF) into structured Chinese knowledge files — summary, methodology, figures, Q&A, and pseudocode — then sync to Zotero. Use this skill whenever a user asks to analyze, read, process, summarize, understand, extract knowledge from, or deconstruct a research paper or PDF. Also triggers for Chinese equivalents like "帮我读这篇论文", "分析这篇文章", "总结一下这个PDF", or when the user drops/mentions a .pdf file path in the context of academic work. Works for standard research papers, review/survey papers, and simulation/computational papers.
---

# Academic Paper Deconstruction

Extract and organize knowledge from a research PDF into 5 structured files, then sync to Zotero.

**Output language rule**: All files are written in **Chinese**, except `code.md` which uses English code with Chinese comments. Technical terms keep their original English names and abbreviations inline — e.g., "物理信息神经网络 (Physics-Informed Neural Networks, PINNs)".

## Prerequisites

Confirm a `.env` file exists at `~/.claude/skills/paper-deconstructor/.env` with:
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
- System CLI: `tesseract <image_file> stdout -l eng`
- Platform OCR APIs (e.g., Windows OCR, macOS Vision, Google Cloud Vision) if available

If OCR succeeds and yields sufficient text, continue with the normal workflow using the OCR output. If OCR is unavailable or still yields fewer than 500 characters, warn the user: "This appears to be a scanned PDF — text extraction is limited. Results may be incomplete."

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

## Step 3: Read and Analyze the Content

Before writing any files, read the full extracted text carefully. Identify:
- The core research problem being addressed
- The proposed method or framework
- Key results and their significance
- Whether it's a **review paper** (surveys existing work) or **original research**
- Whether it involves **simulation, algorithms, or numerical computation**

For long papers (>40 pages), prioritize abstract, introduction, method section, conclusion, and any appendix — you don't need to summarize every experiment detail.

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

- If `matched: false` for a figure (image could not be extracted), omit the `![]()` line and add `（图片提取失败，仅文字描述）` at the start of the analysis.
- If Step 2b returned no figures at all, fall back to scanning the full text for "Figure N" / "Fig. N" patterns manually and write text-only entries.

### qa.md — 知识问答

Generate 8–12 Q&A pairs that cover the most important concepts. Mix:
- Conceptual understanding (What is X? Why does Y matter?)
- Technical details (How is Z computed? What are the key parameters?)
- Critical thinking (What are the limitations of this approach?)

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
