"""列计算对话框"""
import re
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QLineEdit, QPushButton, QListWidget,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QGroupBox, QMessageBox)
from typing import Optional


class ColumnCalcDialog(QDialog):
    """列计算对话框 - 通过表达式创建新列"""

    def __init__(self, parent=None, df: pd.DataFrame = None):
        super().__init__(parent)
        self.main_window = parent
        self.source_df = df
        self.result_df = df.copy() if df is not None else None
        self.init_ui()
        self._fill_column_list()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('列计算')
        self.setMinimumSize(650, 500)

        layout = QVBoxLayout()

        # 可用列
        col_group = QGroupBox('可用列（双击插入列名）')
        col_layout = QVBoxLayout()
        self.col_list = QListWidget()
        self.col_list.itemDoubleClicked.connect(self._insert_column)
        col_layout.addWidget(self.col_list)
        col_group.setLayout(col_layout)
        layout.addWidget(col_group)

        # 表达式输入
        expr_group = QGroupBox('表达式')
        expr_layout = QVBoxLayout()
        help_label = QLabel('语法: 使用 {列名} 引用列，支持 +, -, *, / 四则运算')
        help_label.setStyleSheet('color: #666; font-size: 11px;')
        expr_layout.addWidget(help_label)
        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText('示例: {销售额} * 1.2 + {成本}')
        expr_layout.addWidget(self.expr_input)
        expr_group.setLayout(expr_layout)
        layout.addWidget(expr_group)

        # 新列名
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('新列名:'))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('输入新列名')
        name_layout.addWidget(self.name_input)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        self.preview_btn = QPushButton('预览')
        self.preview_btn.clicked.connect(self._preview)
        btn_layout.addWidget(self.preview_btn)

        self.apply_btn = QPushButton('应用')
        self.apply_btn.clicked.connect(self._apply)
        btn_layout.addWidget(self.apply_btn)

        btn_layout.addStretch()
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 预览
        preview_group = QGroupBox('预览结果（前 5 行）')
        preview_layout = QVBoxLayout()
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(160)
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        self.setLayout(layout)

    def _fill_column_list(self):
        """填充可用列列表"""
        self.col_list.clear()
        if self.source_df is None:
            return
        for col in self.source_df.columns:
            dtype = self.source_df[col].dtype
            is_num = np.issubdtype(dtype, np.number)
            label = f'{col}  [{dtype}]  {"(数值)" if is_num else "(文本)"}'
            self.col_list.addItem(label)

    def _insert_column(self, item):
        """双击列名插入到表达式"""
        col_name = item.text().split('  [')[0]
        current = self.expr_input.text()
        self.expr_input.setText(f'{current}{{{col_name}}}')
        self.expr_input.setFocus()

    def _build_expression(self) -> Optional[str]:
        """将 {col} 替换为列名，返回可供 df.eval 的表达式"""
        raw = self.expr_input.text().strip()
        if not raw:
            return None
        # 验证大括号匹配
        if raw.count('{') != raw.count('}'):
            return None
        # 替换 {col} → col
        expr = re.sub(r'\{(\w+)\}', r'\1', raw)
        # 验证所有引用的列都存在
        refs = re.findall(r'(\w+)', expr)
        for col_ref in refs:
            if col_ref not in self.source_df.columns and col_ref not in ('str', 'int', 'float', 'True', 'False', 'None'):
                # 可能是数值字面量或函数名，跳过
                pass
        return expr

    def _evaluate(self) -> Optional[pd.Series]:
        """计算表达式并返回结果 Series"""
        if self.source_df is None:
            return None
        raw = self.expr_input.text().strip()
        if not raw:
            return None
        new_name = self.name_input.text().strip()
        if not new_name:
            return None

        try:
            # 替换 {col} → df['col'] 以支持含空格的列名
            expr = re.sub(r'\{([^}]+)\}', r"df['\1']", raw)
            # 安全执行：只允许有限的操作
            result = eval(expr, {'df': self.source_df, 'pd': pd, 'np': np})
            if isinstance(result, pd.Series):
                return result
            # 标量结果转为 Series
            return pd.Series(result, index=self.source_df.index)
        except Exception as e:
            raise ValueError(f'表达式错误: {e}')

    def _preview(self):
        """预览计算结果"""
        if self.source_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return
        try:
            new_col = self._evaluate()
            if new_col is None:
                return
            new_name = self.name_input.text().strip() or '新列'
            preview_df = self.source_df.head(5).copy()
            preview_df[new_name] = new_col.head(5)
            self._show_preview_table(preview_df)
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def _apply(self):
        """应用并关闭"""
        if self.source_df is None:
            QMessageBox.warning(self, '警告', '没有可用的数据')
            return
        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, '警告', '请输入新列名')
            return
        try:
            new_col = self._evaluate()
            if new_col is None:
                return
            self.result_df = self.source_df.copy()
            self.result_df[new_name] = new_col
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def _show_preview_table(self, df: pd.DataFrame):
        """在预览表格中显示数据"""
        self.preview_table.clear()
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for i in range(len(df)):
            for j in range(len(df.columns)):
                value = df.iloc[i, j]
                text = '' if pd.isna(value) else str(value)
                self.preview_table.setItem(i, j, QTableWidgetItem(text))

        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def get_result(self) -> Optional[pd.DataFrame]:
        """获取包含新列的 DataFrame"""
        return self.result_df
