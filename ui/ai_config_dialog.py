"""AI 配置对话框"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                              QLineEdit, QComboBox, QPushButton, QLabel,
                              QMessageBox)
from PyQt5.QtCore import QSettings


PRESET_MODELS = [
    ('claude-sonnet-4-6', 'Claude Sonnet 4.6（推荐）'),
    ('claude-opus-4-7', 'Claude Opus 4.7'),
    ('claude-haiku-4-5-20251001', 'Claude Haiku 4.5'),
    ('custom', '自定义'),
]


class AIConfigDialog(QDialog):
    """AI 配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI 配置')
        self.resize(500, 250)
        self.settings = QSettings('shujufenxi', 'settings')
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText('sk-ant-...')
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        form.addRow('API Key:', self.api_key_edit)

        # Model
        self.model_combo = QComboBox()
        for value, label in PRESET_MODELS:
            self.model_combo.addItem(label, value)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        form.addRow('模型:', self.model_combo)

        # Custom model name input (hidden by default)
        self.custom_model_edit = QLineEdit()
        self.custom_model_edit.setPlaceholderText('输入自定义模型名')
        self.custom_model_edit.setVisible(False)
        form.addRow('自定义模型:', self.custom_model_edit)

        # Endpoint
        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText('https://api.anthropic.com/v1/messages')
        form.addRow('端点 URL:', self.endpoint_edit)

        layout.addLayout(form)

        # 提示
        tip = QLabel('提示：API Key 仅保存在本地，不会上传到服务器。')
        tip.setStyleSheet('color: gray; font-size: 11px;')
        layout.addWidget(tip)

        # 按钮
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton('测试连接')
        self.test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch()

        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _on_model_changed(self):
        is_custom = self.model_combo.currentData() == 'custom'
        self.custom_model_edit.setVisible(is_custom)

    def load_settings(self):
        api_key = self.settings.value('ai_api_key', '')
        model = self.settings.value('ai_model', 'claude-sonnet-4-6')
        endpoint = self.settings.value('ai_endpoint', 'https://api.anthropic.com/v1/messages')

        self.api_key_edit.setText(api_key)
        self.endpoint_edit.setText(endpoint)

        # Select model in combo
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model:
                self.model_combo.setCurrentIndex(i)
                break
        else:
            # Custom model
            idx = self.model_combo.findData('custom')
            self.model_combo.setCurrentIndex(idx)
            self.custom_model_edit.setText(model)

    def get_model(self) -> str:
        if self.model_combo.currentData() == 'custom':
            return self.custom_model_edit.text().strip()
        return self.model_combo.currentData()

    def save_and_close(self):
        self.settings.setValue('ai_api_key', self.api_key_edit.text().strip())
        self.settings.setValue('ai_model', self.get_model())
        self.settings.setValue('ai_endpoint', self.endpoint_edit.text().strip())
        self.accept()

    def test_connection(self):
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, '警告', '请先输入 API Key')
            return

        from core.ai_summarizer import AISummarizer
        model = self.get_model()
        endpoint = self.endpoint_edit.text().strip() or 'https://api.anthropic.com/v1/messages'

        summarizer = AISummarizer(api_key=api_key, model=model, endpoint=endpoint)
        result = summarizer.summarize(
            __import__('pandas').DataFrame({'测试': [1]}),
            context='这是一条测试消息，请回复"连接成功"。',
        )

        if '待接入' in result or '待配置' in result:
            QMessageBox.warning(self, '测试失败', result)
        elif '失败' in result or '出错' in result or '错误' in result:
            QMessageBox.warning(self, '测试失败', result)
        else:
            QMessageBox.information(self, '测试成功', result[:200])
