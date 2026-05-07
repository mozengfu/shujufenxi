"""帮助对话框"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextBrowser, QPushButton, QHBoxLayout
from PyQt6.QtGui import QFont


class HelpDialog(QDialog):
    """帮助对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('帮助')
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout()

        # 标题
        title = QLabel('电子表格数据分析系统 - 使用指南')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 内容
        content = """
        <h2>功能说明</h2>

        <h3>1. 导入文件</h3>
        <p>菜单: 文件 → 导入文件<br>
        支持 .xlsx, .xls, .csv 格式。CSV 文件自动识别编码（UTF-8/GBK）。</p>

        <h3>2. 描述性统计</h3>
        <p>菜单: 分析 → 描述性统计<br>
        计算计数、求和、平均值、中位数、标准差、最大/最小值、四分位数。</p>

        <h3>3. 数据质量检测</h3>
        <p>菜单: 分析 → 数据质量检测<br>
        检测内容：缺失值、异常值（IQR 方法）、重复行、格式问题。</p>

        <h3>4. 对比分析</h3>
        <p>菜单: 分析 → 对比分析<br>
        选择第二个文件进行对比，查看列差异和行差异。</p>

        <h3>5. 多表合并</h3>
        <p>菜单: 分析 → 多表合并<br>
        支持两种模式：<br>
        - 按关键列合并（类似 VLOOKUP）<br>
        - 行追加合并（相同结构表垂直拼接）</p>

        <h3>6. 导出 Excel</h3>
        <p>菜单: 文件 → 导出 Excel<br>
        将当前数据导出为带格式的 Excel 文件。</p>

        <h3>7. 导出 Word 报告</h3>
        <p>菜单: 文件 → 导出 Word 报告<br>
        生成包含统计结果和数据质量报告的 Word 文档。</p>

        <h2>键盘快捷键</h2>
        <table>
        <tr><td>Ctrl+I</td><td>导入文件</td></tr>
        <tr><td>Ctrl+E</td><td>导出 Excel</td></tr>
        <tr><td>Ctrl+W</td><td>导出 Word 报告</td></tr>
        <tr><td>Ctrl+1</td><td>描述性统计</td></tr>
        <tr><td>Ctrl+2</td><td>数据质量检测</td></tr>
        <tr><td>Ctrl+3</td><td>对比分析</td></tr>
        <tr><td>Ctrl+M</td><td>多表合并</td></tr>
        <tr><td>F1</td><td>显示帮助</td></tr>
        </table>

        <h2>注意事项</h2>
        <ul>
        <li>大文件导入可能需要几秒钟</li>
        <li>异常值检测使用 IQR 方法（1.5倍四分位距）</li>
        <li>合并前请确保关键列数据一致</li>
        </ul>
        """

        browser = QTextBrowser()
        browser.setHtml(content)
        browser.setOpenExternalLinks(True)
        layout.addWidget(browser)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)