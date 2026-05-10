# MEMORY.md

项目记忆 — 数据分析系统

---

## 架构

- main.py: 入口，初始化 QApplication + MainWindow
- core/: 纯逻辑层，无 GUI 依赖
  - analyzer.py: DataAnalyzer — 统计/质量检测/分组聚合/对比
  - cleaner.py: DataCleaner — 类型转换/列拆分/字符操作/去重/填充
  - exporter.py: ExcelExporter — 带格式导出
  - importer.py: TableImporter — xlsx/xls/csv 导入，自动编码
  - merger.py: TableMerger — 关键列合并/行追加
  - reporter.py: WordReporter — docx 报告生成
- ui/: PyQt6 界面层，只做编排不处理业务逻辑
  - main_window.py, analysis_panel.py, field_selector.py, import_dialog.py, clean_dialog.py, merge_dialog.py, report_dialog.py, help_dialog.py
- 数据分析系统.spec: PyInstaller 打包配置

## 数据流

```
导入 → TableImporter → pd.DataFrame → AnalysisPanel 展示
                                          ↓
                                  DataAnalyzer 分析
                                          ↓
                          ExcelExporter / WordReporter 导出
```

## 聚合系统

AGG_FUNCTIONS: 计数/去重计数/求和/均值/中位数/最大/最小/标准差/第一值/最后值/占比/累计占比/排名/百分位排名
NUMERIC_AGGS: 仅适用于数值列的聚合子集
特殊聚合(占比/累计占比/排名/百分位排名)在 aggregate_with_custom_funcs 第二步计算，依赖第一步常规聚合结果

## 约定

- core/ 所有类无 Qt 依赖，可独立测试
- ui/ 只做界面编排，业务委托给 core/
- MainWindow 持有所有 core 模块实例，作为全局共享入口
- AnalysisPanel 含 5 个结果标签页：预览/统计/质量/分组对比/频次
- 拖放支持: MainWindow/AnalysisPanel/FieldSelector 均实现 dragEnterEvent/dropEvent

## 打包

- PyInstaller spec 打包为 .app
- 排除 PyQt5/PySide6，禁用 console，打包 Qt plugins

## 活跃工作

- 无活跃开发任务
