"""分析面板模块"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QTableWidget, QTableWidgetItem, QLabel, QComboBox,
                              QGroupBox, QTextEdit, QTabWidget, QHeaderView,
                              QPushButton, QMessageBox, QListWidget,
                              QListWidgetItem, QLineEdit, QDialog, QFormLayout,
                              QCheckBox)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from .field_selector import FieldSelector
from .chart_widget import ChartWidget
from core import TableImporter
from core.analyzer import AGG_FUNCTIONS, make_total_row, is_percent_col
from core.ai_summarizer import AISummarizer


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


class AggItemDialog(QDialog):
    """聚合项配置对话框：支持自定义列名、筛选条件、占比"""

    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.df = df
        self.setWindowTitle('聚合项配置')
        self.resize(400, 350)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # 值列
        self.col_combo = QComboBox()
        self.col_combo.addItems([str(c) for c in self.df.columns])
        layout.addRow('值列:', self.col_combo)

        # 聚合函数
        self.func_combo = QComboBox()
        self.func_combo.addItems(list(AGG_FUNCTIONS.keys()))
        layout.addRow('聚合:', self.func_combo)

        # 自定义列名
        self.alias_edit = QLineEdit()
        self.alias_edit.setPlaceholderText('留空则自动生成')
        layout.addRow('自定义列名:', self.alias_edit)

        # 显示占比
        self.show_percent_cb = QCheckBox('显示占比（该列总值的百分比）')
        layout.addRow('', self.show_percent_cb)

        # 百分比模式选择
        self.percent_mode_combo = QComboBox()
        self.percent_mode_combo.addItems(['按列总计', '按组总数'])
        self.percent_mode_combo.setVisible(False)
        self.show_percent_cb.toggled.connect(self.percent_mode_combo.setVisible)
        layout.addRow('占比基准:', self.percent_mode_combo)

        # 筛选条件区域
        cond_group = QGroupBox('筛选条件（可选，留空表示不过滤）')
        cond_layout = QVBoxLayout()

        self.cond_col_combo = QComboBox()
        self.cond_col_combo.addItems([str(c) for c in self.df.columns])
        self.cond_col_combo.insertItem(0, '-- 不筛选 --')

        self.cond_op_combo = QComboBox()
        self.cond_op_combo.addItems(['>', '<', '==', '!=', '>=', '<=', '包含'])

        self.cond_value_edit = QLineEdit()
        self.cond_value_edit.setPlaceholderText('筛选值')

        cond_row_layout = QHBoxLayout()
        cond_row_layout.addWidget(self.cond_col_combo)
        cond_row_layout.addWidget(self.cond_op_combo)
        cond_row_layout.addWidget(self.cond_value_edit)
        cond_layout.addLayout(cond_row_layout)

        self.cond_list_widget = QListWidget()
        self.cond_list_widget.setMinimumHeight(40)
        self.cond_list_widget.itemDoubleClicked.connect(self._remove_cond)
        cond_layout.addWidget(self.cond_list_widget)

        add_cond_btn = QPushButton('添加条件')
        add_cond_btn.clicked.connect(self._add_cond)
        cond_layout.addWidget(add_cond_btn)

        cond_group.setLayout(cond_layout)
        layout.addRow('', cond_group)

        # 按钮
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow('', btn_layout)

        self.setLayout(layout)
        self.conditions: List[Dict] = []

    def _add_cond(self):
        col = self.cond_col_combo.currentText()
        if col == '-- 不筛选 --':
            return
        op = self.cond_op_combo.currentText()
        value = self.cond_value_edit.text()
        if not value:
            QMessageBox.warning(self, '警告', '请输入筛选值')
            return
        self.conditions.append({'col': col, 'op': op, 'value': value})
        self.cond_list_widget.addItem(f'{col} {op} {value}')
        self.cond_value_edit.clear()

    def _remove_cond(self, item: QListWidgetItem):
        idx = self.cond_list_widget.row(item)
        if 0 <= idx < len(self.conditions):
            self.conditions.pop(idx)
            self.cond_list_widget.takeItem(idx)

    def get_result(self) -> Dict[str, Any]:
        col = self.col_combo.currentText()
        func = self.func_combo.currentText()
        alias = self.alias_edit.text().strip() or f'{col}-{func}'
        show_percent = self.show_percent_cb.isChecked()
        percent_mode = 'group' if self.percent_mode_combo.currentText() == '按组总数' else 'column'

        condition_dict = {}
        for cond in self.conditions:
            condition_dict[cond['col']] = (cond['op'], cond['value'])

        return {
            'col': col,
            'func': func,
            'alias': alias,
            'show_percent': show_percent,
            'percent_mode': percent_mode,
            'condition': condition_dict if condition_dict else None
        }


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
        # 从 QSettings 读取 AI 配置
        settings = QSettings('shujufenxi', 'settings')
        self.summarizer = AISummarizer(
            api_key=settings.value('ai_api_key', ''),
            model=settings.value('ai_model', 'claude-sonnet-4-6'),
            endpoint=settings.value('ai_endpoint', 'https://api.anthropic.com/v1/messages'),
        )
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

        # AI 总结标签页
        self.ai_tab = QWidget()
        ai_layout = QVBoxLayout()
        self.ai_summary_edit = QTextEdit()
        self.ai_summary_edit.setPlaceholderText('点击"生成 AI 总结"按钮，AI 将根据当前分析结果解读数据含义。')
        ai_layout.addWidget(self.ai_summary_edit)

        ai_btn_layout = QHBoxLayout()
        self.ai_gen_btn = QPushButton('生成 AI 总结')
        self.ai_gen_btn.clicked.connect(self.generate_ai_summary)
        ai_btn_layout.addWidget(self.ai_gen_btn)
        ai_btn_layout.addStretch()
        ai_layout.addLayout(ai_btn_layout)
        self.ai_tab.setLayout(ai_layout)
        self.tab_widget.addTab(self.ai_tab, 'AI 总结')

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
            item.setCheckState(Qt.Unchecked)

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

        self.preview_table.setRowCount(rows + 1)
        self.preview_table.setColumnCount(cols)
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for i in range(rows):
            for j, col_name in enumerate(df.columns):
                value = df.iloc[i, j]
                if is_percent_col(col_name):
                    text = _fmt_percent(value)
                else:
                    text = _fmt_value(value)
                self.preview_table.setItem(i, j, QTableWidgetItem(text))

        # 合计行
        total_row = make_total_row(df)
        for j, col_name in enumerate(df.columns):
            item = QTableWidgetItem(_fmt_value(total_row.iloc[j]))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.preview_table.setItem(rows, j, item)

        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
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
                Qt.Unchecked if current == Qt.Checked
                else Qt.Checked
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
            if item.checkState() == Qt.Checked:
                cols.append(item.text())
        return cols

    def add_aggregation_item(self):
        """添加聚合项（弹出配置对话框）"""
        if self.current_df is None or self.current_df.empty:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return

        dialog = AggItemDialog(self.current_df, self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()

            # 检查是否已存在相同别名
            for item in self.agg_items:
                if item.get('alias') == result['alias']:
                    QMessageBox.warning(self, '警告', f'列名 "{result["alias"]}" 已存在')
                    return

            self.agg_items.append(result)
            self.update_agg_list_widget()

    def update_agg_list_widget(self):
        """更新聚合项列表显示"""
        self.agg_list_widget.clear()
        for i, item in enumerate(self.agg_items):
            col = item['col']
            func = item['func']
            alias = item.get('alias', f'{col}-{func}')
            conditions = item.get('condition') or {}
            show_percent = item.get('show_percent', False)
            percent_mode = item.get('percent_mode', 'column')

            parts = [f'{col} - {func} [{alias}]']
            for cond_col, (op, val) in conditions.items():
                parts.append(f'{cond_col}{op}{val}')
            if show_percent:
                mode_label = '组' if percent_mode == 'group' else '列'
                parts.append(f'占比:{mode_label}')

            text = '  '.join(parts)
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.UserRole, i)
            list_item.setToolTip('双击移除')
            self.agg_list_widget.addItem(list_item)

    def on_agg_item_double_clicked(self, item: QListWidgetItem):
        """双击聚合项移除"""
        index = item.data(Qt.UserRole)
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
            list_item.setData(Qt.UserRole, i)
            list_item.setToolTip('双击移除')
            self.filter_list_widget.addItem(list_item)

    def on_filter_item_double_clicked(self, item: QListWidgetItem):
        """双击筛选条件移除"""
        index = item.data(Qt.UserRole)
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
            model.item(i, 0).setCheckState(Qt.Unchecked)
        # 清空结果表格
        self.stats_table.clear()
        self.compare_table.clear()
        self.freq_table.clear()
        self.quality_text.clear()
        self.last_result_df = None
        self.chart_widget.clear()
        # 切换到数据预览
        self.tab_widget.setCurrentWidget(self.preview_tab)

    def _refresh_ai_config(self):
        """在调用 AI 前重新读取配置，避免使用初始化时的旧值"""
        settings = QSettings('shujufenxi', 'settings')
        self.summarizer.api_key = settings.value('ai_api_key', '')
        self.summarizer.model = settings.value('ai_model', 'claude-sonnet-4-6')
        self.summarizer.endpoint = settings.value('ai_endpoint', 'https://api.anthropic.com/v1/messages')

    def generate_ai_summary(self):
        """生成 AI 数据解读总结"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return

        # 重新读取最新 AI 配置
        self._refresh_ai_config()
        if not self.summarizer.api_key:
            QMessageBox.warning(self, '警告', '请先在 AI 配置中设置 API Key')
            return

        # 调试信息：显示当前配置
        ep = self.summarizer.endpoint
        model = self.summarizer.model
        key_preview = self.summarizer.api_key[:10] + '...' if self.summarizer.api_key else '(empty)'
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, 'AI 配置', f'Endpoint: {ep}\nModel: {model}\nKey: {key_preview}')

        self.ai_summary_edit.setText('正在生成 AI 总结...')
        self.ai_gen_btn.setEnabled(False)

        # 收集分析上下文
        stats = self.main_window.analyzer.descriptive_stats(self.current_df) if self.current_df is not None else None
        quality = self.main_window.analyzer.full_quality_report(self.current_df) if self.current_df is not None else None
        freq = self.last_result_df if self.last_result_df is not None and '频次' in self.last_result_df.columns else None
        analysis = self.last_result_df

        summary = self.summarizer.summarize(
            df=self.current_df,
            stats=stats,
            quality_report=quality,
            freq_result=freq,
            analysis_result=analysis,
        )

        self.ai_summary_edit.setText(summary)
        self.ai_gen_btn.setEnabled(True)

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
        group_cols = self._get_group_columns()

        if not group_cols:
            QMessageBox.warning(self, '警告', '请选择至少一个分组列')
            return

        if not self.agg_items:
            QMessageBox.warning(self, '警告', '请添加至少一个聚合项')
            return

        analyzer = self.main_window.analyzer

        # 判断是否有多条件项（condition 或 show_percent）
        has_multi_cond = any(
            item.get('condition') or item.get('show_percent')
            for item in self.agg_items
        )

        if has_multi_cond:
            result = analyzer.multi_conditional_aggregate(
                self.current_df, group_cols, self.agg_items
            )
        else:
            result = analyzer.aggregate_with_custom_funcs(
                self.current_df, group_cols, self.agg_items
            )

        if result.empty:
            QMessageBox.information(self, '提示', '无法进行分组分析')
            return

        self.tab_widget.setCurrentWidget(self.compare_tab)
        self.show_compare_table(result)

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
        group_cols = self._get_group_columns()

        if not group_cols:
            QMessageBox.warning(self, '警告', '请选择至少一个分组列')
            return

        selected_columns = self.field_selector.get_selected_columns()
        if not selected_columns:
            selected_columns = []

        analyzer = self.main_window.analyzer

        # 1. 分组聚合结果
        group_result = None
        if self.agg_items:
            has_multi_cond = any(
                item.get('condition') or item.get('show_percent')
                for item in self.agg_items
            )
            if has_multi_cond:
                group_result = analyzer.multi_conditional_aggregate(
                    self.current_df, group_cols, self.agg_items
                )
            else:
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

        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

        self.compare_table.setRowCount(rows + 1)
        self.compare_table.setColumnCount(cols)
        self.compare_table.setHorizontalHeaderLabels([str(c) for c in stats.columns])

        for i in range(rows):
            for j, col in enumerate(stats.columns):
                value = stats.iloc[i, j]
                if is_percent_col(col):
                    text = _fmt_percent(value)
                else:
                    text = _fmt_value(value)
                self.compare_table.setItem(i, j, QTableWidgetItem(text))

        # 合计行
        total_row = make_total_row(stats, self.agg_items)
        for j, col in enumerate(stats.columns):
            if is_percent_col(col):
                text = _fmt_percent(total_row.iloc[j])
            else:
                text = _fmt_value(total_row.iloc[j])
            item = QTableWidgetItem(text)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.compare_table.setItem(rows, j, item)

        self.compare_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.compare_table.setSortingEnabled(True)

    def show_freq_table(self, freq: pd.DataFrame):
        """显示频次分析表格"""
        self.freq_table.clear()

        if freq.empty:
            return

        rows = len(freq)
        cols = len(freq.columns)

        self.freq_table.setRowCount(rows + 1)
        self.freq_table.setColumnCount(cols)
        self.freq_table.setHorizontalHeaderLabels([str(c) for c in freq.columns])

        for i in range(rows):
            for j, col in enumerate(freq.columns):
                value = freq.iloc[i, j]
                if is_percent_col(col):
                    text = _fmt_percent(value)
                else:
                    text = _fmt_value(value)
                self.freq_table.setItem(i, j, QTableWidgetItem(text))

        # 合计行
        total_row = make_total_row(freq)
        for j, col in enumerate(freq.columns):
            if col == '占比%':
                total_row.iloc[j] = 100.0
            if is_percent_col(col):
                text = _fmt_percent(total_row.iloc[j])
            else:
                text = _fmt_value(total_row.iloc[j])
            item = QTableWidgetItem(text)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.freq_table.setItem(rows, j, item)

        self.freq_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.freq_table.setSortingEnabled(True)

        self.last_result_df = freq
