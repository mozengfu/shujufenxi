"""分析面板模块"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QTableWidget, QTableWidgetItem, QLabel, QComboBox,
                              QGroupBox, QTextEdit, QTabWidget, QHeaderView,
                              QPushButton, QMessageBox, QListWidget,
                              QListWidgetItem, QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from .field_selector import FieldSelector
from .chart_widget import ChartWidget
from core import TableImporter
from core.analyzer import AGG_FUNCTIONS


def _fmt_value(value) -> str:
    """格式化显示值：数值保留两位小数，占比加 %"""
    if pd.isna(value):
        return ''
    if isinstance(value, (int, np.integer)):
        return str(value)
    if isinstance(value, (float, np.floating)):
        if value == int(value):
            return f'{value:.0f}'
        return f'{value:.2f}'
    return str(value)


def _fmt_percent(value) -> str:
    """格式化百分比"""
    if pd.isna(value):
        return ''
    try:
        return f'{float(value):.2f}%'
    except (ValueError, TypeError):
        return str(value)


class AnalysisPanel(QWidget):
    """分析面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.current_df: pd.DataFrame = None
        self.current_info: Dict[str, Any] = {}
        self.agg_items: List[Dict] = []  # 当前聚合项列表
        self.condition_items: List[Dict] = []  # 当前筛选条件列表
        self.last_result_df: pd.DataFrame = None  # 最后一次分析结果
        self.importer = TableImporter()
        self.setAcceptDrops(True)
        self.init_ui()

    @property
    def chart_figure(self):
        """获取当前图表 Figure（供 Word 导出用）"""
        return self.chart_widget.get_figure()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖动进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(('.xlsx', '.xls', '.csv')):
                files.append(file_path)

        if files:
            file_path = files[0]
            try:
                df = self.importer.import_file(file_path)
                info = self.importer.get_info()
                info['file_path'] = file_path
                self.current_df = df
                self.current_info = info
                self.update_data(df, info)
                if self.main_window:
                    self.main_window.current_df = df
                    self.main_window.statusBar().showMessage(f'已导入: {info["rows"]} 行 x {info["columns"]} 列')
                QMessageBox.information(self, '成功', f'成功导入 {info["rows"]} 行 x {info["columns"]} 列')
            except Exception as e:
                QMessageBox.critical(self, '错误', str(e))
        event.acceptProposedAction()

    def init_ui(self):
        """初始化 UI"""
        main_layout = QHBoxLayout()

        # 左侧：字段选择区
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        self.field_selector = FieldSelector()
        self.field_selector.selection_changed.connect(self.on_field_selection_changed)
        left_layout.addWidget(self.field_selector)

        # 分析类型选择
        analysis_group = QGroupBox('分析类型')
        analysis_layout = QGridLayout()

        analysis_layout.addWidget(QLabel('分析类型:'), 0, 0)
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            '描述性统计',
            '缺失值检测',
            '异常值检测',
            '格式问题检测',
            '分组分析',
            '频次分析',
            '综合分析',
            '同比分析',
            '环比分析'
        ])
        self.analysis_type_combo.currentTextChanged.connect(self.on_analysis_type_changed)
        analysis_layout.addWidget(self.analysis_type_combo, 0, 1, 1, 2)

        # 分组列选择（下拉复选框）
        analysis_layout.addWidget(QLabel('分组列:'), 1, 0)
        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(180)
        self.group_combo.view().pressed.connect(self._on_group_item_pressed)
        analysis_layout.addWidget(self.group_combo, 1, 1, 1, 2)

        # 聚合项配置区域
        agg_group = QGroupBox('聚合项配置')
        agg_layout = QVBoxLayout()

        # 值列 + 聚合函数 选择行
        agg_config_layout = QHBoxLayout()
        agg_config_layout.addWidget(QLabel('值列:'))
        self.agg_col_combo = QComboBox()
        agg_config_layout.addWidget(self.agg_col_combo)

        agg_config_layout.addWidget(QLabel('聚合:'))
        self.agg_func_combo = QComboBox()
        self.agg_func_combo.addItems(list(AGG_FUNCTIONS.keys()))
        agg_config_layout.addWidget(self.agg_func_combo)

        self.add_agg_btn = QPushButton('添加')
        self.add_agg_btn.clicked.connect(self.add_aggregation_item)
        agg_config_layout.addWidget(self.add_agg_btn)
        agg_layout.addLayout(agg_config_layout)

        # 聚合项列表
        self.agg_list_widget = QListWidget()
        self.agg_list_widget.setMinimumHeight(60)
        self.agg_list_widget.itemDoubleClicked.connect(self.on_agg_item_double_clicked)
        agg_layout.addWidget(self.agg_list_widget)

        agg_group.setLayout(agg_layout)
        analysis_layout.addWidget(agg_group, 3, 0, 1, 3)

        # 筛选条件区域
        filter_group = QGroupBox('筛选条件')
        filter_layout = QVBoxLayout()

        filter_config_layout = QHBoxLayout()
        filter_config_layout.addWidget(QLabel('列:'))
        self.filter_col_combo = QComboBox()
        filter_config_layout.addWidget(self.filter_col_combo)

        filter_config_layout.addWidget(QLabel('条件:'))
        self.filter_op_combo = QComboBox()
        self.filter_op_combo.addItems(['>', '<', '==', '!=', '>=', '<=', '包含'])
        filter_config_layout.addWidget(self.filter_op_combo)

        self.filter_value_edit = QLineEdit()
        self.filter_value_edit.setPlaceholderText('值')
        filter_config_layout.addWidget(self.filter_value_edit)

        self.add_filter_btn = QPushButton('添加')
        self.add_filter_btn.clicked.connect(self.add_filter_condition)
        filter_config_layout.addWidget(self.add_filter_btn)
        filter_layout.addLayout(filter_config_layout)

        # 筛选条件列表
        self.filter_list_widget = QListWidget()
        self.filter_list_widget.setMinimumHeight(40)
        self.filter_list_widget.itemDoubleClicked.connect(self.on_filter_item_double_clicked)
        filter_layout.addWidget(self.filter_list_widget)

        filter_group.setLayout(filter_layout)
        analysis_layout.addWidget(filter_group, 4, 0, 1, 3)

        # 开始分析按钮
        self.run_btn = QPushButton('开始分析')
        self.run_btn.clicked.connect(self.run_analysis)
        analysis_layout.addWidget(self.run_btn, 5, 0, 1, 1)

        # 重置按钮
        self.reset_btn = QPushButton('重置')
        self.reset_btn.clicked.connect(self.reset_analysis)
        analysis_layout.addWidget(self.reset_btn, 5, 1, 1, 1)

        analysis_group.setLayout(analysis_layout)
        left_layout.addWidget(analysis_group)

        # 时间序列配置（同比/环比）
        self.ts_group = QGroupBox('时间序列配置')
        ts_layout = QHBoxLayout()
        ts_layout.addWidget(QLabel('日期:'))
        self.ts_date_col = QComboBox()
        ts_layout.addWidget(self.ts_date_col)
        ts_layout.addWidget(QLabel('数值:'))
        self.ts_val_col = QComboBox()
        ts_layout.addWidget(self.ts_val_col)
        ts_layout.addWidget(QLabel('周期:'))
        self.ts_period = QComboBox()
        self.ts_period.addItems(['月', '季'])
        ts_layout.addWidget(self.ts_period)
        self.ts_group.setLayout(ts_layout)
        left_layout.addWidget(self.ts_group)

        left_widget.setMaximumWidth(450)
        main_layout.addWidget(left_widget)

        # 右侧：结果展示区
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        self.info_label = QLabel('请导入数据')
        right_layout.addWidget(self.info_label)

        self.tab_widget = QTabWidget()

        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout()

        # 筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('筛选:'))
        self.preview_filter_col = QComboBox()
        self.preview_filter_col.setMinimumWidth(120)
        filter_layout.addWidget(self.preview_filter_col)
        self.preview_filter_op = QComboBox()
        self.preview_filter_op.addItems(['>', '<', '==', '!=', '>=', '<=', '包含'])
        filter_layout.addWidget(self.preview_filter_op)
        self.preview_filter_value = QLineEdit()
        self.preview_filter_value.setPlaceholderText('值')
        self.preview_filter_value.setMaximumWidth(150)
        filter_layout.addWidget(self.preview_filter_value)
        self.preview_filter_apply = QPushButton('筛选')
        self.preview_filter_apply.clicked.connect(self._apply_preview_filter)
        filter_layout.addWidget(self.preview_filter_apply)
        self.preview_filter_reset = QPushButton('重置')
        self.preview_filter_reset.clicked.connect(self._reset_preview_filter)
        filter_layout.addWidget(self.preview_filter_reset)
        self.preview_filter_info = QLabel('')
        filter_layout.addWidget(self.preview_filter_info)
        filter_layout.addStretch()
        preview_layout.addLayout(filter_layout)

        self.preview_table = QTableWidget()
        preview_layout.addWidget(self.preview_table)
        self.preview_tab.setLayout(preview_layout)
        self.tab_widget.addTab(self.preview_tab, '数据预览')

        self.stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        self.stats_table = QTableWidget()
        stats_layout.addWidget(self.stats_table)
        self.stats_tab.setLayout(stats_layout)
        self.tab_widget.addTab(self.stats_tab, '统计结果')

        self.quality_tab = QWidget()
        quality_layout = QVBoxLayout()
        self.quality_text = QTextEdit()
        self.quality_text.setReadOnly(True)
        quality_layout.addWidget(self.quality_text)
        self.quality_tab.setLayout(quality_layout)
        self.tab_widget.addTab(self.quality_tab, '质量报告')

        self.compare_tab = QWidget()
        compare_layout = QVBoxLayout()
        self.compare_table = QTableWidget()
        compare_layout.addWidget(self.compare_table)
        self.compare_tab.setLayout(compare_layout)
        self.tab_widget.addTab(self.compare_tab, '分组对比')

        self.freq_tab = QWidget()
        freq_layout = QVBoxLayout()
        self.freq_table = QTableWidget()
        freq_layout.addWidget(self.freq_table)
        self.freq_tab.setLayout(freq_layout)
        self.tab_widget.addTab(self.freq_tab, '频次分析')

        # 图表标签页
        self.chart_tab = QWidget()
        chart_layout = QVBoxLayout()
        self.chart_widget = ChartWidget()
        chart_layout.addWidget(self.chart_widget)
        self.chart_tab.setLayout(chart_layout)
        self.tab_widget.addTab(self.chart_tab, '图表')

        right_layout.addWidget(self.tab_widget)

        main_layout.addWidget(right_widget, stretch=3)

        self.setLayout(main_layout)

        # 初始状态：隐藏分组相关控件
        self.group_combo.hide()
        self.agg_col_combo.hide()
        self.agg_func_combo.hide()
        self.add_agg_btn.hide()
        self.agg_list_widget.hide()
        self.filter_col_combo.hide()
        self.filter_op_combo.hide()
        self.filter_value_edit.hide()
        self.add_filter_btn.hide()
        self.filter_list_widget.hide()
        self.ts_group.hide()

    def update_data(self, df: pd.DataFrame, info: Dict[str, Any]):
        """更新数据"""
        self.current_df = df
        self.current_info = info

        self.info_label.setText(
            f'文件: {info.get("file_path", "无")} | '
            f'行数: {info["rows"]} | 列数: {info["columns"]}'
        )

        self.field_selector.set_dataframe(df)
        self.update_preview(df)
        self.update_column_combos(df)

    def update_column_combos(self, df: pd.DataFrame):
        """更新列下拉框"""
        # 分组列下拉（勾选项）
        self.group_combo.clear()
        for col in df.columns:
            self.group_combo.addItem(col)
            item = self.group_combo.model().item(self.group_combo.count() - 1, 0)
            item.setCheckable(True)
            item.setCheckState(Qt.CheckState.Unchecked)

        # 聚合值列（显示所有列）
        self.agg_col_combo.clear()
        self.agg_col_combo.addItems([str(c) for c in df.columns])

        # 筛选条件列
        self.filter_col_combo.clear()
        self.filter_col_combo.addItems([str(c) for c in df.columns])

        # 预览筛选列
        self.preview_filter_col.clear()
        self.preview_filter_col.addItems([str(c) for c in df.columns])

        # 时间序列列
        self.ts_date_col.clear()
        self.ts_date_col.addItems([str(c) for c in df.columns])
        self.ts_val_col.clear()
        self.ts_val_col.addItems([str(c) for c in df.columns])

    def update_preview(self, df: pd.DataFrame):
        """更新数据预览"""
        self.preview_table.clear()
        self.preview_table.setSortingEnabled(False)

        rows = min(100, len(df))
        cols = len(df.columns)

        self.preview_table.setRowCount(rows)
        self.preview_table.setColumnCount(cols)
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for i in range(rows):
            for j, col_name in enumerate(df.columns):
                value = df.iloc[i, j]
                if col_name in ('占比%', '累计占比%'):
                    text = _fmt_percent(value)
                else:
                    text = _fmt_value(value)
                self.preview_table.setItem(i, j, QTableWidgetItem(text))

        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.preview_table.setSortingEnabled(True)
        total_rows = len(df)
        shown = min(100, total_rows)
        self.preview_filter_info.setText(f'显示 {shown} / {total_rows} 行')

    def _apply_preview_filter(self):
        """应用预览筛选"""
        if self.current_df is None:
            return
        col = self.preview_filter_col.currentText()
        op = self.preview_filter_op.currentText()
        value_text = self.preview_filter_value.text()
        if not col or not value_text:
            return

        try:
            if '.' in value_text:
                value = float(value_text)
            else:
                value = int(value_text)
        except ValueError:
            value = value_text

        df = self.current_df
        if col not in df.columns:
            return
        try:
            if op == '>':
                filtered = df[df[col] > value]
            elif op == '<':
                filtered = df[df[col] < value]
            elif op == '==':
                filtered = df[df[col] == value]
            elif op == '!=':
                filtered = df[df[col] != value]
            elif op == '>=':
                filtered = df[df[col] >= value]
            elif op == '<=':
                filtered = df[df[col] <= value]
            elif op == '包含':
                filtered = df[df[col].astype(str).str.contains(str(value), na=False)]
            else:
                return
            self.update_preview(filtered)
        except Exception as e:
            QMessageBox.warning(self, '筛选错误', str(e))

    def _reset_preview_filter(self):
        """重置预览筛选"""
        self.preview_filter_value.clear()
        if self.current_df is not None:
            self.update_preview(self.current_df)

    def on_field_selection_changed(self, selected_columns: List[str]):
        """字段选择变化"""
        pass

    def _on_group_item_pressed(self, index):
        """点击分组列下拉项时切换勾选状态"""
        item = self.group_combo.model().itemFromIndex(index)
        if item is not None:
            current = item.checkState()
            item.setCheckState(
                Qt.CheckState.Unchecked if current == Qt.CheckState.Checked
                else Qt.CheckState.Checked
            )

    def on_analysis_type_changed(self, analysis_type: str):
        """分析类型变化"""
        is_group_analysis = analysis_type in ('分组分析', '频次分析', '综合分析')

        # 分组列选择
        self.group_combo.setVisible(is_group_analysis)

        # 聚合配置 - 分组分析和综合分析都需要
        show_agg = is_group_analysis
        for w in [self.agg_col_combo, self.agg_func_combo, self.add_agg_btn, self.agg_list_widget]:
            w.setVisible(show_agg)

        # 筛选条件 - 分组分析和综合分析显示
        show_filter = analysis_type in ('分组分析', '综合分析')
        for w in [self.filter_col_combo, self.filter_op_combo, self.filter_value_edit,
                  self.add_filter_btn, self.filter_list_widget]:
            w.setVisible(show_filter)

        # 时间序列配置 - 同比/环比分析显示
        is_ts = analysis_type in ('同比分析', '环比分析')
        self.ts_group.setVisible(is_ts)

    def _get_group_columns(self) -> List[str]:
        """从分组下拉获取选中的列"""
        cols = []
        model = self.group_combo.model()
        for i in range(self.group_combo.count()):
            item = model.item(i, 0)
            if item.checkState() == Qt.CheckState.Checked:
                cols.append(item.text())
        return cols

    def add_aggregation_item(self):
        """添加聚合项"""
        col = self.agg_col_combo.currentText()
        func = self.agg_func_combo.currentText()
        alias = f'{col}-{func}'

        # 检查是否已存在
        for item in self.agg_items:
            if item['col'] == col and item['func'] == func:
                QMessageBox.warning(self, '警告', '该聚合项已存在')
                return

        agg_item = {'col': col, 'func': func, 'alias': alias}
        self.agg_items.append(agg_item)

        self.update_agg_list_widget()

    def update_agg_list_widget(self):
        """更新聚合项列表显示"""
        self.agg_list_widget.clear()
        for i, item in enumerate(self.agg_items):
            text = f"{item['col']} - {item['func']}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, i)
            list_item.setToolTip('双击移除')
            self.agg_list_widget.addItem(list_item)

    def on_agg_item_double_clicked(self, item: QListWidgetItem):
        """双击聚合项移除"""
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.agg_items):
            self.agg_items.pop(index)
            self.update_agg_list_widget()

    def remove_agg_item(self, index: int):
        """移除聚合项"""
        if 0 <= index < len(self.agg_items):
            self.agg_items.pop(index)
            self.update_agg_list_widget()

    def add_filter_condition(self):
        """添加筛选条件"""
        col = self.filter_col_combo.currentText()
        op = self.filter_op_combo.currentText()
        value = self.filter_value_edit.text()

        if not value:
            QMessageBox.warning(self, '警告', '请输入筛选值')
            return

        # 尝试转换数值
        try:
            if not value:
                raise ValueError('empty')
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
        except (ValueError, TypeError):
            pass  # 保持字符串

        condition = {'col': col, 'op': op, 'value': value}
        self.condition_items.append(condition)

        self.update_filter_list_widget()

    def update_filter_list_widget(self):
        """更新筛选条件列表显示"""
        self.filter_list_widget.clear()
        for i, cond in enumerate(self.condition_items):
            text = f"{cond['col']} {cond['op']} {cond['value']}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, i)
            list_item.setToolTip('双击移除')
            self.filter_list_widget.addItem(list_item)

    def on_filter_item_double_clicked(self, item: QListWidgetItem):
        """双击筛选条件移除"""
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.condition_items):
            self.condition_items.pop(index)
            self.update_filter_list_widget()

    def reset_analysis(self):
        """重置分析配置"""
        # 清空聚合项
        self.agg_items.clear()
        self.update_agg_list_widget()
        # 清空筛选条件
        self.condition_items.clear()
        self.update_filter_list_widget()
        # 清空分组列选择
        model = self.group_combo.model()
        for i in range(self.group_combo.count()):
            model.item(i, 0).setCheckState(Qt.CheckState.Unchecked)
        # 清空结果表格
        self.stats_table.clear()
        self.compare_table.clear()
        self.freq_table.clear()
        self.quality_text.clear()
        self.last_result_df = None
        self.chart_widget.clear()
        # 切换到数据预览
        self.tab_widget.setCurrentWidget(self.preview_tab)

    def run_analysis(self):
        """执行分析"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return

        selected_columns = self.field_selector.get_selected_columns()
        if not selected_columns and self.analysis_type_combo.currentText() not in (
            '频次分析', '综合分析', '同比分析', '环比分析'):
            QMessageBox.warning(self, '警告', '请选择要分析的字段')
            return

        analysis_type = self.analysis_type_combo.currentText()

        try:
            if analysis_type == '描述性统计':
                self.run_descriptive_stats(selected_columns)
            elif analysis_type == '缺失值检测':
                self.run_missing_detection(selected_columns)
            elif analysis_type == '异常值检测':
                self.run_outlier_detection(selected_columns)
            elif analysis_type == '格式问题检测':
                self.run_format_detection(selected_columns)
            elif analysis_type == '分组分析':
                self.run_group_analysis()
            elif analysis_type == '频次分析':
                self.run_frequency_analysis()
            elif analysis_type == '综合分析':
                self.run_comprehensive_analysis()
            elif analysis_type == '同比分析':
                self.run_yoy_analysis()
            elif analysis_type == '环比分析':
                self.run_mom_analysis()
        except Exception as e:
            import traceback
            QMessageBox.critical(self, '错误', str(e) + '\n' + traceback.format_exc())

    def run_descriptive_stats(self, columns: List[str]):
        """执行描述性统计"""
        analyzer = self.main_window.analyzer
        stats = analyzer.describe_cols(self.current_df, columns)

        if stats.empty:
            QMessageBox.information(self, '提示', '选中的列中没有数值类型数据')
            return

        self.tab_widget.setCurrentWidget(self.stats_tab)
        self.show_stats_table(stats)

        # 图表：均值柱状图
        if 'mean' in stats.columns:
            self.chart_widget.draw_bar_chart(stats['mean'], title='平均值对比')

    def run_missing_detection(self, columns: List[str]):
        """执行缺失值检测"""
        analyzer = self.main_window.analyzer
        result = analyzer.detect_missing_cols(self.current_df, columns)

        self.tab_widget.setCurrentWidget(self.quality_tab)
        self.show_quality_report({'missing': result})

    def run_outlier_detection(self, columns: List[str]):
        """执行异常值检测"""
        analyzer = self.main_window.analyzer
        result = analyzer.detect_outliers_cols(self.current_df, columns)

        self.tab_widget.setCurrentWidget(self.quality_tab)
        self.show_quality_report({'outliers': result})

        # 图表：箱线图
        self.chart_widget.draw_boxplot(self.current_df, columns)

    def run_format_detection(self, columns: List[str]):
        """执行格式问题检测"""
        analyzer = self.main_window.analyzer
        result = analyzer.detect_format_issues_cols(self.current_df, columns)

        self.tab_widget.setCurrentWidget(self.quality_tab)
        self.show_quality_report({'format_issues': result})

    def run_group_analysis(self):
        """执行分组分析"""
        # 获取选中的分组列
        group_cols = self._get_group_columns()

        if not group_cols:
            QMessageBox.warning(self, '警告', '请选择至少一个分组列')
            return

        if not self.agg_items:
            QMessageBox.warning(self, '警告', '请添加至少一个聚合项')
            return

        analyzer = self.main_window.analyzer

        # 执行聚合
        result = analyzer.aggregate_with_custom_funcs(
            self.current_df, group_cols, self.agg_items
        )

        if result.empty:
            QMessageBox.information(self, '提示', '无法进行分组分析')
            return

        self.tab_widget.setCurrentWidget(self.compare_tab)
        self.show_compare_table(result)

        # 图表：分组柱状图
        numeric_cols = result.select_dtypes(include=[np.number]).columns.tolist()
        if group_cols and numeric_cols:
            self.chart_widget.draw_grouped_bar(result, group_cols[0], numeric_cols)

    def run_frequency_analysis(self):
        """执行频次分析"""
        selected_columns = self.field_selector.get_selected_columns()
        if not selected_columns:
            QMessageBox.warning(self, '警告', '请选择要分析的字段')
            return

        analyzer = self.main_window.analyzer

        result = analyzer.frequency_analysis(self.current_df, selected_columns)

        if result.empty:
            QMessageBox.information(self, '提示', '无法进行频次分析')
            return

        self.tab_widget.setCurrentWidget(self.freq_tab)
        self.show_freq_table(result)

        # 图表：频次柱状图（前 20 项）
        self.chart_widget.draw_bar_chart(result.head(20), title='频次分析（前 20）')

    def run_comprehensive_analysis(self):
        """执行综合分析（分组 + 频次）"""
        # 获取选中的分组列
        group_cols = self._get_group_columns()

        if not group_cols:
            QMessageBox.warning(self, '警告', '请选择至少一个分组列')
            return

        # 获取选中的值列（字段选择区）
        selected_columns = self.field_selector.get_selected_columns()
        if not selected_columns:
            selected_columns = []

        analyzer = self.main_window.analyzer

        # 1. 分组聚合结果
        group_result = None
        if self.agg_items:
            group_result = analyzer.aggregate_with_custom_funcs(
                self.current_df, group_cols, self.agg_items
            )

        # 2. 频次分析结果（基于分组列）
        freq_result = analyzer.frequency_analysis(self.current_df, group_cols)

        # 合并结果到 last_result_df（分组结果优先）
        if group_result is not None and not group_result.empty:
            self.last_result_df = group_result
            self.tab_widget.setCurrentWidget(self.compare_tab)
            self.show_compare_table(group_result)
        elif not freq_result.empty:
            self.last_result_df = freq_result
            self.tab_widget.setCurrentWidget(self.freq_tab)
            self.show_freq_table(freq_result)
        else:
            QMessageBox.information(self, '提示', '无法进行综合分析')

    def run_yoy_analysis(self):
        """执行同比分析"""
        self._run_time_series_analysis('同比')

    def run_mom_analysis(self):
        """执行环比分析"""
        self._run_time_series_analysis('环比')

    def _run_time_series_analysis(self, mode: str):
        """执行同比/环比分析"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return
        date_col = self.ts_date_col.currentText()
        val_col = self.ts_val_col.currentText()
        period = 'month' if self.ts_period.currentText() == '月' else 'quarter'

        if not date_col or not val_col:
            QMessageBox.warning(self, '警告', '请选择日期列和数值列')
            return

        analyzer = self.main_window.analyzer
        try:
            if mode == '同比':
                result = analyzer.yoy_analysis(self.current_df, date_col, val_col, period)
            else:
                result = analyzer.mom_analysis(self.current_df, date_col, val_col, period)

            if result.empty:
                QMessageBox.information(self, '提示', '数据不足，无法分析（需要至少两期数据）')
                return

            self.last_result_df = result
            self.tab_widget.setCurrentWidget(self.compare_tab)
            self.show_compare_table(result)
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def show_stats_table(self, stats: pd.DataFrame):
        """显示统计结果表格"""
        self.stats_table.clear()

        if stats.empty:
            return

        rows = len(stats)
        cols = len(stats.columns) + 1

        self.stats_table.setRowCount(rows)
        self.stats_table.setColumnCount(cols)
        self.stats_table.setHorizontalHeaderLabels(['指标'] + list(stats.columns))

        for i, idx in enumerate(stats.index):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(idx)))

        for i, idx in enumerate(stats.index):
            for j, col in enumerate(stats.columns):
                value = stats.iloc[i, j]
                text = _fmt_value(value)
                self.stats_table.setItem(i, j + 1, QTableWidgetItem(text))

        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setSortingEnabled(True)

    def show_quality_report(self, report: Dict[str, Any]):
        """显示质量报告"""
        lines = []
        lines.append('=' * 50)
        lines.append('数据质量报告')
        lines.append('=' * 50)

        if report.get('missing'):
            lines.append('\n【缺失值】')
            for col, info in report['missing'].items():
                lines.append(f"  {col}: {info['count']} 个 ({info['percentage']:.2f}%)")

        if report.get('outliers'):
            lines.append('\n【异常值】')
            for col, info in report['outliers'].items():
                bounds = f" (范围: {info.get('lower_bound', '无')} ~ {info.get('upper_bound', '无')})"
                lines.append(f"  {col}: {info['count']} 个{bounds}")

        if report.get('format_issues'):
            lines.append('\n【格式问题】')
            for col, issues in report['format_issues'].items():
                lines.append(f"  {col}: {', '.join(issues)}")

        if report.get('duplicates'):
            lines.append('\n【重复行】')
            dup = report['duplicates']
            lines.append(f"  重复行数: {dup['count']} ({dup['percentage']:.2f}%)")

        lines.append('\n' + '=' * 50)

        self.quality_text.setText('\n'.join(lines))

    def show_compare_table(self, stats: pd.DataFrame):
        """显示分组对比表格"""
        self.compare_table.clear()

        if stats.empty:
            return

        self.last_result_df = stats

        rows = len(stats)
        cols = len(stats.columns)

        self.compare_table.setRowCount(rows)
        self.compare_table.setColumnCount(cols)
        self.compare_table.setHorizontalHeaderLabels([str(c) for c in stats.columns])

        for i in range(rows):
            for j, col in enumerate(stats.columns):
                value = stats.iloc[i, j]
                text = _fmt_value(value)
                self.compare_table.setItem(i, j, QTableWidgetItem(text))

        self.compare_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.compare_table.setSortingEnabled(True)

    def show_freq_table(self, freq: pd.DataFrame):
        """显示频次分析表格"""
        self.freq_table.clear()

        if freq.empty:
            return

        rows = len(freq)
        cols = len(freq.columns)

        self.freq_table.setRowCount(rows)
        self.freq_table.setColumnCount(cols)
        self.freq_table.setHorizontalHeaderLabels([str(c) for c in freq.columns])

        for i in range(rows):
            for j, col in enumerate(freq.columns):
                value = freq.iloc[i, j]
                if col in ('占比%', '累计占比%'):
                    text = _fmt_percent(value)
                else:
                    text = _fmt_value(value)
                self.freq_table.setItem(i, j, QTableWidgetItem(text))

        self.freq_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.freq_table.setSortingEnabled(True)

        self.last_result_df = freq
