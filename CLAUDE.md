# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
桌面应用，用于导入 Excel/CSV 表格，进行描述性统计、数据质量检测、对比分析、多表合并、数据清洗、列计算，输出 Excel 报表和 Word 报告。

技术栈：PyQt5 + pandas + openpyxl + python-docx + matplotlib

## 常用命令
```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python main.py

# 语法检查
ruff check .

# PyInstaller 打包 (macOS)
pyinstaller 数据分析系统.spec

# PyInstaller 打包 (Windows ONEDIR)
pyinstaller 数据分析系统-win.spec

# 本地 Windows 打包（自动安装依赖 + Inno Setup 安装包）
python build_windows.py
```

**CI/CD**: 推送 `v*` 标签自动构建 Windows 安装包并创建 Release（`.github/workflows/build-windows.yml`）。产物：Inno Setup 安装包 + ZIP 备份。

## 目录结构
```
├── main.py                   # 入口，QApplication + MainWindow + 全局 QSS 样式
├── requirements.txt          # Python 依赖
├── MEMORY.md                 # 项目轻量级记忆文件
├── WINDOWS_BUILD.md          # Windows 打包与部署指南
├── setup.iss                 # Inno Setup 安装包脚本
├── icon.icns                 # macOS 应用图标
├── _build_icon.py            # .png → .ico 图标生成脚本
├── build_windows.py / .spec  # Windows PyInstaller 构建
├── build.bat                 # Windows 批处理构建脚本
├── 数据分析系统.spec          # PyInstaller macOS 打包配置
├── 数据分析系统-win.spec     # PyInstaller Windows ONEDIR 打包配置
├── core/                     # 纯逻辑层，无 GUI 依赖
│   ├── analyzer.py           # DataAnalyzer - 统计/质量/分组聚合/对比/时间序列
│   ├── cleaner.py            # DataCleaner - 类型转换/列拆分/去重/填充
│   ├── exporter.py           # ExcelExporter - 带格式导出（边框/数字格式/冻结/打印设置/自适应行列）
│   ├── importer.py           # TableImporter - xlsx/xls/csv 导入，自动编码检测
│   ├── merger.py             # TableMerger - 关键列合并/行追加合并
│   ├── reporter.py           # WordReporter - docx 报告（表格样式/隔行变色/页眉页脚）
│   ├── report_builder.py     # ReportConfig/ReportSection 数据模型 + ReportGenerator 引擎
│   └── ai_summarizer.py      # AISummarizer - AI 摘要生成（外部 API 调用）
└── ui/                       # PyQt5 界面层
    ├── main_window.py        # MainWindow - 主窗口，持有所有 core 模块实例
    ├── analysis_panel.py     # AnalysisPanel - 核心分析面板（5 标签页）
    ├── field_selector.py     # FieldSelector - 字段选择组件
    ├── import_dialog.py      # ImportDialog - 导入对话框
    ├── clean_dialog.py       # CleanDialog - 数据清洗对话框（QStackedWidget 多页面）
    ├── merge_dialog.py       # MergeDialog - 多表合并对话框
    ├── report_dialog.py      # ReportDialog - Word 导出选项对话框
    ├── report_designer.py    # ReportDesigner - 自定义报表设计器（6 种区块）
    ├── column_calc_dialog.py # ColumnCalcDialog - 表达式列计算
    ├── chart_widget.py       # ChartWidget - matplotlib 嵌入（直方图/箱线图/柱状图/分组图）
    ├── ai_config_dialog.py   # AIConfigDialog - AI API 配置
    ├── ai_chat_dialog.py     # AIChatDialog - AI 多轮对话
    └── help_dialog.py        # HelpDialog - 使用指南
```

## 架构要点

