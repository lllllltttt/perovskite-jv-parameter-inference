# 导师审阅稿 — 五张主图定稿 + 正文装配 + SI 同步（v2 + 排版局部修补）

日期：2026-10-07（排版修补）· 交付根目录：`E:\project\work1\20261006\manuscript_figures_SI_integrated_v2_layout_final\`
来源：v2 交付 `E:\project\work1\20261006\manuscript_figures_SI_integrated_v2\`（**未覆盖**，只读）

> **本目录 = v2 全部内容 + 三处排版修补**。改动只有：正文 p8 的 `cm⁻²` 断行、
> SI 表 T6.8b 的行跨页拆开、SI 表 T6.9 的孤立表头。科学内容、数据、图片、统计方法、
> 参考文献一律未动，页数仍是正文 18 页 / SI 50 页，正文只有 p8、SI 只有 p14–p15
> 的文字发生变化。逐条证据见 **`LAYOUT_PATCH_NOTES.md`**，验收日志见
> `report\LAYOUT_PATCH_QA.log`，三处修复位置的最终 PDF 渲染截图见 `render_checks\`。
> 下文（v2 那轮的说明）保持原样，仍然适用。

> **v2 是本轮修补的结果**：在两处图注事实、Figure 3 图内文字与选例规则、SI 中两个新
> 案例的数值依据、配对坐标分档表、两段 7 pt 正文与 Table S5 表头上做了定向修补。
> 逐条对应见 **`PATCH_NOTES.md`**。数值、数据、配对规则、随机基线、案例选择与统计
> 定义均未改动。

## 先看这几个文件

| 想了解 | 打开 |
|---|---|
| 本轮逐条改了什么、为什么 | **`PATCH_NOTES.md`** |
| 装配后的正文（18 页，5 张主图） | `manuscript\Manuscript_20261002_Working_integrated.pdf` |
| 同步后的 SI（50 页，含新增 Figure S6 / S7 与 T6.7–T6.9） | `si\Supplementary_Information_synced.pdf` |
| v1 那轮改了什么、为什么 | `report\CHANGELOG.md` |
| 数值判定、缺陷与假警报、仍需作者决定的事项 | `report\QA.md` |
| 每一条图表交叉引用指向哪里 | `report\cross_reference_map.csv` |

Word 源文件在同名的 `.docx`。请用 PDF 阅读，用 DOCX 继续编辑。

## 目录

```
manuscript\   正文 DOCX + PDF + 修改日志（14 处：5 处插图 + 7 处文字 + 2 处字号修复）
si\           配套 SI DOCX + PDF + 修改日志（169 处）
figures\      五张主图 + 新增 SI 图 S6/S7，每张 6 件套（png / 大图 png / pdf / 大图 pdf / svg / 大图 svg）
data_used\    绘图与新增 SI 表实际用到的轻量数据（37 个文件，36 MB）
scripts\      可复现脚本（含 render.ps1、restore_hd.py 与四个验收脚本）
qa\           逐页渲染（pages\ 全尺寸，pages_small\ 缩略）与裁图
qa_render\    单图预览与局部放大
report\       CHANGELOG.md、QA.md、cross_reference_map.csv
```

## 关键校验结果

- 交叉引用 **127 条（正文 57 / SI 70），0 条未解析**；图表指针已按**内容**核对
  （不是只检查编号存在）。
- `verify_si.py` **115 项全部 PASS**（含 T6.7–T6.9 逐格对回 `data_used\` 的冻结 CSV、
  图注 → Methods 选例规则的跨文档内容核对）。
- `figure_font_audit.py`、`svg_pdf_audit.py`、`qa_layout.py` 全部 PASS。
- 图内最小字号不低于 17.27 cm 显示宽度下的 6 pt 底线。
- 两份 PDF 中嵌入的位图与 `figures\` 里的原图**逐像素相同**（Word 导出会把位图压到 200 ppi，交付前已用 `restore_hd.py` 原位换回高清流，版面与文字不变）。

## 复现

解释器 `D:\PythonProject\.venv\Scripts\python.exe`，环境变量 `PYTHONIOENCODING=utf-8`。

```
python scripts\build_all_figures.py
python scripts\build_manuscript.py
python scripts\build_si.py
powershell -File scripts\render.ps1
python scripts\restore_hd.py manuscript\Manuscript_20261002_Working_integrated.docx
python scripts\restore_hd.py si\Supplementary_Information_synced.docx
python scripts\verify_si.py
python scripts\figure_font_audit.py
python scripts\svg_pdf_audit.py
python scripts\qa_layout.py
python scripts\cross_reference_map.py
```

`restore_hd.py` 必须在**每次**重新导出 PDF 之后再跑一次：Word 每次导出都会重新压图。

## 输入（只读，本轮未改动）

| 用途 | 路径 | sha256 前 16 位 |
|---|---|---|
| 导师正文底稿 | `E:\project\work1\20261006\Manuscript_20261002_Working.docx` | `ca7aed66ca0535fe` |
| SI 底稿 | `E:\project\work1\20260929_si_provenance_wording\Supplementary_Information_provenance_wording_20260929.docx` | `4a16fcd06f62e7a1` |
| 冻结模型预测 | `E:\project\work1\final_figures\scripts\_frozen_preds.npz` | `ad156cd18c1933e8` |
| 冻结 J scaler | `E:\project\work1\data\J_scaler.pkl` | `3b82a2541bd77c59` |

本轮**没有**重训模型、没有重新预测、没有重拟合 scaler、没有启动 COMSOL；没有改动原始数据、冻结模型、数据划分、既定算例与统计定义；没有恢复 S19；没有编造数据共享地址、软件版本或服务器记录；没有覆盖任何输入文件。

## 仍需作者决定

见 `QA.md` 第 7 节：正文 p8 那段 7 pt 小字段落、pp. 4/6/8/10 因"图+图注不可分割"留出的下半页空白、SI 表 S5 表头折行成 "Recoverabilit / y"。三项都是底稿自带、本轮刻意未动。
