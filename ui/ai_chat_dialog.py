"""AI 对话对话框 — 多轮对话界面"""
import html
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                              QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont

import pandas as pd

from core import AISummarizer


class AIChatDialog(QDialog):
    """AI 多轮对话对话框"""

    def __init__(self, parent=None, df: pd.DataFrame = None):
        super().__init__(parent)
        self.setWindowTitle('AI 对话')
        self.resize(700, 600)
        self.df = df
        self.message_history = []
        self.chat_html = ''
        self.settings = QSettings('shujufenxi', 'settings')

        # 初始化 AISummarizer
        api_key = self.settings.value('ai_api_key', '')
        model = self.settings.value('ai_model', 'claude-sonnet-4-6')
        endpoint = self.settings.value('ai_endpoint', 'https://api.anthropic.com/v1/messages')
        self.summarizer = AISummarizer(api_key=api_key, model=model, endpoint=endpoint)

        # 构建系统提示（如果有数据）
        self.system_prompt = ''
        if df is not None:
            stats = self._safe_stats(df)
            quality = self._safe_quality(df)
            self.system_prompt = self.summarizer._build_chat_system_prompt(df, stats, quality)

        self.init_ui()

    def _safe_stats(self, df):
        try:
            from core import DataAnalyzer
            return DataAnalyzer().descriptive_stats(df)
        except Exception:
            return None

    def _safe_quality(self, df):
        try:
            from core import DataAnalyzer
            return DataAnalyzer().full_quality_report(df)
        except Exception:
            return None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)

        # 顶部栏
        top = QHBoxLayout()
        title = QLabel('与 AI 讨论你的数据')
        title.setFont(QFont('', 11, QFont.Bold))
        top.addWidget(title)
        top.addStretch()

        self.new_btn = QPushButton('新对话')
        self.new_btn.clicked.connect(self.new_chat)
        top.addWidget(self.new_btn)
        layout.addLayout(top)

        # 聊天区
        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setStyleSheet("""
            QTextEdit {
                background: #fafafa;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 13px;
                padding: 8px;
            }
        """)
        self.chat_view.setPlaceholderText('发送消息开始对话...')
        layout.addWidget(self.chat_view, stretch=1)

        # 输入区
        self.input_edit = QTextEdit()
        self.input_edit.setFixedHeight(60)
        self.input_edit.setPlaceholderText('输入您的问题... 按 Enter 发送，Ctrl+Enter 换行')
        self.input_edit.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 13px;
                padding: 6px;
            }
        """)
        self.input_edit.installEventFilter(self)
        layout.addWidget(self.input_edit)

        # 按钮栏
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        self.send_btn = QPushButton('发送')
        self.send_btn.setObjectName('primary')
        self.send_btn.clicked.connect(self.send_message)
        btn_bar.addWidget(self.send_btn)

        self.close_btn = QPushButton('关闭')
        self.close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(self.close_btn)
        layout.addLayout(btn_bar)

        self.setLayout(layout)

    def eventFilter(self, obj, event):
        if obj is self.input_edit and event.type() == 6:  # KeyPress
            key_event = event
            if key_event.key() == Qt.Key_Return and (
                key_event.modifiers() & Qt.ControlModifier
            ):
                # Ctrl+Enter: insert newline
                return False
            if key_event.key() == Qt.Key_Return:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def _update_chat_view(self):
        self.chat_view.setHtml(self.chat_html)
        # 滚动到底部
        vbar = self.chat_view.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def append_user_message(self, text: str):
        escaped = html.escape(text).replace('\n', '<br>')
        self.chat_html += (
            f'<div style="text-align: right; margin: 6px 0;">'
            f'<span style="background: #d4e6ff; color: #1a1a1a; '
            f'padding: 8px 14px; border-radius: 14px 4px 4px 14px; '
            f'display: inline-block; max-width: 80%;">'
            f'{escaped}</span></div>'
        )
        self._update_chat_view()

    def append_ai_message(self, text: str):
        escaped = html.escape(text).replace('\n', '<br>')
        self.chat_html += (
            f'<div style="text-align: left; margin: 6px 0;">'
            f'<span style="background: #e8e8e8; color: #1a1a1a; '
            f'padding: 8px 14px; border-radius: 4px 14px 14px 4px; '
            f'display: inline-block; max-width: 80%;">'
            f'{escaped}</span></div>'
        )
        self._update_chat_view()

    def show_typing_indicator(self):
        self.chat_html += (
            '<div style="text-align: left; margin: 6px 0;">'
            '<span style="background: #e8e8e8; color: #888; '
            'padding: 8px 14px; border-radius: 4px 14px 14px 4px; '
            'display: inline-block; max-width: 80%;">'
            'AI 正在思考...</span></div>'
        )
        self._update_chat_view()

    def remove_typing_indicator(self):
        # 移除最后一条 typing 消息
        marker = 'AI 正在思考...'
        idx = self.chat_html.rfind(marker)
        if idx != -1:
            # 从 typing 的 div 开头截取并删除
            start = self.chat_html.rfind('<div style="text-align: left;', 0, idx)
            if start != -1:
                end = self.chat_html.find('</div>', idx) + len('</div>')
                self.chat_html = self.chat_html[:start] + self.chat_html[end:]
                self._update_chat_view()

    def send_message(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        # 检查 API Key
        if not self.summarizer.api_key:
            QMessageBox.warning(self, '未配置', '请先在"设置 → AI 配置"中配置 API Key 和模型。')
            return

        self.input_edit.clear()
        self.append_user_message(text)
        self.message_history.append({'role': 'user', 'content': text})

        # 禁用输入
        self.send_btn.setEnabled(False)
        self.send_btn.setText('发送中...')
        self.input_edit.setEnabled(False)
        self.show_typing_indicator()

        # 调用 API
        response = self.summarizer.chat(text, self.message_history[:-1], self.system_prompt)
        self.message_history.append({'role': 'assistant', 'content': response})

        self.remove_typing_indicator()
        self.append_ai_message(response)

        # 恢复输入
        self.send_btn.setEnabled(True)
        self.send_btn.setText('发送')
        self.input_edit.setEnabled(True)

    def new_chat(self):
        self.message_history.clear()
        self.chat_html = ''
        self.chat_view.clear()
