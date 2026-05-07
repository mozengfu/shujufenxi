"""报告导出对话框"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QLineEdit, QFileDialog, QCheckBox)


class ReportDialog(QDialog):
    """报告导出对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None
        self.include_stats = True
        self.include_quality = True
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('导出 Word 报告')
        self.setMinimumSize(500, 200)

        layout = QVBoxLayout()

        # 说明
        label = QLabel('设置报告导出选项')
        layout.addWidget(label)

        # 文件路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('保存路径:'))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText('选择保存位置...')
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        # 报告内容选项
        options_layout = QVBoxLayout()

        self.stats_checkbox = QCheckBox('包含描述性统计')
        self.stats_checkbox.setChecked(True)
        options_layout.addWidget(self.stats_checkbox)

        self.quality_checkbox = QCheckBox('包含数据质量报告')
        self.quality_checkbox.setChecked(True)
        options_layout.addWidget(self.quality_checkbox)

        layout.addLayout(options_layout)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def browse_file(self):
        """浏览保存路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存报告', '', 'Word 文档 (*.docx)'
        )
        if file_path:
            if not file_path.endswith('.docx'):
                file_path += '.docx'
            self.selected_file = file_path
            self.path_input.setText(file_path)

    def accept(self):
        """确认"""
        if not self.path_input.text():
            return

        self.selected_file = self.path_input.text()
        self.include_stats = self.stats_checkbox.isChecked()
        self.include_quality = self.quality_checkbox.isChecked()

        if not self.selected_file.endswith('.docx'):
            self.selected_file += '.docx'

        super().accept()