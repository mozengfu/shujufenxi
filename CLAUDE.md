# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
桌面应用，用于导入 Excel/CSV 表格，进行描述性统计、数据质量检测、对比分析、多表合并、数据清洗，输出 Excel 报表和 Word 报告。

技术栈：PyQt6 + pandas + openpyxl + python-docx

## 常用命令
```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python main.py

# 语法检查
ruff check .

# PyInstaller 打包
pyinstaller 数据分析系统.spec
```

## 目录结构
```
shujufenxi/
├── main.py                   # 入口，初始化 QApplication + MainWindow
├── 数据分析系统.spec          # PyInstaller 打包配置
├── core/                     # 纯逻辑层，无 GUI 依赖
│   ├── analyzer.py           # DataAnalyzer - 统计/质量检测/分组聚合/对比
│   ├── cleaner.py            # DataCleaner - 类型转换/列拆分/字符操作/去重/填充
│   ├── exporter.py           # ExcelExporter - 带格式导出/统计/质量/对比报告
│   ├── importer.py           # TableImporter - xlsx/xls/csv 导入，自动编码
│   ├── merger.py             # TableMerger - 关键列合并/行追加合并
│   └── reporter.py           # WordReporter - docx 报告生成
└── ui/                       # PyQt6 界面层
    ├── main_window.py        # MainWindow - 主窗口，协调所有模块
    ├── analysis_panel.py     # AnalysisPanel - 核心分析面板，聚合配置/结果展示
    ├── field_selector.py     # FieldSelector - 字段选择组件（复选框+类型标签+缺失提示）
    ├── import_dialog.py      # ImportDialog - 导入对话框
    ├── clean_dialog.py       # CleanDialog - 数据清洗对话框，QStackedWidget 多页面
    ├── merge_dialog.py       # MergeDialog - 多表合并对话框
    ├── report_dialog.py      # ReportDialog - Word 导出选项对话框
    └── help_dialog.py        # HelpDialog - 使用指南
```

## 架构要点

### 模块职责
- **core/** 所有类均无 Qt 依赖，可独立测试
- **ui/** 只做界面编排，业务逻辑委托给 core/
- **MainWindow** 持有 core 模块的实例（importer, analyzer, merger, exporter, reporter），作为全局共享入口
- **AnalysisPanel** 是核心工作区，包含 5 个结果标签页：数据预览 / 统计结果 / 质量报告 / 分组对比 / 频次分析

### 数据流
```
导入文件 → TableImporter → pd.DataFrame → AnalysisPanel 展示
                                                  ↓
                                          DataAnalyzer 分析
                                                  ↓
                                ExcelExporter / WordReporter 导出
```

### 聚合系统
`AGG_FUNCTIONS` 字典定义支持的聚合函数（计数、去重计数、求和、平均值、中位数、最大值、最小值、标准差、第一值、最后值、占比、累计占比、排名、百分位排名）。
其中占比/累计占比/排名/百分位排名作为"特殊聚合"在 aggregate_with_custom_funcs 中第二步计算，依赖第一步的常规聚合结果。
NUMERIC_AGGS 列出仅适用于数值列的聚合。

### 拖放支持
MainWindow、AnalysisPanel、FieldSelector 均实现 dragEnterEvent/dropEvent 支持文件拖放导入。

### 打包
- 使用 PyInstaller spec 打包为 .app
- 关键配置：排除 PyQt5/PySide6，禁用 console，打包 Qt plugins 目录
- 打包命令：`pyinstaller 数据分析系统.spec`
