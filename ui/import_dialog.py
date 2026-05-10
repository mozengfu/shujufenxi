"""导入对话框"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QListWidget, QFileDialog)
from PyQt5.QtCore import Qt


class ImportDialog(QDialog):
    """文件导入对话框"""

    def __init__(self, parent=None, multi_select=False):
        super().__init__(parent)
        self.multi_select = multi_select
        self.selected_file = None
        self.selected_files = []
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('导入文件')
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout()

        # 说明标签
        label = QLabel('选择要导入的 Excel 或 CSV 文件')
        layout.addWidget(label)

        # 文件列表
        self.file_list = QListWidget()
        if self.multi_select:
            self.file_list.setSelectionMode(Qt.MultiSelection)
        layout.addWidget(self.file_list)

        # 按钮
        button_layout = QHBoxLayout()

        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self.browse_files)
        button_layout.addWidget(browse_btn)

        button_layout.addStretch()

        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def browse_files(self):
        """浏览文件"""
        if self.multi_select:
            files, _ = QFileDialog.getOpenFileNames(
                self, '选择文件', '', 'Excel/CSV 文件 (*.xlsx *.xls *.csv)'
            )
            if files:
                self.selected_files = files
                self.file_list.clear()
                for f in files:
                    self.file_list.addItem(f)
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, '选择文件', '', 'Excel/CSV 文件 (*.xlsx *.xls *.csv)'
            )
            if file_path:
                self.selected_file = file_path
                self.file_list.clear()
                self.file_list.addItem(file_path)

    def accept(self):
        """确认"""
        if self.multi_select:
            self.selected_files = [self.file_list.item(i).text()
                                   for i in range(self.file_list.count())]
            if not self.selected_files:
                return
        else:
            self.selected_file = self.file_list.item(0).text() if self.file_list.count() > 0 else None
            if not self.selected_file:
                return
        super().accept()