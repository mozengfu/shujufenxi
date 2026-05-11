"""自定义报表设计器 UI"""
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
                              QListWidget, QListWidgetItem, QPushButton,
                              QLabel, QMessageBox, QFileDialog, QWidget,
                              QAbstractItemView)
from PyQt5.QtCore import Qt, QSettings

import pandas as pd
from core.report_builder import ReportConfig, ReportSection, ReportGenerator


AVAILABLE_SECTIONS = [
    ('title', '报告标题'),
    ('stats', '描述性统计'),
    ('quality', '数据质量报告'),
    ('text', '文本块'),
    ('data_table', '数据明细表'),
    ('chart', '分析图表'),
    ('analysis_result', '分析结果'),
]


class ReportDesigner(QDialog):
    """自定义报表设计器"""

    def __init__(self, parent=None, df: pd.DataFrame = None):
        super().__init__(parent)
        self.main_window = parent
        self.df = df
        self.config = ReportConfig()
        self.analyzer = None
        if parent and hasattr(parent, 'analyzer'):
            self.analyzer = parent.analyzer
        self.chart_figures = {}
        self.analysis_result = None
        if parent and hasattr(parent, 'analysis_panel'):
            fig = parent.analysis_panel.chart_figure
            if fig is not None:
                self.chart_figures['current'] = fig
            self.analysis_result = parent.analysis_panel.last_result_df
        self.settings = QSettings('shujufenxi', 'report_templates')
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('自定义报表设计器')
        self.setMinimumSize(750, 550)

        layout = QVBoxLayout()

        # 主区域：两栏布局
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：可用内容
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel('可用内容'))
        self.available_list = QListWidget()
        for stype, sname in AVAILABLE_SECTIONS:
            item = QListWidgetItem(sname)
            item.setData(Qt.UserRole, stype)
            self.available_list.addItem(item)
        self.available_list.itemDoubleClicked.connect(self._add_section)
        left_layout.addWidget(self.available_list)

        add_btn = QPushButton('添加 →')
        add_btn.clicked.connect(self._add_selected)
        left_layout.addWidget(add_btn)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # 右侧：已选章节
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel('已选章节（双击编辑标题）'))
        self.section_list = QListWidget()
        self.section_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.section_list.itemDoubleClicked.connect(self._edit_section_title)
        right_layout.addWidget(self.section_list)

        btn_row = QHBoxLayout()
        self.remove_btn = QPushButton('移除')
        self.remove_btn.clicked.connect(self._remove_section)
        btn_row.addWidget(self.remove_btn)

        self.up_btn = QPushButton('上移')
        self.up_btn.clicked.connect(self._move_up)
        btn_row.addWidget(self.up_btn)

        self.down_btn = QPushButton('下移')
        self.down_btn.clicked.connect(self._move_down)
        btn_row.addWidget(self.down_btn)

        btn_row.addStretch()
        right_layout.addLayout(btn_row)
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        splitter.setSizes([250, 500])
        layout.addWidget(splitter)

        # 底部按钮
        bottom_layout = QHBoxLayout()

        self.export_word_btn = QPushButton('导出 Word')
        self.export_word_btn.clicked.connect(self._export_word)
        bottom_layout.addWidget(self.export_word_btn)

        self.export_excel_btn = QPushButton('导出 Excel')
        self.export_excel_btn.clicked.connect(self._export_excel)
        bottom_layout.addWidget(self.export_excel_btn)

        bottom_layout.addSpacing(16)

        self.save_template_btn = QPushButton('保存模板')
        self.save_template_btn.clicked.connect(self._save_template)
        bottom_layout.addWidget(self.save_template_btn)

        self.load_template_btn = QPushButton('加载模板')
        self.load_template_btn.clicked.connect(self._load_template)
        bottom_layout.addWidget(self.load_template_btn)

        bottom_layout.addStretch()
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def _add_section(self, item: QListWidgetItem):
        """双击左侧添加章节"""
        stype = item.data(Qt.UserRole)
        sname = item.text()
        section = ReportSection(section_type=stype, title=sname)
        self.config.sections.append(section)
        self._refresh_section_list()

    def _add_selected(self):
        """点击按钮添加选中的章节"""
        item = self.available_list.currentItem()
        if item:
            self._add_section(item)

    def _remove_section(self):
        """移除选中的章节"""
        row = self.section_list.currentRow()
        if row >= 0 and row < len(self.config.sections):
            self.config.sections.pop(row)
            self._refresh_section_list()

    def _move_up(self):
        """上移章节"""
        row = self.section_list.currentRow()
        if row > 0 and row < len(self.config.sections):
            self.config.sections[row], self.config.sections[row-1] = \
                self.config.sections[row-1], self.config.sections[row]
            self._refresh_section_list()
            self.section_list.setCurrentRow(row - 1)

    def _move_down(self):
        """下移章节"""
        row = self.section_list.currentRow()
        if 0 <= row < len(self.config.sections) - 1:
            self.config.sections[row], self.config.sections[row+1] = \
                self.config.sections[row+1], self.config.sections[row]
            self._refresh_section_list()
            self.section_list.setCurrentRow(row + 1)

    def _edit_section_title(self, item: QListWidgetItem):
        """双击编辑章节标题"""
        row = self.section_list.currentRow()
        if row >= 0 and row < len(self.config.sections):
            from PyQt5.QtWidgets import QInputDialog
            new_title, ok = QInputDialog.getText(
                self, '编辑标题', '请输入新标题:',
                text=self.config.sections[row].title
            )
            if ok and new_title:
                self.config.sections[row].title = new_title
                self._refresh_section_list()

    def _refresh_section_list(self):
        """刷新已选章节列表"""
        self.section_list.clear()
        for i, section in enumerate(self.config.sections):
            text = f'{i+1}. [{section.section_type}] {section.title}'
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, i)
            self.section_list.addItem(item)

    def _export_word(self):
        """导出 Word 报告"""
        if self.df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return
        if not self.config.sections:
            QMessageBox.warning(self, '警告', '请先添加报表章节')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出 Word 报告', '', 'Word 文档 (*.docx)'
        )
        if not file_path:
            return
        if not file_path.endswith('.docx'):
            file_path += '.docx'

        try:
            from core.reporter import WordReporter
            reporter = WordReporter()
            generator = ReportGenerator(self.df, self.analyzer, self.analysis_result)
            generator.generate_word(self.config, reporter, self.chart_figures)
            reporter.save(file_path)
            QMessageBox.information(self, '成功', f'已导出到 {file_path}')
        except Exception as e:
            import traceback
            QMessageBox.critical(self, '错误', str(e) + '\n' + traceback.format_exc())

    def _export_excel(self):
        """导出 Excel 报告"""
        if self.df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return
        if not self.config.sections:
            QMessageBox.warning(self, '警告', '请先添加报表章节')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出 Excel 报告', '', 'Excel 文件 (*.xlsx)'
        )
        if not file_path:
            return
        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'

        try:
            from core.exporter import ExcelExporter
            exporter = ExcelExporter()
            generator = ReportGenerator(self.df, self.analyzer, self.analysis_result)
            generator.generate_excel(self.config, exporter, file_path)
            QMessageBox.information(self, '成功', f'已导出到 {file_path}')
        except Exception as e:
            import traceback
            QMessageBox.critical(self, '错误', str(e) + '\n' + traceback.format_exc())

    def _save_template(self):
        """保存模板到 QSettings"""
        if not self.config.sections:
            QMessageBox.warning(self, '警告', '没有章节可保存')
            return

        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, '保存模板', '模板名称:')
        if ok and name:
            try:
                existing = json.loads(self.settings.value('templates', '{}'))
            except (json.JSONDecodeError, TypeError):
                existing = {}
            existing[name] = self.config.to_dict()
            self.settings.setValue('templates', json.dumps(existing, ensure_ascii=False))
            QMessageBox.information(self, '成功', f'模板 "{name}" 已保存')

    def _load_template(self):
        """从 QSettings 加载模板"""
        try:
            templates_data = json.loads(self.settings.value('templates', '{}'))
        except (json.JSONDecodeError, TypeError):
            templates_data = {}

        if not templates_data:
            QMessageBox.information(self, '提示', '没有已保存的模板')
            return

        names = list(templates_data.keys())
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getItem(self, '加载模板', '选择模板:', names, 0, False)
        if ok and name:
            self.config = ReportConfig.from_dict(templates_data[name])
            self._refresh_section_list()
            QMessageBox.information(self, '成功', f'模板 "{name}" 已加载')
