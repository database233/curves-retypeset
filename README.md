# 《形形色色的曲线》LaTeX 忠实重排版项目

本项目为蒋声先生所著《形形色色的曲线》（上海教育出版社 1985 年第 1 版，“中学生文库”系列）的全书 LaTeX 重排版源码与成品工程。全书按原书 **小 32 开（`130mm × 184mm`）** 物理开本忠实重排，覆盖 **1985 版封面复刻、扉页、前言、目录、正文全部 100 节、附录曲线名称对照表、重排版校订注记与版权页**，成书共 **193 页**。

---

## 一、目录结构

```text
book_project/
├── main.tex                          # 全书主控文件（导言引入、前置/正文/后置编排）
├── preamble.tex                      # 版心尺寸、字体、TikZ/PGFPlots、古典数学记号宏定义
├── main.pdf                          # 已编译验证的全书成品 PDF（193 页）
├── sections_index.json               # 原书 100 节与原扫描 PDF 页码映射索引
├── .gitignore                        # 忽略 LaTeX 中间文件与核对渲染缓存
├── README.md                         # 本使用与迁移说明文档
│
├── frontmatter/                      # 前置部分
│   ├── cover.tex                     # 1985 原版封面纯矢量 TikZ 复刻（鹦鹉螺螺线 + 第 79 节伪球面与测地线）
│   ├── titlepage.tex                 # “中学生文库”扉页及矢量徽标
│   └── preface.tex                   # 前言
│
├── sections/                         # 正文 100 节独立源码（共 88 节含插图，169 幅 TikZ 矢量图）
│   ├── sec_001.tex
│   ├── ...
│   └── sec_100.tex
│
├── backmatter/                       # 后置部分
│   ├── appendix_terms.tex            # 附：曲线名称汉英对照表（longtable）
│   ├── errata_notes.tex              # 附：重排版校订注记（汇总原书误植与插图数理订正）
│   └── colophon.tex                  # 版权页与内容提要（含弧形 ZXS 矢量徽标）
│
├── assets/
│   └── generated/                    # 5 幅实景/科普插图（由 sec_006、007、021、042 引用）
│       ├── fig_006_1.png             # 图 6.1 杰尼西亚山洞（狄奥尼修斯之耳）
│       ├── fig_007_3.png             # 图 7.3 建筑师小模型
│       ├── fig_007_4.png             # 图 7.4 双曲抛物面屋顶实景
│       ├── fig_021_1.png             # 图 21.1 熊猫滚圆玩具
│       └── fig_042_1.png             # 图 42.1 手持大齿轮套小齿轮画花曲线
│
└── scripts/                          # 编译校验与对照工具（均使用相对路径，可跨机直接运行）
    ├── audit_build.py                # 扫描 main.log 红线指标，支持按需导出页面 PNG
    ├── verify_sec017_and_redlines.py # 全书空白页、页脚碰撞及第 17 节单页收敛检查
    ├── clean_generated_art.py        # 线稿白底去灰与自动裁边辅助工具
    ├── prepare_pages.py              # 从原书扫描 PDF 提取 300 DPI 参考页（供对照使用）
    └── build_compare_cards.py        # 生成“左重排 / 右原书”双栏对照卡（供人工或 AI 审校）
```

---

## 二、运行环境与依赖

### 1. LaTeX 发行版与字体
- **编译器**：`XeLaTeX`（已在 TeX Live 2026 测试通过）
- **中文字体**：`ctexbook` 使用 `fontset=fandol`（TeX Live 默认内置 Fandol 宋体/黑体/仿宋/楷体，跨平台兼容性好）
- **西文与数学字体**：`TeX Gyre Termes` + `newtxmath` + `yhmath`（提供圆弧符号 `\wideparen`）
- **主要宏包**：`geometry`、`amsmath`、`amssymb`、`tikz`、`pgfplots`（`compat=1.18`）、`graphicx`、`wrapfig`、`caption`、`longtable`、`booktabs`、`array`、`xcolor`、`fancyhdr`、`titlesec`、`titletoc`、`hyperref`

### 2. Python 脚本依赖（仅核对与辅助脚本需要）
- Python 3.10+
- `pymupdf`（`import pymupdf`）
- `pillow`（仅 `build_compare_cards.py` 需要）
- `opencv-python`、`numpy`（仅 `clean_generated_art.py` 需要）

---

## 三、编译与质量校验流程

