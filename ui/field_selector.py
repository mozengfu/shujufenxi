"""字段选择组件"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QColor
import pandas as pd
import numpy as np
from typing import Dict, List, Any


class FieldSelector(QWidget):
    """字段选择器 - QListWidget 带复选框"""

    selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df: pd.DataFrame = None
        self.field_list: QListWidget = None
        self._updating = False
        self.init_ui()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if self.parent() and hasattr(self.parent(), 'dropEvent'):
            self.parent().dropEvent(event)
        else:
            super().dropEvent(event)
        event.acceptProposedAction()

    def init_ui(self):
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel('字段选择'))
        header_layout.addStretch()

        self.select_all_btn = QPushButton('全选')
        self.select_all_btn.clicked.connect(self.select_all)
        header_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton('取消全选')
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        header_layout.addWidget(self.deselect_all_btn)

        layout.addLayout(header_layout)

        self.field_list = QListWidget()
        self.field_list.itemChanged.connect(self._on_item_changed)
        self.field_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.field_list)

        self.setLayout(layout)

    def set_dataframe(self, df: pd.DataFrame):
        self.df = df
        self.update_field_list()

    def update_field_list(self):
        self.field_list.clear()
        self._updating = True

        if self.df is not None:
            for col in self.df.columns:
                dtype = self.df[col].dtype
                is_num = np.issubdtype(dtype, np.number)
                type_tag = ' (数值)' if is_num else ' (文本)'
                missing = self.df[col].isna().sum()
                missing_tag = f' 缺失:{missing}' if missing > 0 else ''
                text = f'{col}{type_tag}{missing_tag}'

                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, col)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                if is_num:
                    item.setForeground(QColor('#2c3e50'))
                else:
                    item.setForeground(QColor('#7f8c8d'))
                self.field_list.addItem(item)

        self._updating = False
        self._notify_selection()

    def _on_item_changed(self, item):
        """项变化（复选框点击）"""
        if self._updating:
            return
        self._notify_selection()

    def _on_item_clicked(self, item):
        """点击行任意位置切换复选框"""
        current = item.checkState()
        item.setCheckState(
            Qt.CheckState.Unchecked if current == Qt.CheckState.Checked else Qt.CheckState.Checked
        )

    def _notify_selection(self):
        """通知选中变化"""
        self.selection_changed.emit(self.get_selected_columns())

    def select_all(self):
        for i in range(self.field_list.count()):
            self.field_list.item(i).setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        for i in range(self.field_list.count()):
            self.field_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_selected_columns(self) -> List[str]:
        items = []
        for i in range(self.field_list.count()):
            item = self.field_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                items.append(item.data(Qt.ItemDataRole.UserRole))
        return items

    def get_column_info(self, col: str) -> Dict[str, Any]:
        if self.df is None or col not in self.df.columns:
            return {}
        return {
            'dtype': str(self.df[col].dtype),
            'missing': int(self.df[col].isna().sum()),
            'unique': int(self.df[col].nunique()),
            'is_numeric': np.issubdtype(self.df[col].dtype, np.number)
        }