### 模块职责
- **core/** — 无 Qt 依赖，可独立测试
- **ui/** — 只做界面编排，业务逻辑委托给 core/
- **MainWindow** — 持有 importer/analyzer/merger/exporter/reporter 实例，作为全局共享入口
- **AnalysisPanel** — 5 个结果标签页：数据预览 / 统计结果 / 质量报告 / 分组对比 / 频次分析

### 数据流
```
导入 → TableImporter → pd.DataFrame → AnalysisPanel 展示
                                                  ↓
                                          DataAnalyzer 分析
                                                  ↓
                                      DataCleaner 清洗（可选）
                                                  ↓
                                ExcelExporter / WordReporter 导出
                                                  ↓
                                     AISummarizer 生成摘要（可选）
```

### 状态持久化
QSettings (`organization='shujufenxi'`, `app='data-analyzer'`) 存储：
- 窗口几何状态（`window_geometry` / `window_state`）
- 最近文件列表（`recent_files`，最多 10 条）
- 自定义报表模板
- AI API 配置

### 全局样式
`main.py` 中定义全局 QSS 样式表，统一控制 QGroupBox/QPushButton/QComboBox/QTableWidget/QTabWidget/QMenuBar 等组件的外观。使用 Fusion 风格 (`app.setStyle('fusion')`)。Qt 内置对话框中文翻译通过 `QTranslator` 加载。

### 聚合系统
`core/analyzer.py`:
- `AGG_FUNCTIONS` — 14 种聚合函数（计数/去重计数/求和/均值/中位数/最大/最小/标准差/第一值/最后值/占比/累计占比/排名/百分位排名/行数）
- `NUMERIC_AGGS` — 仅适用于数值列的聚合子集
- 特殊聚合（占比/累计占比/排名/百分位排名）在 `aggregate_with_custom_funcs` 第二步计算，依赖第一步常规聚合结果
- 多条件聚合通过 `multi_conditional_aggregate` 实现，支持按列总和或按组内行数两种占比模式
- 合计行通过 `make_total_row()` 生成，占比列特殊处理

### 时间序列分析
`yoy_analysis`（同比）和 `mom_analysis`（环比）支持按月/季度聚合后与上期对比，返回增减额和增幅百分比。

### 报表系统
- `core/report_builder.py` — JSON 可序列化的 ReportConfig/ReportSection 模型 + ReportGenerator 引擎
- `core/exporter.py` — Excel 导出：边框、数字格式（千分位/百分比）、冻结首行、自动筛选、打印设置、行列自适应
- `core/reporter.py` — Word 报告：表头蓝底白字、隔行变色、页眉页脚页码
- `ui/report_designer.py` — 可视化设计器，支持标题/统计/质量/文本/表格/图表六种区块，模板通过 QSettings 持久化

### 图表系统
`ui/chart_widget.py` — matplotlib QtAgg 后端嵌入 PyQt，自动检测系统中文字体。图表导出到 Word 使用临时 PNG 文件。

### 列计算
`ui/column_calc_dialog.py` — Python `eval` 在 DataFrame 作用域内计算，`{column_name}` 语法引用已有列。

### AI 功能
- `core/ai_summarizer.py` — 调用外部 API 生成数据分析摘要
- `ui/ai_config_dialog.py` — API 配置（URL/Key/模型），QSettings 持久化
- `ui/ai_chat_dialog.py` — 多轮对话，支持对分析结果进行交互式问答

### 拖放支持
MainWindow、AnalysisPanel、FieldSelector 均实现 `dragEnterEvent`/`dropEvent` 支持 `.xlsx`/`.xls`/`.csv` 文件拖放导入。

## 调试
- **崩溃日志**：打包后查看桌面 `数据分析系统_crash.log`（main.py 自动写入 Python traceback + 环境信息）
- **Qt 插件路径**：`QT_QPA_PLATFORM_PLUGIN_PATH` 在 main.py 中自动探测
- **Windows DLL 加载失败**：缺 MSVC 运行库。解决：安装 [vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe)，详见 `WINDOWS_BUILD.md`
- **双击无反应**：临时加 `--console` 参数查看错误

## 打包
| 平台 | 命令 | 产物 |
|------|------|------|
| macOS | `pyinstaller 数据分析系统.spec` | `dist/数据分析系统.app` |
| Windows ONEDIR | `pyinstaller 数据分析系统-win.spec` | `dist/数据分析系统/` |
| Windows CI | 推送 `v*` 标签触发 | Inno Setup 安装包 + ZIP |

**关键配置**：排除 PyQt6/PySide6，禁用 console，打包 Qt plugins 目录，CI 自动捆绑 MSVC 运行库 DLL。`build_windows.spec` 将 `CLAUDE.md` 打包进应用。

## 测试
**项目无自动化测试。** core/ 模块无 Qt 依赖，理论上可独立测试。验证主要依靠 `ruff check .` 和手动运行应用。

---

## 修改记录

### 2026-05-13 报表格式优化

#### 问题
导出的 Excel 表格没有自适应行高和列宽，且缺少标准报表格式（边框、数字格式、打印设置等）。

#### 修改内容

**1. core/exporter.py - Excel 导出增强**

新增功能：
- **边框线**：表头白色边框，数据行黑色细边框
- **数字格式**：普通数值千分位格式 `#,##0.00`，百分比自动识别为 `0.00%`
- **冻结首行 + 自动筛选**：首行冻结，自动添加筛选器下拉箭头
- **打印区域和页面设置**：
  - 列数 > 6 时自动切换横向
  - A4 纸张，自适应宽度（1页宽）
  - 打印标题行重复
  - 页边距设置（左右 0.5，上下 0.75）
- **行高列宽自适应**：
  - 中文按 2 字符宽度计算（使用 `unicodedata.east_asian_width`）
  - 自动换行，最小行高 15，最大行高 60
  - 采样前 100 行避免大数据量过慢

新增方法：
- `_apply_table_format()` - 应用表格格式（边框、样式、数字格式）
- `_freeze_header_and_filter()` - 冻结首行并添加自动筛选
- `_setup_print_settings()` - 设置打印区域和页面设置
- `_get_text_width()` - 计算文本宽度（中文按 2 字符）
- `_adjust_column_widths()` - DataFrame 列宽自适应
- `_adjust_row_heights()` - DataFrame 行高自适应
- `_adjust_column_widths_for_worksheet()` - Worksheet 列宽自适应
- `_adjust_row_heights_for_worksheet()` - Worksheet 行高自适应
- `_apply_format_to_worksheet()` - 为 Worksheet 应用格式

所有导出方法更新：
- `export_with_format()` - 主导出方法
- `export_stats_report()` - 统计报告
- `export_quality_report()` - 数据质量报告
- `export_comparison()` - 对比分析报告

**2. core/reporter.py - Word 报告增强**

新增功能：
- **表格样式美化**：
  - 表头：蓝色背景 `#366092` + 白色字体 + 粗体 + 居中
  - 隔行变色：浅灰 `#F2F2F2` / 白色 `#FFFFFF` 交替
  - 黑色边框
  - 数字右对齐，其他居中
  - 统一字体大小 10pt
- **页眉页脚**：
  - 页眉：报告标题（居中，灰色，9pt）
  - 页脚：页码 / 总页数（居中，灰色，9pt）

新增方法：
- `_set_cell_shading()` - 设置单元格背景色
- `_set_cell_border()` - 设置单元格边框
- `_set_cell_font()` - 设置单元格字体
- `_add_header_footer()` - 添加页眉页脚

修改方法：
- `create_document()` - 支持添加页眉页脚参数
- `add_table_from_df()` - 增强表格样式（边框、隔行变色、对齐）

#### 技术细节
- 使用 `openpyxl.styles.Border` 和 `Side` 实现边框
- 使用 `openpyxl.worksheet.page.PageMargins` 设置页边距
- 使用 `docx.oxml` 操作 Word XML 实现背景色和页码
- 使用 `unicodedata.east_asian_width` 识别中文字符宽度

#### 验证
- 语法检查通过：`python3 -m py_compile core/exporter.py`
- 语法检查通过：`python3 -m py_compile core/reporter.py`

---

### 2026-05-13 复杂报表模板系统

#### 功能概述
新增复杂报表模板系统，支持多层表头、数据映射、计算规则、条件格式，可生成类似宽带业务不可用时长统计报表的复杂格式。

#### 新增文件

**1. core/complex_report.py - 复杂报表核心模块**

数据类定义：
- `HeaderCell` - 表头单元格（名称、跨行列数、父级、数据字段、对齐）
- `CalculationRule` - 计算规则（排名、公式、求和、平均）
- `ConditionalFormat` - 条件格式（排名前三高亮等）
- `TotalRowConfig` - 合计行配置
- `ComplexReportTemplate` - 复杂报表模板（完整配置）

核心类：
- `ComplexReportGenerator` - 报表生成引擎
  - `generate()` - 根据模板生成报表数据
  - `_apply_data_mapping()` - 应用数据映射
  - `_apply_calculations()` - 执行计算规则
  - `_calc_rank()` - 计算排名
  - `_calc_formula()` - 计算公式
  - `_restructure_data()` - 重组数据结构
  - `get_header_structure()` - 获取表头结构
  - `calculate_total_row()` - 计算合计行

- `TemplateLibrary` - 预定义模板库
  - `create_broadband_outage_template()` - 宽带业务不可用时长报表模板

**2. core/exporter.py - 新增复杂报表导出方法**

新增方法：
- `export_complex_report()` - 导出复杂报表
  - 支持多层表头
  - 支持合并单元格
  - 支持条件格式（排名高亮）
  - 支持合计行
  - 完整打印设置
- `_write_multi_headers()` - 写入并合并多层表头
- `_apply_complex_data_format()` - 应用复杂数据格式
- `_apply_conditional_format()` - 应用条件格式
- `_adjust_complex_column_widths()` - 调整复杂报表列宽
- `_adjust_complex_row_heights()` - 调整复杂报表行高

**3. ui/template_designer.py - 模板设计器界面**

界面组件：
- `HeaderDesignerWidget` - 表头设计器
  - 可视化配置多层表头
  - 支持跨行跨列设置
  - 支持父级关系配置
- `CalculationRuleWidget` - 计算规则配置
  - 排名、公式、求和、平均
- `TemplateDesignerDialog` - 模板设计器对话框
  - 模板基本信息配置
  - 表头设计
  - 计算规则配置
  - 合计行配置
  - 保存/加载模板

#### 使用方式

**1. 使用预定义模板**
```python
from core import TemplateLibrary, ComplexReportGenerator, ExcelExporter

# 获取预定义模板
template = TemplateLibrary.create_broadband_outage_template()

# 生成报表数据
generator = ComplexReportGenerator(template)
report_df = generator.generate(raw_df)

# 导出复杂报表
exporter = ExcelExporter()
exporter.export_complex_report(raw_df, template, 'output.xlsx')
```

**2. 自定义模板**
```python
from core import ComplexReportTemplate, HeaderCell, CalculationRule

# 创建模板
template = ComplexReportTemplate(
    name='custom_report',
    title='自定义报表',
    headers=[
        [HeaderCell(name='单位', rowspan=2, data_field='unit')],
        [HeaderCell(name='数值', parent='单位', data_field='value')]
    ],
    calculations=[
        CalculationRule(name='排名', calc_type='rank', params={'by': 'value'})
    ]
)

# 保存模板
template.save('custom_template.json')
```

**3. 使用模板设计器**
```python
from ui import show_template_designer

# 打开设计器对话框
template = show_template_designer(parent_window)
```

#### 模板配置说明

**表头结构**：
- 支持多层嵌套（2层及以上）
- 支持跨行(rowspan)和跨列(colspan)
- 支持父级关系（子表头归属）

**数据映射**：
- 模板字段名 → 原始数据列名
- 支持计算字段（calculated:xxx）

**计算规则**：
- `rank` - 排名（支持升序/降序）
- `formula` - 公式计算（支持DataFrame表达式）
- `sum` - 多列求和
- `avg` - 多列平均

**条件格式**：
- 支持按值匹配
- 支持背景色、字体颜色设置
- 典型应用：排名前三高亮

**合计行**：
- 支持按列配置聚合方式
- 支持 sum/avg/count/-（不计算）

#### 技术特点

1. **模板可序列化** - JSON格式保存，可复用
2. **数据与表现分离** - 模板定义结构，数据动态填充
3. **计算规则可扩展** - 支持自定义计算类型
4. **可视化设计** - 无需编码，界面配置

#### 验证
- 语法检查通过：`python3 -m py_compile core/complex_report.py`
- 语法检查通过：`python3 -m py_compile ui/template_designer.py`
