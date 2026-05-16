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
│   ├── importer.py           # TableImporter - xlsx/xls/csv 导入，自动编码检测
│   ├── merger.py             # TableMerger - 关键列合并/行追加合并
│   ├── reporter.py           # WordReporter - docx 报告（表格样式/隔行变色/页眉页脚）
│   ├── report_builder.py     # ReportConfig/ReportSection 数据模型 + ReportGenerator 引擎
│   ├── complex_report.py     # 复杂报表模板系统（多层表头/计算规则/条件格式/模板库）
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
    ├── template_designer.py  # TemplateDesignerDialog - 复杂报表模板设计器
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

### 复杂报表系统
- `core/complex_report.py` — 模型与引擎分离：
  - `ComplexReportTemplate` (dataclass) — 定义多层表头(`HeaderCell`)、数据映射、计算规则(`CalculationRule`)、条件格式(`ConditionalFormat`)、合计行(`TotalRowConfig`)
  - `ComplexReportGenerator` — 接收模板 + DataFrame，执行映射/计算/重组三步生成
  - `TemplateLibrary` — 预定义模板，当前含宽带业务不可用时长报表
  - 模板可 JSON 序列化，通过 `save()`/`load()` 持久化
- `ui/template_designer.py` — 可视化设计器，支持表头结构/计算规则/合计行配置
- `core/exporter.py` 中 `export_complex_report()` — 导出含多层表头合并、条件格式（排名高亮）、合计行的 Excel

### AI 功能
- `core/ai_summarizer.py` — 调用外部 API 生成数据分析摘要
- `ui/ai_config_dialog.py` — API 配置（URL/Key/模型），QSettings 持久化
- `ui/ai_chat_dialog.py` — 多轮对话，支持对分析结果进行交互式问答

## 关键陷阱

- **列计算安全**：`column_calc_dialog.py` 使用 `eval()` 在 DataFrame 作用域执行表达式，`{column_name}` 语法替换为 `df["column_name"]`。仅限当前 DataFrame 列名引用，不适用于任意 Python 表达式。
- **聚合系统两步计算**：特殊聚合（占比/累计占比/排名/百分位排名）在 `aggregate_with_custom_funcs` 第二步计算，依赖第一步常规聚合结果。修改聚合逻辑时需注意两步依赖关系。
- **复杂报表公式计算**：`complex_report.py` 中 `_calc_formula` 同样使用 `eval()`，公式中 `{field_name}` 语法引用已在映射中的字段。注意表达式中的字段名依赖 `data_mapping` 的输出列名，非原始数据列名。

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
