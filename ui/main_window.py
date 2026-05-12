"""主窗口模块"""
from PyQt5.QtWidgets import (QMainWindow, QToolBar, QAction,
                              QFileDialog, QMessageBox, QTabWidget,
                              QLineEdit, QTextEdit, QApplication)
from PyQt5.QtGui import QKeySequence, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt, QSettings
import pandas as pd

from core import TableImporter, DataAnalyzer, TableMerger, ExcelExporter, WordReporter
from .import_dialog import ImportDialog
from .analysis_panel import AnalysisPanel
from .report_dialog import ReportDialog
from .merge_dialog import MergeDialog
from .help_dialog import HelpDialog
from .clean_dialog import CleanDialog
from .column_calc_dialog import ColumnCalcDialog
from .report_designer import ReportDesigner


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.importer = TableImporter()
        self.analyzer = DataAnalyzer()
        self.merger = TableMerger()
        self.exporter = ExcelExporter()
        self.reporter = WordReporter()

        self.current_df: pd.DataFrame = None
        self.last_comparison: dict = {}
        self.loaded_dfs: dict = {}

        self.init_ui()
        self._init_settings()

    def _init_settings(self):
        """初始化 QSettings 并恢复窗口状态"""
        self.settings = QSettings('shujufenxi', 'data-analyzer')
        self.restore_window_geometry()
        self.update_recent_menu()

    def save_window_geometry(self):
        """保存窗口几何和状态"""
        self.settings.setValue('window_geometry', self.saveGeometry())
        self.settings.setValue('window_state', self.saveState())

    def restore_window_geometry(self):
        """恢复窗口几何和状态"""
        geometry = self.settings.value('window_geometry')
        state = self.settings.value('window_state')
        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)

    def update_recent_menu(self):
        """从 QSettings 加载最近文件列表并更新菜单"""
        self.recent_menu.clear()
        files = self.settings.value('recent_files', [])
        if isinstance(files, list):
            files = [f for f in files if f]
        else:
            files = []

        if not files:
            self.recent_menu.setVisible(False)
            return

        self.recent_menu.setVisible(True)
        for path in files:
            name = path.split('/')[-1] if '/' in path else path
            action = QAction(name, self)
            action.setData(path)
            action.triggered.connect(lambda checked, p=path: self._open_recent_file(p))
            self.recent_menu.addAction(action)

    def _add_recent_file(self, file_path: str):
        """添加文件到最近文件列表"""
        files = self.settings.value('recent_files', [])
        if not isinstance(files, list):
            files = []
        if file_path in files:
            files.remove(file_path)
        files.insert(0, file_path)
        files = files[:10]
        self.settings.setValue('recent_files', files)
        self.update_recent_menu()

    def _open_recent_file(self, file_path: str):
        """打开最近文件列表中的文件"""
        try:
            self.current_df = self.importer.import_file(file_path)
            info = self.importer.get_info()
            info['file_path'] = file_path
            self.statusBar().showMessage(f'已导入: {info["rows"]} 行 x {info["columns"]} 列')
            self.analysis_panel.update_data(self.current_df, info)
            QMessageBox.information(self, '成功', f'成功导入 {info["rows"]} 行 x {info["columns"]} 列')
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

    def closeEvent(self, event):
        """关闭事件 - 保存窗口状态"""
        self.save_window_geometry()
        super().closeEvent(event)

    def _edit_on_focused(self, action: str):
        """将编辑操作路由到当前聚焦的文本控件"""
        widget = QApplication.focusWidget()
        if isinstance(widget, QLineEdit):
            if action == 'undo':
                widget.undo()
            elif action == 'redo':
                widget.redo()
            elif action == 'cut':
                widget.cut()
            elif action == 'copy':
                widget.copy()
            elif action == 'paste':
                widget.paste()
            elif action == 'delete':
                widget.backspace() if hasattr(widget, 'backspace') else widget.clear()
            elif action == 'select_all':
                widget.selectAll()
        elif isinstance(widget, QTextEdit):
            if action == 'undo':
                widget.undo()
            elif action == 'redo':
                widget.redo()
            elif action == 'cut':
                widget.cut()
            elif action == 'copy':
                widget.copy()
            elif action == 'paste':
                widget.paste()
            elif action == 'delete':
                widget.textCursor().removeSelectedText()
            elif action == 'select_all':
                widget.selectAll()

    def _toggle_maximized(self):
        """切换窗口最大化/正常状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle('电子表格数据分析系统')
        self.setGeometry(100, 100, 1200, 800)

        self.create_menu()
        self.create_toolbar()

        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        self.analysis_panel = AnalysisPanel(self)
        self.central_widget.addTab(self.analysis_panel, '数据分析')

        self.statusBar().showMessage('就绪')

        # 启用拖放支持
        self.setAcceptDrops(True)

    def handle_file_drop(self, event: QDropEvent):
        """处理文件拖放"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(('.xlsx', '.xls', '.csv')):
                files.append(file_path)

        if files:
            file_path = files[0]
            try:
                self.current_df = self.importer.import_file(file_path)
                info = self.importer.get_info()
                info['file_path'] = file_path
                self.statusBar().showMessage(f'已导入: {info["rows"]} 行 x {info["columns"]} 列')
                self.analysis_panel.update_data(self.current_df, info)
                self._add_recent_file(file_path)
                QMessageBox.information(self, '成功', f'成功导入 {info["rows"]} 行 x {info["columns"]} 列')
            except Exception as e:
                QMessageBox.critical(self, '错误', str(e))

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖动进入事件"""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith(('.xlsx', '.xls', '.csv')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        self.handle_file_drop(event)

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')

        import_action = QAction('导入文件', self)
        import_action.setShortcut(QKeySequence('Ctrl+I'))
        import_action.triggered.connect(self.import_file)
        file_menu.addAction(import_action)

        export_excel_action = QAction('导出 Excel', self)
        export_excel_action.setShortcut(QKeySequence('Ctrl+E'))
        export_excel_action.triggered.connect(self.export_excel)
        file_menu.addAction(export_excel_action)

        export_word_action = QAction('导出 Word 报告', self)
        export_word_action.setShortcut(QKeySequence('Ctrl+W'))
        export_word_action.triggered.connect(self.export_word)
        file_menu.addAction(export_word_action)

        file_menu.addSeparator()

        custom_report_action = QAction('自定义报表', self)
        custom_report_action.triggered.connect(self.custom_report)
        file_menu.addAction(custom_report_action)

        file_menu.addSeparator()

        self.recent_menu = file_menu.addMenu('最近文件')
        self.recent_menu.setVisible(False)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单（macOS 原生菜单，覆盖默认英文菜单）
        edit_menu = menubar.addMenu('编辑')

        undo_action = QAction('撤销', self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(lambda: self._edit_on_focused('undo'))
        edit_menu.addAction(undo_action)

        redo_action = QAction('重做', self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(lambda: self._edit_on_focused('redo'))
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction('剪切', self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(lambda: self._edit_on_focused('cut'))
        edit_menu.addAction(cut_action)

        copy_action = QAction('复制', self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(lambda: self._edit_on_focused('copy'))
        edit_menu.addAction(copy_action)

        paste_action = QAction('粘贴', self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(lambda: self._edit_on_focused('paste'))
        edit_menu.addAction(paste_action)

        delete_action = QAction('删除', self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(lambda: self._edit_on_focused('delete'))
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        select_all_action = QAction('全选', self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(lambda: self._edit_on_focused('select_all'))
        edit_menu.addAction(select_all_action)

        # 数据菜单
        data_menu = menubar.addMenu('数据')

        merge_action = QAction('多表合并', self)
        merge_action.setShortcut(QKeySequence('Ctrl+M'))
        merge_action.triggered.connect(self.merge_tables)
        data_menu.addAction(merge_action)

        clean_action = QAction('数据清洗', self)
        clean_action.triggered.connect(self.clean_data)
        data_menu.addAction(clean_action)

        calc_action = QAction('列计算', self)
        calc_action.triggered.connect(self.calc_column)
        data_menu.addAction(calc_action)

        # 窗口菜单（macOS 原生菜单，覆盖默认英文菜单）
        window_menu = menubar.addMenu('窗口')

        minimize_action = QAction('最小化', self)
        minimize_action.triggered.connect(self.showMinimized)
        window_menu.addAction(minimize_action)

        zoom_action = QAction('缩放', self)
        zoom_action.triggered.connect(self._toggle_maximized)
        window_menu.addAction(zoom_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')

        help_action = QAction('使用指南', self)
        help_action.setShortcut(QKeySequence('F1'))
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        import_btn = QAction('导入', self)
        import_btn.triggered.connect(self.import_file)
        toolbar.addAction(import_btn)

        export_btn = QAction('导出', self)
        export_btn.triggered.connect(self.export_excel)
        toolbar.addAction(export_btn)

    def import_file(self):
        """导入文件"""
        dialog = ImportDialog(self)
        if dialog.exec_():
            file_path = dialog.selected_file
            try:
                self.current_df = self.importer.import_file(file_path)
                info = self.importer.get_info()
                info['file_path'] = file_path
                self.statusBar().showMessage(f'已导入: {info["rows"]} 行 x {info["columns"]} 列')
                self.analysis_panel.update_data(self.current_df, info)
                self._add_recent_file(file_path)
                QMessageBox.information(self, '成功', f'成功导入 {info["rows"]} 行 x {info["columns"]} 列')
            except Exception as e:
                QMessageBox.critical(self, '错误', str(e))

    def merge_tables(self):
        """多表合并"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return

        dialog = MergeDialog(self, initial_df=self.current_df)
        if dialog.exec_():
            result = dialog.get_result()
            try:
                if result['mode'] == 'key':
                    merged = self.merger.merge_by_key(
                        [t['df'] for t in result['tables']],
                        result['key_column'],
                        result.get('how', 'inner')
                    )
                else:
                    merged = self.merger.append_rows([t['df'] for t in result['tables']])

                self.current_df = merged
                info = {'rows': len(merged), 'columns': len(merged.columns), 'file_path': '合并结果'}
                self.analysis_panel.update_data(merged, info)
                QMessageBox.information(self, '成功', f'合并完成: {info["rows"]} 行 x {info["columns"]} 列')
            except Exception as e:
                QMessageBox.critical(self, '错误', str(e))

    def clean_data(self):
        """数据清洗"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return

        dialog = CleanDialog(self, initial_df=self.current_df)
        if dialog.exec_():
            result = dialog.get_result()
            if result is not None:
                self.current_df = result
                info = {'rows': len(result), 'columns': len(result.columns), 'file_path': '清洗结果'}
                self.analysis_panel.update_data(result, info)
                QMessageBox.information(self, '成功', f'清洗完成: {info["rows"]} 行 x {info["columns"]} 列')

    def calc_column(self):
        """列计算"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return

        dialog = ColumnCalcDialog(self, df=self.current_df)
        if dialog.exec_():
            result = dialog.get_result()
            if result is not None:
                self.current_df = result
                info = {'rows': len(result), 'columns': len(result.columns), 'file_path': '计算结果'}
                self.analysis_panel.update_data(result, info)
                QMessageBox.information(self, '成功', f'已添加新列，当前 {info["columns"]} 列')

    def export_excel(self):
        """导出 Excel"""
        # 优先导出分析结果，其次导出原数据
        export_df = None
        if self.analysis_panel.last_result_df is not None and not self.analysis_panel.last_result_df.empty:
            export_df = self.analysis_panel.last_result_df
        elif self.current_df is not None:
            export_df = self.current_df

        if export_df is None:
            QMessageBox.warning(self, '警告', '没有可导出的数据')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出 Excel', '', 'Excel 文件 (*.xlsx)'
        )
        if file_path:
            try:
                self.exporter.export_with_format(export_df, file_path, agg_items=self.analysis_panel.agg_items)
                QMessageBox.information(self, '成功', f'已导出到 {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', str(e))

    def custom_report(self):
        """自定义报表"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '请先导入数据')
            return

        dialog = ReportDesigner(self, df=self.current_df)
        dialog.exec_()

    def export_word(self):
        """导出 Word 报告"""
        if self.current_df is None:
            QMessageBox.warning(self, '警告', '没有可导出的数据')
            return

        dialog = ReportDialog(self)
        if dialog.exec_():
            file_path = dialog.selected_file
            try:
                self.reporter.create_document()
                self.reporter.add_title('数据分析报告', level=0)

                if dialog.include_stats:
                    stats = self.analyzer.descriptive_stats(self.current_df)
                    self.reporter.add_stats_report(stats)

                if dialog.include_quality:
                    report = self.analyzer.full_quality_report(self.current_df)
                    self.reporter.add_quality_report(report)

                if self.last_comparison:
                    self.reporter.add_comparison_report(self.last_comparison)

                # 嵌入图表（如果有）
                fig = self.analysis_panel.chart_figure
                if fig is not None:
                    self.reporter.add_chart(fig, title='分析图表')

                self.reporter.save(file_path)
                QMessageBox.information(self, '成功', f'已导出到 {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', str(e))

    def show_help(self):
        """显示帮助"""
        dialog = HelpDialog(self)
        dialog.exec_()

    def show_about(self):
        """显示关于"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                                      QPushButton, QLabel)
        from PyQt5.QtGui import QFont
        dialog = QDialog(self)
        dialog.setWindowTitle('关于')
        dialog.setFixedSize(420, 280)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 20)

        title = QLabel('电子表格数据分析系统')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        ver = QLabel('版本 2.0')
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet('color: #7f8c8d; margin-bottom: 10px;')
        layout.addWidget(ver)

        desc = QLabel(
            '用于导入 Excel/CSV 表格，进行描述性统计、数据质量检测、\n'
            '对比分析、多表合并、数据清洗，输出 Excel 报表和 Word 报告。'
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet('color: #2c3e50; margin: 10px 0;')
        layout.addWidget(desc)

        tech = QLabel('技术栈: PyQt5 · pandas · openpyxl · python-docx · matplotlib')
        tech.setAlignment(Qt.AlignCenter)
        tech.setStyleSheet('color: #95a5a6; font-size: 11px;')
        layout.addWidget(tech)

        layout.addStretch()

        btn = QPushButton('确定')
        btn.setObjectName('primary')
        btn.clicked.connect(dialog.accept)
        btn.setFixedWidth(100)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)
        dialog.exec_()