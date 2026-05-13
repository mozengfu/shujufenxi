"""复杂报表模板设计器"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QGroupBox, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QFileDialog, QTabWidget, QWidget, QHeaderView, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import json
from pathlib import Path
from typing import Optional

from core.complex_report import (
    ComplexReportTemplate, HeaderCell, CalculationRule,
    ConditionalFormat, TotalRowConfig, TemplateLibrary
)


class HeaderDesignerWidget(QWidget):
    """表头设计器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.headers = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 工具栏
        toolbar = QHBoxLayout()
        self.btn_add_level = QPushButton('添加层级')
        self.btn_add_level.clicked.connect(self.add_header_level)
        toolbar.addWidget(self.btn_add_level)

        self.btn_add_cell = QPushButton('添加单元格')
        self.btn_add_cell.clicked.connect(self.add_header_cell)
        toolbar.addWidget(self.btn_add_cell)

        self.btn_delete = QPushButton('删除选中')
        self.btn_delete.clicked.connect(self.delete_selected)
        toolbar.addWidget(self.btn_delete)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 表头表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            '名称', '跨行数', '跨列数', '父级', '数据字段', '对齐'
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def add_header_level(self):
        """添加新的表头层级"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._setup_row(row)

    def add_header_cell(self):
        """在当前行添加单元格"""
        current_row = self.table.currentRow()
        if current_row < 0:
            current_row = self.table.rowCount()

        self.table.insertRow(current_row)
        self._setup_row(current_row)

    def _setup_row(self, row: int):
        """设置行默认值"""
        # 名称
        self.table.setItem(row, 0, QTableWidgetItem(''))

        # 跨行数
        rowspan_spin = QSpinBox()
        rowspan_spin.setRange(1, 10)
        rowspan_spin.setValue(1)
        self.table.setCellWidget(row, 1, rowspan_spin)

        # 跨列数
        colspan_spin = QSpinBox()
        colspan_spin.setRange(1, 20)
        colspan_spin.setValue(1)
        self.table.setCellWidget(row, 2, colspan_spin)

        # 父级
        self.table.setItem(row, 3, QTableWidgetItem(''))

        # 数据字段
        self.table.setItem(row, 4, QTableWidgetItem(''))

        # 对齐
        align_combo = QComboBox()
        align_combo.addItems(['left', 'center', 'right'])
        align_combo.setCurrentText('center')
        self.table.setCellWidget(row, 5, align_combo)

    def delete_selected(self):
        """删除选中行"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def get_headers(self) -> list:
        """获取表头定义"""
        headers = []
        current_level = []

        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text() if self.table.item(row, 0) else ''
            rowspan = self.table.cellWidget(row, 1).value() if self.table.cellWidget(row, 1) else 1
            colspan = self.table.cellWidget(row, 2).value() if self.table.cellWidget(row, 2) else 1
            parent = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
            data_field = self.table.item(row, 4).text() if self.table.item(row, 4) else ''
            align = self.table.cellWidget(row, 5).currentText() if self.table.cellWidget(row, 5) else 'center'

            cell = HeaderCell(
                name=name,
                rowspan=rowspan,
                colspan=colspan,
                parent=parent if parent else None,
                data_field=data_field if data_field else None,
                align=align
            )
            current_level.append(cell)

        if current_level:
            headers.append(current_level)

        return headers

    def set_headers(self, headers: list):
        """设置表头定义"""
        self.table.setRowCount(0)

        for level in headers:
            for cell in level:
                row = self.table.rowCount()
                self.table.insertRow(row)

                # 名称
                self.table.setItem(row, 0, QTableWidgetItem(cell.name))

                # 跨行数
                rowspan_spin = QSpinBox()
                rowspan_spin.setRange(1, 10)
                rowspan_spin.setValue(cell.rowspan)
                self.table.setCellWidget(row, 1, rowspan_spin)

                # 跨列数
                colspan_spin = QSpinBox()
                colspan_spin.setRange(1, 20)
                colspan_spin.setValue(cell.colspan)
                self.table.setCellWidget(row, 2, colspan_spin)

                # 父级
                self.table.setItem(row, 3, QTableWidgetItem(cell.parent or ''))

                # 数据字段
                self.table.setItem(row, 4, QTableWidgetItem(cell.data_field or ''))

                # 对齐
                align_combo = QComboBox()
                align_combo.addItems(['left', 'center', 'right'])
                align_combo.setCurrentText(cell.align)
                self.table.setCellWidget(row, 5, align_combo)