在 `book_project/` 目录下执行以下流程：

### 1. 两遍编译全书 PDF
必须运行 **两遍 `xelatex`**（确保目录、`hyperref` 书签及封面的 `remember picture, overlay` 坐标完全收敛）：

```bash
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

### 2. 日志红线与版式校验
```bash
# 1) 检查 main.log 编译红线（Errors=0, Missing chars=0, Overfull hbox >= 1.5pt = 0, Undefined refs=0）
python scripts/audit_build.py

# 如需将特定页或全书导出为 PNG 查看，可追加 --render 参数（输出至 _audit_renders/）：
# python scripts/audit_build.py --render 1,33
# python scripts/audit_build.py --render all

# 2) 检查空白页、页脚数字碰撞及第 17 节单页收敛
python scripts/verify_sec017_and_redlines.py
```

### 3. 重建“重排 vs 原书”双栏对照卡（可选）
若需修改插图后与原书扫描 PDF（`形形色色的曲线__蒋声-中学生文库.pdf`）逐节对照：

```bash
python scripts/prepare_pages.py "原书PDF路径（若位于上一级目录可省略）"
python scripts/audit_build.py --render all
python scripts/build_compare_cards.py
```

生成的对照卡位于 `_compare_cards/`（构建完可随时清理，不影响源码）。

---

## 四、排版约定与数学记号规范（后续修改必读）

1. **忠实保留原书 1985 年记号习惯**：
   - 三角/双曲函数使用 [preamble.tex](preamble.tex) 定义的传统记号：`\tg`（正切）、`\ctg`（余切）、`\arctg`、`\arcctg`、`\sh`、`\ch`、`\thyp`、`\cth`。
   - 圆弧记号使用 `\arc{AB}`（基于 `yhmath` 的 `\wideparen`）。
   - 微分算子使用 `\dd`（如 `\int f(x)\dd x`）。
2. **窄版心防溢出与防踩脚控制**：
   - 开本为 `130mm × 184mm`，左右页边距各 `14mm`，正文 `9.5pt`、行距 `1.28`。
   - 图文混排优先使用 `wrapfig` 或居中 `tikzpicture`；**切勿在 `\end{minipage}` 后漏掉空行**，以免下一段行距异常压缩（第 17、50 节曾重点排查此类问题）。
   - 多行长公式注意断行或使用 `aligned`，保证 `Overfull \hbox (>= 1.5pt)` 始终为 `0`。
3. **原书错漏订正机制（校订分离原则）**：
   - 若发现原书存在**文字误植**或**插图数学原理错误**（如第 24 节图 24.2 内摆线绕扣误绘、第 38 节玫瑰线倒置、第 45 节刀尖轨迹方位差 $180^\circ$ 等），重排版中应**绘制数学上正确的图像或订正文字**，并在对应节加随文 `\footnote{...}` 简明说明，同时在 [backmatter/errata_notes.tex](backmatter/errata_notes.tex) 补充汇总条目。
4. **封面结构说明（`frontmatter/cover.tex`）**：
   - 采用全页 `tikzpicture[remember picture, overlay]` 矢量绘制，编译需至少 2 遍。
   - 左上主骨架为单条顺时针外延对数螺线（`2.85pt`）及 C 形气室隔壁；中下部白色旋转曲面对应第 79 节《曳物线与伪球面》，曲面上的 10 条绿色曲线还原了原封面伪球面上的罗氏几何测地线。

---

## 五、迁移给其他 AI 协作的提示要点

若将本项目迁移给新的 AI 工具或新会话继续维护，可直接告知以下信息：
1. 主入口为 `main.tex`，样式集中在 `preamble.tex`，正文按节拆分为 `sections/sec_001.tex` ～ `sec_100.tex`，互不耦合，可按节精准局部修改。
2. 每次修改任意 `.tex` 文件后，必须运行 **两遍 `xelatex`** 并执行 `python scripts/audit_build.py` 与 `python scripts/verify_sec017_and_redlines.py`，确保满足：
   - `Errors: 0`、`Missing chars: 0`、`Overfull \hbox (>= 1.5pt): 0`、`Undefined refs: 0`
   - `Blank Pages: 0`、`Footer Collisions: 0`
3. 新生成的对比渲染或缓存目录（`_audit_renders/`、`_compare_cards/`、`_ref_pages/`）及 `.aux/.log/.out/.toc` 在交付前均可安全清理。
