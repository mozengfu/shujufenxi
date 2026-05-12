# 电子表格数据分析系统

桌面应用，用于导入 Excel/CSV 表格，进行描述性统计、数据质量检测、对比分析、多表合并、数据清洗、列计算，输出 Excel 报表和 Word 报告。

## 技术栈

PyQt5 · pandas · openpyxl · python-docx · matplotlib

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 打包

### macOS

```bash
pyinstaller 数据分析系统.spec
# 输出：dist/数据分析系统.app
```

### Windows (ONEDIR)

```bash
pyinstaller 数据分析系统-win.spec
# 输出：dist/数据分析系统/
```

### Windows 自动构建（含 Inno Setup 安装包）

```bash
python build_windows.py
```

### GitHub Actions

推送 `v*` 标签自动构建 Windows 安装包并创建 Release。

## 目录结构

```
├── main.py                   # 入口
├── core/                     # 纯逻辑层（无 GUI 依赖）
│   ├── analyzer.py           # 统计 / 质量检测 / 分组聚合 / 对比
│   ├── cleaner.py            # 数据清洗
│   ├── exporter.py           # Excel 导出
│   ├── importer.py           # xlsx/xls/csv 导入
│   ├── merger.py             # 多表合并
│   ├── reporter.py           # Word 报告生成
│   └── report_builder.py     # 报表配置与生成引擎
└── ui/                       # PyQt5 界面层
    ├── main_window.py        # 主窗口
    ├── analysis_panel.py     # 分析面板
    ├── field_selector.py     # 字段选择
    ├── import_dialog.py      # 导入对话框
    ├── clean_dialog.py       # 数据清洗对话框
    ├── merge_dialog.py       # 多表合并对话框
    ├── report_dialog.py      # Word 导出选项对话框
    ├── report_designer.py    # 自定义报表设计器
    ├── column_calc_dialog.py # 列计算
    ├── chart_widget.py       # matplotlib 嵌入
    └── help_dialog.py        # 使用指南
```

## 功能

- **导入**: 支持 xlsx / xls / csv，自动编码检测
- **描述性统计**: 计数、求和、均值、中位数、标准差、分位数等
- **数据质量检测**: 缺失值、异常值（IQR / Z-score）、重复行、格式问题
- **分组分析**: 多列分组 + 自定义聚合（含占比、累计占比、排名、百分位排名）
- **频次分析**: 单列 / 多列交叉频次统计
- **同比 / 环比分析**: 按月 / 按季聚合后与上期对比
- **多表合并**: 关键列合并 / 行追加合并
- **数据清洗**: 类型转换、列拆分、字符操作、去重、填充
- **列计算**: 表达式计算创建新列
- **导出**: 带格式的 Excel 报表 + Word 报告
- **自定义报表**: 可视化设计器，支持标题 / 统计 / 质量 / 文本 / 表格 / 图表六种区块
