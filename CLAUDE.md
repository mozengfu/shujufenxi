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

# 本地 Windows 打包（自动安装依赖）
python build_windows.py

# GitHub Actions 触发方式
# - 手动 dispatch
# - 推送 v* 标签（自动构建 Windows 安装包并创建 Release）
# CI 产物：Inno Setup 安装包 (shujufenxi-setup.exe) + ZIP 备份
```

## 调试
- **崩溃日志**：打包后双击无响应时，查看桌面 `数据分析系统_crash.log`（main.py 自动写入 Python traceback + 环境信息）
- **Qt 插件路径**：`QT_QPA_PLATFORM_PLUGIN_PATH` 环境变量在 main.py 中自动探测，无需手动设置
- **Windows DLL 加载失败**：若提示 `DLL load failed while importing QtWidgets`，原因是缺 MSVC 运行库或 `qwindows.dll` 缺失。解决：安装 [vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe)，或打包时在 spec 中加 `--win-private-assemblies`。详见 `WINDOWS_BUILD.md`。

## 项目规划
`.planning/` 目录存放项目规划文档：
- `config.json` — 工作流配置（原子提交、ruff 验证、顺序执行）
- `PROJECT.md` — 项目概述
- `ROADMAP.md` — 功能路线图
- `STATE.md` — 当前开发状态

## 目录结构
```
shujufenxi/
├── main.py                   # 入口，QApplication + MainWindow + 全局样式
├── requirements.txt          # Python 依赖
├── 数据分析系统.spec          # PyInstaller 打包配置 (macOS)
├── 数据分析系统-win.spec     # PyInstaller 打包配置 (Windows ONEDIR)
├── build_windows.spec        # PyInstaller 打包配置 (Windows 单 EXE)
├── build_windows.py          # Windows PyInstaller 构建脚本
├── build.bat                 # Windows 批处理构建脚本
├── setup.iss                 # Inno Setup 安装包脚本
├── icon.icns                 # macOS 应用图标
├── core/                     # 纯逻辑层，无 GUI 依赖
│   ├── analyzer.py           # DataAnalyzer - 统计/质量检测/分组聚合/对比
│   ├── cleaner.py            # DataCleaner - 类型转换/列拆分/字符操作/去重/填充
│   ├── exporter.py           # ExcelExporter - 带格式导出/统计/质量/对比报告
│   ├── importer.py           # TableImporter - xlsx/xls/csv 导入，自动编码
│   ├── merger.py             # TableMerger - 关键列合并/行追加合并
│   ├── reporter.py           # WordReporter - docx 报告生成
│   ├── report_builder.py     # ReportConfig/ReportSection 数据模型 + ReportGenerator 引擎
│   └── ai_summarizer.py      # AISummarizer - AI 摘要生成（调用外部 API）
└── ui/                       # PyQt5 界面层
    ├── main_window.py        # MainWindow - 主窗口，协调所有模块
    ├── analysis_panel.py     # AnalysisPanel - 核心分析面板，聚合配置/结果展示
    ├── field_selector.py     # FieldSelector - 字段选择组件（复选框+类型标签+缺失提示）
    ├── import_dialog.py      # ImportDialog - 导入对话框
    ├── clean_dialog.py       # CleanDialog - 数据清洗对话框，QStackedWidget 多页面
    ├── merge_dialog.py       # MergeDialog - 多表合并对话框
    ├── report_dialog.py      # ReportDialog - Word 导出选项对话框
    ├── report_designer.py    # ReportDesigner - 自定义报表设计器（支持标题/统计/质量/文本/表格/图表区块）
    ├── column_calc_dialog.py # ColumnCalcDialog - 表达式列计算（Python eval in DataFrame scope）
    ├── chart_widget.py       # ChartWidget - matplotlib 嵌入 PyQt（直方图/箱线图/柱状图/分组图）
    ├── ai_config_dialog.py   # AIConfigDialog - AI 摘要 API 配置对话框
    └── help_dialog.py        # HelpDialog - 使用指南
```

## 架构要点

### 模块职责
- **core/** 所有类均无 Qt 依赖，可独立测试
- **ui/** 只做界面编排，业务逻辑委托给 core/
- **MainWindow** 持有 core 模块的实例（importer, analyzer, merger, exporter, reporter, ai_summarizer），作为全局共享入口
- **AnalysisPanel** 是核心工作区，包含 5 个结果标签页：数据预览 / 统计结果 / 质量报告 / 分组对比 / 频次分析

### 数据流
```
导入文件 → TableImporter → pd.DataFrame → AnalysisPanel 展示
                                                  ↓
                                          DataAnalyzer 分析
                                                  ↓
                                      DataCleaner 清洗（可选）
                                                  ↓
                                ExcelExporter / WordReporter 导出
                                                  ↓
                                     AISummarizer 生成摘要（可选）
```

### 时间序列分析
`core/analyzer.py` 中的 `yoy_analysis`（同比）和 `mom_analysis`（环比）方法支持按月/季度聚合后与上期对比，返回增减额和增幅百分比。

### 聚合系统
`AGG_FUNCTIONS` 字典定义支持的聚合函数（计数、去重计数、求和、平均值、中位数、最大值、最小值、标准差、第一值、最后值、占比、累计占比、排名、百分位排名）。
其中占比/累计占比/排名/百分位排名作为"特殊聚合"在 `aggregate_with_custom_funcs` 中第二步计算，依赖第一步的常规聚合结果。
`NUMERIC_AGGS` 列出仅适用于数值列的聚合。

### 报表系统
`core/report_builder.py` 提供 JSON 可序列化的 ReportConfig/ReportSection 数据模型和 ReportGenerator 引擎，协调 WordReporter + ExcelExporter + DataAnalyzer 完成报表生成。
`ui/report_designer.py` 提供可视化报表设计器，支持标题、统计、质量、文本、数据表、图表六种区块，模板通过 QSettings 持久化。

### 图表系统
`ui/chart_widget.py` 使用 matplotlib QtAgg 后端嵌入 PyQt，支持直方图、箱线图、柱状图、分组图。自动检测系统中文字体。

### 列计算
`ui/column_calc_dialog.py` 提供表达式列计算功能，使用 Python eval 在 DataFrame 作用域内计算，语法为 `{column_name}` 引用已有列。

### AI 摘要
`core/ai_summarizer.py` 提供 AISummarizer 类，调用外部 API 生成数据分析摘要。`ui/ai_config_dialog.py` 提供 API 配置界面（URL、Key、模型等），配置通过 QSettings 持久化。

### 拖放支持
MainWindow、AnalysisPanel、FieldSelector 均实现 dragEnterEvent/dropEvent 支持文件拖放导入。

### 打包
- macOS: `pyinstaller 数据分析系统.spec` → 生成 `.app`
- Windows ONEDIR: `pyinstaller 数据分析系统-win.spec` → 生成 `dist/数据分析系统/` 目录
- Windows 单 EXE: `pyinstaller build_windows.spec` → 生成 `dist/数据分析系统.exe`
- CI/CD: `.github/workflows/build-windows.yml` 推送 `v*` 标签自动构建 Windows 安装包并创建 Release
- 关键配置：排除 PyQt6/PySide6，禁用 console，打包 Qt plugins 目录
- `build_windows.spec` 将 `CLAUDE.md` 打包进应用（供打包后的 AI 参考）

### 测试
**项目无自动化测试。** 所有 core/ 模块理论上可独立测试（无 Qt 依赖），但目前没有 test 目录或测试配置。验证主要依靠 `ruff check .` 和手动运行应用。
