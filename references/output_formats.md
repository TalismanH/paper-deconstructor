# Output File Format Reference

Exact templates for each output file produced by the paper-deconstructor skill.
All text (headings included) is in **Chinese** except `code.md`.
Technical terms keep their English names inline: "物理信息神经网络 (Physics-Informed Neural Networks, PINNs)".

**Math formatting**: Inline variables and expressions use LaTeX — `$x$`, `$\lambda$`, `$\nabla u$` — never backtick code blocks for math. Block equations use `$$ ... $$`.

---

## summary.md — 全文概述

```markdown
# 全文概述：<论文标题>

> **作者**：<Authors>
> **来源**：<Journal / Conference, Year>
> **关键词**：<keywords>

---

## 1. 研究背景与问题

<What specific problem does this paper address? What gap in the literature does it fill?
What are the limitations of existing approaches that motivate this work?>

## 2. 核心创新点

<What is specifically new in this work? List 2–4 concrete innovations.
Distinguish from incremental improvements — what is genuinely novel?>

## 3. 与现有工作的对比

<How does this approach differ from the most relevant prior methods?
Key improvements in accuracy, efficiency, generalizability, or applicability.>

## 4. 主要结论与贡献

<What are the key results? How significant are they?
What is the broader impact on the field?>

## 5. 局限性与不足

<What are the acknowledged limitations? What scenarios does the method fail in or not address?>

## 6. 未来展望

<What future directions do the authors suggest? What open problems remain?>
```

---

## method.md — 方法详解

```markdown
# 方法详解：<论文标题>

---

## 1. 理论基础

<The physical, mathematical, or computational theory this method is grounded in.
Governing equations it derives from. Why these theoretical foundations justify the approach.>

## 2. 核心假设

<List every explicit and implicit assumption the method makes:
- 几何与维度：2D/3D？结构化/非结构化网格？
- 物理条件：线性/非线性？稳态/瞬态？特定流态或变形范围？
- 数据要求：噪声水平、采样密度、数据完整性？
- 规模约束：参数量、域大小、分辨率限制？
标注哪些假设是作者明确提出的，哪些是隐含的。>

## 3. 模型/框架结构

<Architecture and components. How are they connected?
Include a high-level description of the data/information flow.>

## 4. 核心数学公式

<All important equations, formatted in LaTeX blocks:>

$$
\mathcal{L} = \mathcal{L}_{\text{data}} + \lambda \mathcal{L}_{\text{physics}}
$$

<For each equation: what it represents, define every symbol, explain the physical/mathematical intuition.>

## 5. 计算流程

<Step-by-step execution of the method:
1. **输入**：方法接收什么数据/参数？
2. **预处理**：归一化、网格划分、采样等
3. **核心计算**：每个阶段发生了什么？
4. **输出**：方法返回什么结果？
用编号步骤或伪代码使流程具体化。>

## 6. 细节设置

<Specific settings that matter for the method to work:
- 超参数及其典型值与敏感性
- 网格/时间步长选择
- 收敛标准和停止条件
- 损失项权重、正则化策略
- 初始化和训练技巧（如适用）>

## 7. 适用范围

<Where does this method work well:
- **维度**：支持 2D / 3D？两者性能是否有差异？
- **问题类型**：稳态/瞬态、线性/非线性、适用的 PDE 类型
- **规模要求**：可处理的问题规模或模型大小范围
- **硬件需求**：计算资源要求
- **已验证领域**：论文中实际测试过的应用场景>

## 8. 方法缺陷

<Critical limitations — go beyond what the authors acknowledge:
- 哪些问题类型会导致方法失效或精度下降？
- 违反哪些假设会破坏方法的有效性？
- 计算成本 / 可扩展性问题
- 特定条件下的精度或收敛问题
- 实际使用中的困难（例如难以调参、需要领域专家知识）>

## 9. 附录方法（如适用）

<Additional methodology, derivations, or equations from the appendix.>

---
<!-- Only for review papers: -->

## 方法对比分析（综述论文专用）

| 方法名称 | 计算方式 | 适用场景 | 主要优点 | 主要局限 |
|---------|---------|---------|---------|---------|
| Method A (Abbreviation) | ... | ... | ... | ... |
| Method B (Abbreviation) | ... | ... | ... | ... |
```

