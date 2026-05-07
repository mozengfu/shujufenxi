# 项目状态

## 当前阶段
全部 7 个 Phase 已完成，所有代码通过 ruff 检查和模块编译

## 已完成
- [x] Bug 修复和 lint 清理（7 个 Bug + 22 个 lint 问题）
- [x] CLAUDE.md 更新
- [x] GSD 项目初始化
- [x] Phase 1: 基础设施（matplotlib + QSettings）
- [x] Phase 2: 最近文件 + 窗口恢复
- [x] Phase 3: 数据筛选和排序
- [x] Phase 4: 列计算/衍生字段
- [x] Phase 5: 数据可视化图表
- [x] Phase 6: 合并增强（列结构对比）
- [x] Phase 7: 自定义报表生成

## 文件变更

### 修改文件
| 文件 | 变更 |
|------|------|
| requirements.txt | 添加 matplotlib>=3.8.0 |
| ui/main_window.py | QSettings + 最近文件 + 列计算入口 + 自定义报表入口 + 图表嵌入 Word |

### 新增文件
| 文件 | 说明 |
|------|------|
| ui/chart_widget.py | matplotlib 图表组件（直方图/箱线图/柱状图/分组图） |
| ui/column_calc_dialog.py | 列计算对话框（表达式引擎） |
| core/report_builder.py | 报表配置数据模型 + 生成引擎 |
| ui/report_designer.py | 自定义报表设计器 UI |

## 决策记录
- matplotlib 使用 QtAgg 后端嵌入 PyQt6，中文字体自动检测
- QSettings organization='shujufenxi', app='data-analyzer'
- 自定义报表使用 JSON 序列化模板，保存在 QSettings
- 列计算使用 Python eval (在 df 作用域内安全执行)
- 图表导出到 Word 使用临时 PNG 文件
