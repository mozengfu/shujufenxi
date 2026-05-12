"""数据清洗对话框"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QGroupBox, QComboBox, QLabel, QLineEdit,
                              QPushButton, QRadioButton, QButtonGroup,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QStackedWidget, QWidget)
import pandas as pd

from core.cleaner import DataCleaner


class CleanDialog(QDialog):
    """数据清洗对话框"""

    def __init__(self, parent=None, initial_df: pd.DataFrame = None):
        super().__init__(parent)
        self.main_window = parent
        self.current_df = initial_df
        self.cleaner = DataCleaner()
        self.result_df = None
        self.init_ui()
        self.update_column_combos()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('数据清洗')
        self.setMinimumSize(650, 550)

        main_layout = QVBoxLayout()

        # 清洗类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('清洗类型:'))
        self.clean_type_combo = QComboBox()
        self.clean_type_combo.addItems([
            '类型转换',
            '列拆分',
            '字符操作',
            '去除重复',
            '填充缺失'
        ])
        self.clean_type_combo.currentTextChanged.connect(self.on_clean_type_changed)
        type_layout.addWidget(self.clean_type_combo)
        type_layout.addStretch()
        main_layout.addLayout(type_layout)

        # 清洗操作区
        self.stack = QStackedWidget()
        self.create_type_convert_page()
        self.create_split_column_page()
        self.create_char_operation_page()
        self.create_remove_dup_page()
        self.create_fillna_page()
        main_layout.addWidget(self.stack)

        # 结果预览区
        result_group = QGroupBox('结果预览')
        result_layout = QVBoxLayout()
        self.result_table = QTableWidget()
        self.result_table.setMaximumHeight(180)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        result_layout.addWidget(self.result_table)
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.apply_btn = QPushButton('应用到数据')
        self.apply_btn.clicked.connect(self.apply_changes)
        btn_layout.addWidget(self.apply_btn)

        self.close_btn = QPushButton('关闭')
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def create_type_convert_page(self):
        """创建类型转换页面"""
        page = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox('类型转换')
        grid = QGridLayout()

        grid.addWidget(QLabel('列:'), 0, 0)
        self.type_col_combo = QComboBox()
        grid.addWidget(self.type_col_combo, 0, 1)

        grid.addWidget(QLabel('转换为:'), 1, 0)
        type_btn_layout = QHBoxLayout()
        self.type_btn_group = QButtonGroup()
        for text, val in [('整数', 'int'), ('小数', 'float'), ('文本', 'str'), ('日期', 'date')]:
            rb = QRadioButton(text)
            rb.setProperty('value', val)
            self.type_btn_group.addButton(rb)
            type_btn_layout.addWidget(rb)
        self.type_btn_group.buttons()[0].setChecked(True)
        grid.addLayout(type_btn_layout, 1, 1)

        self.type_convert_btn = QPushButton('执行转换')
        self.type_convert_btn.clicked.connect(self.do_type_convert)
        grid.addWidget(self.type_convert_btn, 2, 1)

        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def create_split_column_page(self):
        """创建列拆分页面"""
        page = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox('列拆分')
        grid = QGridLayout()

        grid.addWidget(QLabel('列:'), 0, 0)
        self.split_col_combo = QComboBox()
        grid.addWidget(self.split_col_combo, 0, 1)

        grid.addWidget(QLabel('分隔符:'), 1, 0)
        self.split_sep_edit = QLineEdit()
        self.split_sep_edit.setPlaceholderText('如: , 或 | 或 空格')
        grid.addWidget(self.split_sep_edit, 1, 1)

        grid.addWidget(QLabel('新列名(逗号分隔):'), 2, 0)
        self.split_new_cols_edit = QLineEdit()
        self.split_new_cols_edit.setPlaceholderText('如: col1, col2, col3')
        grid.addWidget(self.split_new_cols_edit, 2, 1)

        self.split_execute_btn = QPushButton('执行拆分')
        self.split_execute_btn.clicked.connect(self.do_split_column)
        grid.addWidget(self.split_execute_btn, 3, 1)

        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def create_char_operation_page(self):
        """创建字符操作页面"""
        page = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox('字符操作')
        grid = QGridLayout()

        grid.addWidget(QLabel('列:'), 0, 0)
        self.char_col_combo = QComboBox()
        grid.addWidget(self.char_col_combo, 0, 1)

        grid.addWidget(QLabel('操作:'), 1, 0)
        char_op_layout = QHBoxLayout()
        self.char_op_group = QButtonGroup()
        for i, text in enumerate(['添加前缀', '添加后缀', '移除字符', '替换值']):
            rb = QRadioButton(text)
            rb.setProperty('value', i)
            self.char_op_group.addButton(rb)
            char_op_layout.addWidget(rb)
        self.char_op_group.buttons()[0].setChecked(True)
        grid.addLayout(char_op_layout, 1, 1)

        grid.addWidget(QLabel('值:'), 2, 0)
        self.char_value_edit = QLineEdit()
        self.char_value_edit.setPlaceholderText('输入前缀/后缀/要移除的字符/要替换的值')
        grid.addWidget(self.char_value_edit, 2, 1)

        grid.addWidget(QLabel('替换为(替换值时):'), 3, 0)
        self.char_replace_edit = QLineEdit()
        self.char_replace_edit.setPlaceholderText('替换后的值')
        grid.addWidget(self.char_replace_edit, 3, 1)

        self.char_execute_btn = QPushButton('执行')
        self.char_execute_btn.clicked.connect(self.do_char_operation)
        grid.addWidget(self.char_execute_btn, 4, 1)

        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def create_remove_dup_page(self):
        """创建去除重复页面"""
        page = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox('去除重复行')
        grid = QGridLayout()

        grid.addWidget(QLabel('依据列(逗号分隔):'), 0, 0)
        self.dup_cols_edit = QLineEdit()
        self.dup_cols_edit.setPlaceholderText('留空则全部列')
        grid.addWidget(self.dup_cols_edit, 0, 1)

        self.dup_execute_btn = QPushButton('执行')
        self.dup_execute_btn.clicked.connect(self.do_remove_duplicates)
        grid.addWidget(self.dup_execute_btn, 1, 1)

        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def create_fillna_page(self):
        """创建填充缺失页面"""
        page = QWidget()
        layout = QVBoxLayout()

        group = QGroupBox('填充缺失值')
        grid = QGridLayout()

        grid.addWidget(QLabel('列:'), 0, 0)
        self.fillna_col_combo = QComboBox()
        grid.addWidget(self.fillna_col_combo, 0, 1)

        grid.addWidget(QLabel('填充值:'), 1, 0)
        self.fillna_value_edit = QLineEdit()
        self.fillna_value_edit.setPlaceholderText('输入填充值')
        grid.addWidget(self.fillna_value_edit, 1, 1)

        self.fillna_execute_btn = QPushButton('执行')
        self.fillna_execute_btn.clicked.connect(self.do_fillna)
        grid.addWidget(self.fillna_execute_btn, 2, 1)

        group.setLayout(grid)
        layout.addWidget(group)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def set_dataframe(self, df: pd.DataFrame):
        """设置数据框"""
        self.current_df = df
        self.update_column_combos()

    def update_column_combos(self):
        """更新列下拉框"""
        if self.current_df is None:
            return

        columns = list(self.current_df.columns)
        if not columns:
            return

        # 确保 combobox 已创建
        if not hasattr(self, 'type_col_combo'):
            return

        self.type_col_combo.clear()
        self.type_col_combo.addItems(columns)

        self.split_col_combo.clear()
        self.split_col_combo.addItems(columns)

        self.char_col_combo.clear()
        self.char_col_combo.addItems(columns)

        self.fillna_col_combo.clear()
        self.fillna_col_combo.addItems(columns)

    def on_clean_type_changed(self, clean_type: str):
        """清洗类型变化"""
        index_map = {
            '类型转换': 0,
            '列拆分': 1,
            '字符操作': 2,
            '去除重复': 3,
            '填充缺失': 4
        }
        self.stack.setCurrentIndex(index_map.get(clean_type, 0))

    def _get_preview_df(self) -> pd.DataFrame:
        """获取预览用的数据（最多10行）"""
        if self.current_df is None:
            return pd.DataFrame()
        return self.current_df.head(10)

    def _update_preview(self, df: pd.DataFrame):
        """更新预览（QTableWidget）"""
        self.result_table.clear()
        preview = df.head(10)
        rows = len(preview)
        cols = len(preview.columns)

        self.result_table.setRowCount(rows)
        self.result_table.setColumnCount(cols)
        self.result_table.setHorizontalHeaderLabels([str(c) for c in preview.columns])

        for i in range(rows):
            for j in range(cols):
                value = preview.iloc[i, j]
                text = '' if pd.isna(value) else str(value)
                self.result_table.setItem(i, j, QTableWidgetItem(text))

        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def do_type_convert(self):
        """执行类型转换"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return

        col = self.type_col_combo.currentText()
        if not col:
            QMessageBox.warning(self, '警告', '请选择要转换的列')
            return

        checked_btn = self.type_btn_group.checkedButton()
        if checked_btn:
            to_type = checked_btn.property('value')
        else:
            to_type = 'str'

        try:
            result = self.cleaner.convert_type(self.current_df, col, to_type)
            self.current_df = result
            self._update_preview(result)
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def do_split_column(self):
        """执行列拆分"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return

        col = self.split_col_combo.currentText()
        if not col:
            QMessageBox.warning(self, '警告', '请选择要拆分的列')
            return

        sep = self.split_sep_edit.text()
        if not sep:
            QMessageBox.warning(self, '警告', '请输入分隔符')
            return

        new_cols_text = self.split_new_cols_edit.text().strip()
        new_cols = [c.strip() for c in new_cols_text.split(',')] if new_cols_text else None

        try:
            result = self.cleaner.split_column(self.current_df, col, sep, new_cols)
            self.current_df = result
            self._update_preview(result)
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def do_char_operation(self):
        """执行字符操作"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return

        col = self.char_col_combo.currentText()
        if not col:
            QMessageBox.warning(self, '警告', '请选择要操作的列')
            return

        checked_btn = self.char_op_group.checkedButton()
        if checked_btn:
            op_index = checked_btn.property('value')
        else:
            op_index = 0

        value = self.char_value_edit.text()
        replace_val = self.char_replace_edit.text()

        try:
            if op_index == 0:  # 添加前缀
                result = self.cleaner.add_prefix_suffix(self.current_df, col, prefix=value, suffix='')
            elif op_index == 1:  # 添加后缀
                result = self.cleaner.add_prefix_suffix(self.current_df, col, prefix='', suffix=value)
            elif op_index == 2:  # 移除字符
                result = self.cleaner.remove_chars(self.current_df, col, value)
            elif op_index == 3:  # 替换值
                if not replace_val:
                    QMessageBox.warning(self, '警告', '请输入替换后的值')
                    return
                result = self.cleaner.replace_values(self.current_df, col, value, replace_val)
            else:
                return

            self.current_df = result
            self._update_preview(result)
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def do_remove_duplicates(self):
        """执行去除重复"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return

        cols_text = self.dup_cols_edit.text().strip()
        subset = [c.strip() for c in cols_text.split(',')] if cols_text else None

        try:
            result = self.cleaner.remove_duplicates(self.current_df, subset)
            removed_count = len(self.current_df) - len(result)
            self.current_df = result
            self._update_preview(result)
            QMessageBox.information(self, '提示', f'已移除 {removed_count} 行重复数据')
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def do_fillna(self):
        """执行填充缺失值"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return

        col = self.fillna_col_combo.currentText()
        if not col:
            QMessageBox.warning(self, '警告', '请选择要填充的列')
            return

        value_text = self.fillna_value_edit.text()
        if not value_text:
            QMessageBox.warning(self, '警告', '请输入填充值')
            return

        # 尝试转换数值
        try:
            if '.' in value_text:
                value = float(value_text)
            else:
                value = int(value_text)
        except ValueError:
            value = value_text

        try:
            result = self.cleaner.fillna_with_value(self.current_df, col, value)
            self.current_df = result
            self._update_preview(result)
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def apply_changes(self):
        """应用到数据"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return

        if self.result_table.rowCount() == 0 or self.result_table.columnCount() == 0:
            QMessageBox.warning(self, '警告', '请先执行清洗操作')
            return

        self.result_df = self.current_df

        if self.result_df is not None:
            if self.main_window and hasattr(self.main_window, 'current_df'):
                self.main_window.current_df = self.result_df
            if self.main_window and hasattr(self.main_window, 'analysis_panel'):
                info = {'rows': len(self.result_df), 'columns': len(self.result_df.columns), 'file_path': '清洗结果'}
                self.main_window.analysis_panel.update_data(self.result_df, info)
            QMessageBox.information(self, '成功', '数据已更新')
            self.close()

    def get_result(self) -> pd.DataFrame:
        """获取清洗结果"""
        return self.result_df