class CalculationRuleWidget(QWidget):
    """计算规则配置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 工具栏
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton('添加规则')
        self.btn_add.clicked.connect(self.add_rule)
        toolbar.addWidget(self.btn_add)

        self.btn_delete = QPushButton('删除选中')
        self.btn_delete.clicked.connect(self.delete_selected)
        toolbar.addWidget(self.btn_delete)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 规则表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            '名称', '计算类型', '参数', '说明'
        ])
        layout.addWidget(self.table)

    def add_rule(self):
        """添加计算规则"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 名称
        self.table.setItem(row, 0, QTableWidgetItem(''))

        # 计算类型
        type_combo = QComboBox()
        type_combo.addItems(['rank', 'formula', 'sum', 'avg', 'custom'])
        self.table.setCellWidget(row, 1, type_combo)

        # 参数
        self.table.setItem(row, 2, QTableWidgetItem('{}'))

        # 说明
        self.table.setItem(row, 3, QTableWidgetItem(''))

    def delete_selected(self):
        """删除选中行"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def get_rules(self) -> list:
        """获取计算规则"""
        rules = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text() if self.table.item(row, 0) else ''
            calc_type = self.table.cellWidget(row, 1).currentText() if self.table.cellWidget(row, 1) else 'rank'
            params_text = self.table.item(row, 2).text() if self.table.item(row, 2) else '{}'

            try:
                params = json.loads(params_text)
            except:
                params = {}

            rule = CalculationRule(
                name=name,
                calc_type=calc_type,
                params=params
            )
            rules.append(rule)

        return rules


class TemplateDesignerDialog(QDialog):
    """模板设计器对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('复杂报表模板设计器')
        self.setMinimumSize(1000, 700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 基本信息
        info_group = QGroupBox('基本信息')
        info_layout = QVBoxLayout(info_group)

        # 模板名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('模板名称:'))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        info_layout.addLayout(name_layout)

        # 报表标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel('报表标题:'))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)
        info_layout.addLayout(title_layout)

        # 副标题
        subtitle_layout = QHBoxLayout()
        subtitle_layout.addWidget(QLabel('副标题:'))
        self.subtitle_edit = QLineEdit()
        subtitle_layout.addWidget(self.subtitle_edit)
        info_layout.addLayout(subtitle_layout)

        layout.addWidget(info_group)

        # Tab 容器
        self.tabs = QTabWidget()

        # 表头设计
        self.header_designer = HeaderDesignerWidget()
        self.tabs.addTab(self.header_designer, '表头设计')

        # 计算规则
        self.calc_rules = CalculationRuleWidget()
        self.tabs.addTab(self.calc_rules, '计算规则')

        # 合计行
        self.total_row_widget = self._create_total_row_widget()
        self.tabs.addTab(self.total_row_widget, '合计行')

        layout.addWidget(self.tabs)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_load = QPushButton('加载模板')
        self.btn_load.clicked.connect(self.load_template)
        btn_layout.addWidget(self.btn_load)

        self.btn_save = QPushButton('保存模板')
        self.btn_save.clicked.connect(self.save_template)
        btn_layout.addWidget(self.btn_save)

        self.btn_preview = QPushButton('预览')
        self.btn_preview.clicked.connect(self.preview_template)
        btn_layout.addWidget(self.btn_preview)

        self.btn_ok = QPushButton('确定')
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton('取消')
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _create_total_row_widget(self) -> QWidget:
        """创建合计行配置界面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 启用合计行
        self.total_enabled = QComboBox()
        self.total_enabled.addItems(['启用', '禁用'])
        layout.addWidget(QLabel('合计行:'))
        layout.addWidget(self.total_enabled)

        # 合计行标签
        self.total_label = QLineEdit('合计')
        layout.addWidget(QLabel('标签:'))
        layout.addWidget(self.total_label)

        # 聚合配置说明
        layout.addWidget(QLabel('聚合配置在导出时根据数据类型自动设置'))

        return widget

    def get_template(self) -> ComplexReportTemplate:
        """获取当前配置的模板"""
        return ComplexReportTemplate(
            name=self.name_edit.text() or 'unnamed',
            title=self.title_edit.text(),
            subtitle=self.subtitle_edit.text(),
            headers=self.header_designer.get_headers(),
            calculations=self.calc_rules.get_rules(),
            total_row=TotalRowConfig(
                enabled=self.total_enabled.currentText() == '启用',
                label=self.total_label.text()
            )
        )

    def set_template(self, template: ComplexReportTemplate):
        """设置模板到界面"""
        self.name_edit.setText(template.name)
        self.title_edit.setText(template.title)
        self.subtitle_edit.setText(template.subtitle)
        self.header_designer.set_headers(template.headers)

        # 设置合计行
        self.total_enabled.setCurrentText('启用' if template.total_row.enabled else '禁用')
        self.total_label.setText(template.total_row.label)

    def save_template(self):
        """保存模板到文件"""
        template = self.get_template()

        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存模板', '', 'JSON Files (*.json)'
        )

        if file_path:
            template.save(file_path)
            QMessageBox.information(self, '成功', f'模板已保存到: {file_path}')

    def load_template(self):
        """从文件加载模板"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '加载模板', '', 'JSON Files (*.json)'
        )

        if file_path:
            try:
                template = ComplexReportTemplate.load(file_path)
                self.set_template(template)
                QMessageBox.information(self, '成功', f'模板已加载: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'加载模板失败: {str(e)}')

    def preview_template(self):
        """预览模板效果"""
        template = self.get_template()
        QMessageBox.information(
            self, '模板预览',
            f'模板名称: {template.name}\n'
            f'报表标题: {template.title}\n'
            f'表头层级数: {len(template.headers)}\n'
            f'计算规则数: {len(template.calculations)}'
        )


def show_template_designer(parent=None) -> Optional[ComplexReportTemplate]:
    """显示模板设计器对话框"""
    dialog = TemplateDesignerDialog(parent)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.get_template()
    return None