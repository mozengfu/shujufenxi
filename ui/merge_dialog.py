"""多表合并对话框"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QListWidget, QFileDialog, QComboBox,
                              QGroupBox, QTableWidget, QTableWidgetItem,
                              QHeaderView, QRadioButton, QMessageBox)
import pandas as pd
from typing import List, Dict, Any
from PyQt6.QtGui import QColor

from core import TableImporter


class MergeDialog(QDialog):
    """多表合并对话框"""

    def __init__(self, parent=None, initial_df: pd.DataFrame = None):
        super().__init__(parent)
        self.initial_df = initial_df
        self.tables: List[Dict[str, Any]] = []  # {'name': str, 'df': DataFrame, 'path': str}
        self.merge_mode = 'key'
        self.init_ui()

        # 如果有初始 DataFrame，添加到表中
        if initial_df is not None:
            self.tables.append({
                'name': '当前数据',
                'df': initial_df,
                'path': '当前数据'
            })
            self.update_table_list()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('多表合并')
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout()

        # 已导入表区域
        list_group = QGroupBox('已导入的表')
        list_layout = QVBoxLayout()

        self.table_list = QListWidget()
        self.table_list.itemClicked.connect(self.on_table_selected)
        list_layout.addWidget(self.table_list)

        btn_layout = QHBoxLayout()
        self.add_table_btn = QPushButton('添加表')
        self.add_table_btn.clicked.connect(self.add_table)
        btn_layout.addWidget(self.add_table_btn)

        self.remove_table_btn = QPushButton('移除表')
        self.remove_table_btn.clicked.connect(self.remove_table)
        btn_layout.addWidget(self.remove_table_btn)

        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # 表信息显示
        self.table_info = QTableWidget()
        self.table_info.setMaximumHeight(120)
        self.table_info.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_info)

        # 列结构对比
        struct_layout = QHBoxLayout()
        self.struct_btn = QPushButton('列结构对比')
        self.struct_btn.clicked.connect(self._compare_structures)
        struct_layout.addWidget(self.struct_btn)
        struct_layout.addStretch()
        layout.addLayout(struct_layout)

        # 合并模式选择
        mode_group = QGroupBox('合并模式')
        mode_layout = QHBoxLayout()

        self.key_radio = QRadioButton('按关键列合并 (VLOOKUP 模式)')
        self.key_radio.setChecked(True)
        self.key_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.key_radio)

        self.append_radio = QRadioButton('行追加合并 (相同结构)')
        self.append_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.append_radio)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 关键列选择
        key_group = QGroupBox('合并参数')
        key_layout = QHBoxLayout()

        key_layout.addWidget(QLabel('关键列:'))
        self.key_combo = QComboBox()
        key_layout.addWidget(self.key_combo)

        key_layout.addWidget(QLabel('合并方式:'))
        self.how_combo = QComboBox()
        self.how_combo.addItem('内连接', 'inner')
        self.how_combo.addItem('左连接', 'left')
        self.how_combo.addItem('右连接', 'right')
        self.how_combo.addItem('外连接', 'outer')
        key_layout.addWidget(self.how_combo)

        key_group.setLayout(key_layout)
        layout.addWidget(key_group)

        # 预览按钮
        preview_btn = QPushButton('预览合并结果')
        preview_btn.clicked.connect(self.preview_merge)
        layout.addWidget(preview_btn)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton('开始合并')
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_table(self):
        """添加表"""
        files, _ = QFileDialog.getOpenFileNames(
            self, '选择要合并的文件', '', 'Excel/CSV 文件 (*.xlsx *.xls *.csv)'
        )

        if files:
            importer = TableImporter()
            for path in files:
                try:
                    df = importer.import_file(path)
                    # 提取文件名作为表名
                    import os
                    name = os.path.basename(path)
                    self.tables.append({
                        'name': name,
                        'df': df,
                        'path': path
                    })
                except Exception as e:
                    QMessageBox.warning(self, '警告', f'无法导入 {path}: {str(e)}')

            self.update_table_list()

    def remove_table(self):
        """移除选中的表"""
        current_row = self.table_list.currentRow()
        if current_row >= 0:
            # 不能移除第一个表（初始数据），除非只剩这一个表
            if current_row == 0 and len(self.tables) > 1:
                return
            self.tables.pop(current_row)
            self.update_table_list()

    def update_table_list(self):
        """更新表列表"""
        self.table_list.clear()
        for table in self.tables:
            info = f"{table['name']} ({len(table['df'])}行 x {len(table['df'].columns)}列)"
            self.table_list.addItem(info)

    def on_table_selected(self, item):
        """表选择变化"""
        row = self.table_list.currentRow()
        if row >= 0 and row < len(self.tables):
            table = self.tables[row]
            self.show_table_info(table['df'])

            # 更新关键列下拉
            self.key_combo.clear()
            self.key_combo.addItems([str(c) for c in table['df'].columns])

    def show_table_info(self, df: pd.DataFrame):
        """显示表信息"""
        self.table_info.clear()

        cols = len(df.columns)
        self.table_info.setRowCount(1)
        self.table_info.setColumnCount(cols)
        self.table_info.setHorizontalHeaderLabels([str(c) for c in df.columns])

        # 显示第一行数据
        for j in range(cols):
            value = df.iloc[0, j] if len(df) > 0 else ''
            text = '' if pd.isna(value) else str(value)
            self.table_info.setItem(0, j, QTableWidgetItem(text))

        self.table_info.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _compare_structures(self):
        """列结构对比 - 弹窗显示所有表的列信息"""
        if len(self.tables) < 1:
            QMessageBox.warning(self, '警告', '没有可对比的表')
            return

        # 收集每张表的列信息
        all_columns = {}  # col_name -> {table_name: dtype}
        all_names = []
        for tbl in self.tables:
            name = tbl['name']
            all_names.append(name)
            for col in tbl['df'].columns:
                if col not in all_columns:
                    all_columns[col] = {}
                all_columns[col][name] = tbl['df'][col].dtype

        # 构建弹窗
        dialog = QDialog(self)
        dialog.setWindowTitle('列结构对比')
        dialog.setMinimumSize(650, 400)

        layout = QVBoxLayout()

        # 汇总信息
        common_cols = [c for c, v in all_columns.items() if len(v) == len(self.tables)]
        total_unique = set()
        for cols in all_columns.values():
            total_unique.update(cols.keys())
        info_label = QLabel(
            f'共有 {len(all_columns)} 个唯一列名，'
            f'其中 {len(common_cols)} 列在所有表中都存在'
        )
        layout.addWidget(info_label)

        # 对比表格
        table = QTableWidget()
        cols_n = len(all_names) + 1
        table.setColumnCount(cols_n)
        headers = ['列名'] + [n[:20] for n in all_names]
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(all_columns))

        for i, (col_name, tbl_map) in enumerate(sorted(all_columns.items())):
            table.setItem(i, 0, QTableWidgetItem(str(col_name)))
            for j, name in enumerate(all_names):
                dtype = tbl_map.get(name)
                if dtype is not None:
                    item = QTableWidgetItem(str(dtype))
                    # 标记类型不一致或缺失
                    if col_name not in common_cols:
                        item.setBackground(QColor('#FFE0E0'))
                    elif len(set(tbl_map.values())) > 1:
                        item.setBackground(QColor('#FFF0CC'))
                    table.setItem(i, j + 1, item)
                else:
                    item = QTableWidgetItem('—')
                    item.setBackground(QColor('#FFCCCC'))
                    table.setItem(i, j + 1, item)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def on_mode_changed(self):
        """合并模式变化"""
        self.merge_mode = 'key' if self.key_radio.isChecked() else 'append'

    def preview_merge(self):
        """预览合并结果"""
        if len(self.tables) < 2:
            QMessageBox.warning(self, '警告', '请至少添加两个表')
            return

        try:
            if self.merge_mode == 'key':
                preview_df = self.preview_key_merge()
            else:
                preview_df = self.preview_append_merge()

            if preview_df is not None:
                preview_dialog = QDialog(self)
                preview_dialog.setWindowTitle('合并预览')
                preview_dialog.setMinimumSize(600, 400)

                layout = QVBoxLayout()
                info_label = QLabel(f'结果: {len(preview_df)} 行 x {len(preview_df.columns)} 列')
                layout.addWidget(info_label)

                table = QTableWidget()
                rows = min(20, len(preview_df))
                table.setRowCount(rows)
                table.setColumnCount(len(preview_df.columns))
                table.setHorizontalHeaderLabels([str(c) for c in preview_df.columns])

                for i in range(rows):
                    for j in range(len(preview_df.columns)):
                        value = preview_df.iloc[i, j]
                        text = '' if pd.isna(value) else str(value)
                        table.setItem(i, j, QTableWidgetItem(text))

                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                layout.addWidget(table)

                close_btn = QPushButton('关闭')
                close_btn.clicked.connect(preview_dialog.close)
                layout.addWidget(close_btn)

                preview_dialog.setLayout(layout)
                preview_dialog.exec()
            else:
                QMessageBox.warning(self, '警告', '无法预览合并结果')
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def preview_key_merge(self) -> pd.DataFrame:
        """按关键列合并预览"""
        key_col = self.key_combo.currentText()
        if not key_col:
            return None

        how = self.how_combo.currentData()
        result = self.tables[0]['df']

        for i in range(1, len(self.tables)):
            df = self.tables[i]['df']
            if key_col not in df.columns:
                QMessageBox.warning(self, '警告', f"表 '{self.tables[i]['name']}' 中不存在关键列 '{key_col}'")
                return None
            result = result.merge(df, on=key_col, how=how, suffixes=('', f'_{i}'))

        return result.head(20)

    def preview_append_merge(self) -> pd.DataFrame:
        """行追加合并预览"""
        dfs = [t['df'] for t in self.tables]
        result = pd.concat(dfs, ignore_index=True)
        return result.head(20)

    def accept(self):
        """确认合并"""
        if len(self.tables) < 2:
            QMessageBox.warning(self, '警告', '请至少添加两个表')
            return

        self.merge_mode = 'key' if self.key_radio.isChecked() else 'append'
        super().accept()

    def get_result(self) -> Dict[str, Any]:
        """获取合并结果"""
        return {
            'tables': self.tables,
            'mode': self.merge_mode,
            'key_column': self.key_combo.currentText() if self.merge_mode == 'key' else None,
            'how': self.how_combo.currentData() if self.merge_mode == 'key' else None
        }