---

## picture.md — 图表解析

```markdown
# 图表解析：<论文标题>

---

## 图 1：<Figure 1 caption verbatim>

![图 1](images/figure_1.png)

**解析**：<What does this figure show? What insight does it convey?
Why did the authors include it — what argument does it support?
For result figures: what do the numbers or curves mean for the paper's claims?>

---

## 图 2：<Figure 2 caption verbatim>

![图 2](images/figure_2.png)

**解析**：<...>

<!-- Continue for all figures in ascending figure-number order.
     If image extraction failed for a figure (matched: false), omit the ![]() line
     and start the analysis with "（图片提取失败，仅文字描述）".
     If a figure has subfigures (a)(b)(c), describe each subfigure within the same section. -->
```

---

## qa.md — 知识问答

```markdown
# 知识问答：<论文标题>

---

**Q1: <推导类 — 某个公式或设计选择背后的数学原因>**
A: <Answer. Trace the reasoning from first principles, not just restate the paper.>

**Q2: <机制类 — 某个组件为什么这样设计？去掉它会怎样？>**
A: <...>

**Q3: <对比类 — 与某具体已有方法相比，本文在哪个假设上做了不同取舍？>**
A: <...>

**Q4: <失效类 — 在什么条件下该方法会失效？作者是否意识到了？>**
A: <...>

**Q5: <延伸类 — 应用到论文未测试的场景会遇到什么挑战？>**
A: <...>

**Q6: <实验解读类 — 某个实验结果说明了什么？是否充分支持作者的论断？>**
A: <...>

**Q7: <公式推导或理论理解>**
A: <...>

**Q8: <关键参数敏感性 — 某超参数的选择对结果影响有多大？>**
A: <...>

<!-- Add up to 12 pairs. Every question should require reasoning or synthesis to answer —
     avoid trivial lookups like "What does X stand for?" or "What dataset was used?".
     Answers should include inline LaTeX for any variables or expressions: $\lambda$, $\mathcal{L}$, etc. -->
```

---

## code.md — 伪代码实现（仅限计算/模拟类论文）

````markdown
# 伪代码实现：<Paper Title>

> Based on: <paper citation>
> Language: Python pseudocode (illustrative, not production-ready)
> Comments: Chinese | Code: English

```python
import numpy as np
# (add relevant libraries as described in the paper)

# ----------------------------------------------------------------
# 数据准备 / Data Preparation
# ----------------------------------------------------------------
def prepare_data(config):
    """
    根据论文第X节准备训练数据。
    Returns training data arrays.
    """
    # 从域内随机采样配点 (collocation points)
    x_colloc = np.random.uniform(config.x_min, config.x_max, config.n_colloc)
    ...
    return x_colloc, ...


# ----------------------------------------------------------------
# 主模型 / Core Model
# ----------------------------------------------------------------
class CoreModel:
    """
    实现论文中描述的<模型名称>。
    Architecture: <brief description>
    """
    def __init__(self, ...):
        ...

    def forward(self, x):
        """前向传播 / Forward pass."""
        ...


# ----------------------------------------------------------------
# 损失函数 / Loss Function
# ----------------------------------------------------------------
def compute_loss(model, x_data, u_data, x_colloc):
    """
    计算总损失：L = L_data + lambda * L_physics
    参见论文公式 (N).
    """
    loss_data = ...      # 数据拟合项
    loss_physics = ...   # 物理约束项
    return loss_data + config.lambda_ * loss_physics


# ----------------------------------------------------------------
# 训练循环 / Training Loop
# ----------------------------------------------------------------
def train(model, optimizer, epochs):
    for epoch in range(epochs):
        loss = compute_loss(...)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if epoch % 100 == 0:
            print(f"Epoch {epoch}: loss = {loss.item():.6f}")
```

<!-- For review papers comparing multiple models, give each its own labeled ```python block:
     ## Model A (Abbreviation)
     ```python ... ```
     ## Model B (Abbreviation)
     ```python ... ```
     Keep each stub short (10–30 lines). Focus on the key algorithmic difference. -->
````
