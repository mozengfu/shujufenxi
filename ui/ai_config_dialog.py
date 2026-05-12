"""AI 配置对话框"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                              QLineEdit, QComboBox, QPushButton, QLabel,
                              QMessageBox)
from PyQt5.QtCore import QSettings


PRESET_MODELS = [
    ('claude-sonnet-4-6', 'Claude Sonnet 4.6（推荐）'),
    ('claude-opus-4-7', 'Claude Opus 4.7'),
    ('claude-haiku-4-5-20251001', 'Claude Haiku 4.5'),
    ('MiniMax-M2.7', 'MiniMax M2.7'),
    ('MiniMax-M2.5', 'MiniMax M2.5'),
    ('custom', '自定义'),
]


class AIConfigDialog(QDialog):
    """AI 配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI 配置')
        self.resize(500, 300)
        self.settings = QSettings('shujufenxi', 'settings')
        self._has_saved_key = False
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()

        # API Key — 不预填真实值，仅显示占位提示
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText('输入 API Key（留空则保留原值）')
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

        self.clear_btn = QPushButton('清除配置')
        self.clear_btn.clicked.connect(self.clear_settings)
        btn_layout.addWidget(self.clear_btn)

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

        # 不预填 API Key 的真实值，仅提示
        if api_key:
            self._has_saved_key = True
            self.api_key_edit.setText('')
            self.api_key_edit.setPlaceholderText('已配置（输入新值覆盖）')
        else:
            self._has_saved_key = False
            self.api_key_edit.setText('')
            self.api_key_edit.setPlaceholderText('输入 API Key')

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

    def get_api_key(self) -> str:
        """获取 API Key：优先用用户输入的，没有则用已保存的"""
        typed = self.api_key_edit.text().strip()
        if typed:
            return typed
        return self.settings.value('ai_api_key', '')

    def get_model(self) -> str:
        if self.model_combo.currentData() == 'custom':
            return self.custom_model_edit.text().strip()
        return self.model_combo.currentData()

    def save_and_close(self):
        api_key = self.get_api_key()
        if api_key:
            self.settings.setValue('ai_api_key', api_key)
        else:
            self.settings.remove('ai_api_key')
            self._has_saved_key = False
        self.settings.setValue('ai_model', self.get_model())
        self.settings.setValue('ai_endpoint', self.endpoint_edit.text().strip())
        self.accept()

    def clear_settings(self):
        self.settings.remove('ai_api_key')
        self.settings.remove('ai_model')
        self.settings.remove('ai_endpoint')
        self._has_saved_key = False
        self.api_key_edit.clear()
        self.api_key_edit.setPlaceholderText('输入 API Key')
        self.endpoint_edit.clear()
        self.model_combo.setCurrentIndex(0)
        QMessageBox.information(self, '提示', '配置已清除')

    def test_connection(self):
        api_key = self.get_api_key()
        if not api_key:
            QMessageBox.warning(self, '警告', '请先输入 API Key')
            return

        import httpx
        model = self.get_model()
        endpoint = self.endpoint_edit.text().strip() or 'https://api.anthropic.com/v1/messages'

        # 根据 endpoint 自动判断用哪种格式：anthropic 官方用 Claude 格式，其余用 OpenAI 兼容格式
        is_anthropic = 'anthropic.com' in endpoint

        try:
            if is_anthropic:
                # Claude 原生格式
                headers = {
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json',
                }
                body = {
                    'model': model,
                    'max_tokens': 64,
                    'messages': [{'role': 'user', 'content': '请回复"连接成功"两个字。'}],
                }
            else:
                # OpenAI 兼容格式
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'content-type': 'application/json',
                }
                body = {
                    'model': model,
                    'max_tokens': 64,
                    'messages': [
                        {'role': 'system', 'content': '你是一位助手，请回复"连接成功"四个字。'},
                        {'role': 'user', 'content': '你好'},
                    ],
                }

            resp = httpx.post(endpoint, headers=headers, json=body, timeout=30.0, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()

            # 提取回复
            if 'content' in data:
                # Claude 格式
                reply = data['content'][0]['text']
            elif 'choices' in data:
                # OpenAI 格式
                reply = data['choices'][0]['message']['content']
            else:
                reply = str(data)[:200]

            QMessageBox.information(self, '测试成功', f'API 连接正常！\n\nAI 回复：{reply[:200]}')
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get('error', {}).get('message', '')
            except Exception:
                detail = ''
            QMessageBox.warning(self, '测试失败',
                                f'HTTP {e.response.status_code}\n{detail}')
        except httpx.TimeoutException:
            QMessageBox.warning(self, '测试失败', '请求超时，请检查网络连接。')
        except httpx.ConnectError:
            QMessageBox.warning(self, '测试失败', '无法连接到服务器，请检查端点 URL。')
        except Exception as e:
            QMessageBox.warning(self, '测试失败', f'未知错误：{e}')
