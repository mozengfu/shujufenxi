"""电子表格数据分析系统 - 应用入口"""
import os
import sys
import traceback
from pathlib import Path

# ── 崩溃日志（打包后双击没反应时查这个文件） ──
_CRASH_LOG = Path('~/Desktop/数据分析系统_crash.log').expanduser()


def _log_crash(exc_info):
    """将崩溃信息写入桌面日志文件"""
    try:
        with open(_CRASH_LOG, 'w', encoding='utf-8') as f:
            f.write('数据分析系统 崩溃报告\n')
            f.write('=' * 50 + '\n')
            traceback.print_exception(*exc_info, file=f)
            f.write('\n系统信息:\n')
            f.write(f'  Python: {sys.version}\n')
            f.write(f'  打包: {getattr(sys, "frozen", False)}\n')
            f.write(f'  路径: {sys.argv[0] if sys.argv else "?"}\n')
        print(f'⚠️ 崩溃日志已写入: {_CRASH_LOG}')
    except Exception:
        pass  # 写日志失败也不影响


# ── Qt 插件路径（打包后自动查找） ──
try:
    if not os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH'):
        if getattr(sys, 'frozen', False):
            base = Path(sys._MEIPASS)
            _plugin_candidates = [
                base / 'PyQt6' / 'Qt6' / 'plugins' / 'platforms',
                base / 'plugins' / 'platforms',
            ]
        else:
            try:
                import PyQt6
                base = Path(PyQt6.__file__).parent / 'Qt6'
                _plugin_candidates = [base / 'plugins' / 'platforms']
            except ImportError:
                _plugin_candidates = []
        for _pc in _plugin_candidates:
            if _pc.exists():
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(_pc)
                break
except Exception:
    _log_crash(sys.exc_info())
    raise

# ── Windows 下确保 Qt DLL 在搜索路径中 ──
if sys.platform == 'win32' and getattr(sys, 'frozen', False):
    try:
        _meipass = Path(sys._MEIPASS)
        # PyInstaller 收集 PyQt6 的多种可能路径
        _dll_dirs = [
            _meipass / 'PyQt6' / 'Qt6' / 'bin',
            _meipass / 'Qt6' / 'bin',
            _meipass / 'PyQt6',
            _meipass,
        ]
        for _qp in _dll_dirs:
            if _qp.exists():
                os.add_dll_directory(str(_qp))
        # 也加到 PATH 里（兼容性更好）
        _paths_to_add = []
        for _qp in _dll_dirs:
            if _qp.exists():
                _paths_to_add.append(str(_qp))
        if _paths_to_add:
            os.environ['PATH'] = ';'.join(_paths_to_add) + ';' + os.environ.get('PATH', '')
    except Exception:
        pass

# ── 诊断：写入环境信息到桌面（帮助排查 QtWidgets 加载失败） ──
if getattr(sys, 'frozen', False) and sys.platform == 'win32':
    try:
        _diag = Path('~/Desktop/数据分析系统_diag.txt').expanduser()
        with open(_diag, 'w', encoding='utf-8') as _f:
            _mei = Path(sys._MEIPASS)
            _f.write(f'MEIPASS: {_mei}\n')
            _f.write(f'EXE: {sys.executable}\n')
            _f.write(f'CWD: {Path.cwd()}\n')
            _f.write(f'PATH: {os.environ.get("PATH", "")[:3000]}\n')
            # 扫描常见 Qt DLL 位置
            _scan_dirs = [
                _mei / 'PyQt6' / 'Qt6' / 'bin',
                _mei / 'Qt6' / 'bin',
                _mei / 'PyQt6',
                _mei,
            ]
            for _sd in _scan_dirs:
                if _sd.exists():
                    _f.write(f'\n--- {_sd} ---\n')
                    for _dll in sorted(_sd.glob('*.dll')):
                        _f.write(f'  {_dll.name}\n')
            # 检查关键 DLL
            _key_dlls = ['Qt6Widgets.dll', 'Qt6Core.dll', 'Qt6Gui.dll']
            for _k in _key_dlls:
                _found = False
                for _sd in _scan_dirs:
                    if (_sd / _k).exists():
                        _found = True
                        _f.write(f'{_k}: FOUND in {_sd}\n')
                        break
                if not _found:
                    _f.write(f'{_k}: NOT FOUND\n')
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import QTranslator, QLibraryInfo, QLocale
from ui import MainWindow


def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationDisplayName('电子表格数据分析系统')
        app.setStyle('fusion')
        # 全局调色板 - 修复下拉菜单选中项颜色
        palette = app.palette()
        palette.setColor(palette.ColorRole.Highlight, QColor('#3498db'))
        palette.setColor(palette.ColorRole.HighlightedText, QColor('#ffffff'))
        app.setPalette(palette)
        # 全局基础字号
        font = QFont()
        font.setPointSize(13)
        app.setFont(font)
        _apply_global_style(app)

        # 加载 Qt 中文翻译（影响 QMessageBox 等内置对话框按钮）
        try:
            translator = QTranslator()
            translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
            locale = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
            if translator.load(locale, 'qt', '_', translations_path):
                app.installTranslator(translator)
        except Exception:
            pass  # 翻译文件不存在时静默忽略

        window = MainWindow()
        window.show()

        sys.exit(app.exec())
    except Exception:
        _log_crash(sys.exc_info())
        # 弹窗提示用户（仅在 GUI 就绪后可用）
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle('启动失败')
            msg.setText('应用程序启动时发生错误，详情请查看桌面上的 数据分析系统_crash.log')
            msg.exec()
        except Exception:
            pass
        sys.exit(1)


def _apply_global_style(app):
    """应用全局 QSS 样式表"""
    app.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            margin-top: 10px;
            padding: 12px 8px 8px 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: #2c3e50;
        }
        QPushButton {
            background: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px 14px;
            min-height: 24px;
        }
        QPushButton:hover {
            background: #d5dbdb;
        }
        QPushButton:pressed {
            background: #bdc3c7;
        }
        QComboBox {
            color: #2c3e50;
            background: white;
            border: 1px solid #ccd0d5;
            border-radius: 4px;
            padding: 3px 6px;
        }
        QComboBox:focus {
            border-color: #3498db;
        }
        QComboBox:on {
            background: white;
        }
        QComboBox QAbstractItemView {
            background: white;
            color: #2c3e50;
            selection-background-color: #3498db;
            selection-color: white;
            border: 1px solid #bdc3c7;
            outline: none;
        }
        QLineEdit {
            border: 1px solid #ccd0d5;
            border-radius: 4px;
            padding: 3px 6px;
            background: white;
        }
        QLineEdit:focus {
            border-color: #3498db;
        }
        QListWidget, QTableWidget {
            border: 1px solid #ccd0d5;
            border-radius: 4px;
            background: white;
        }
        QTableWidget {
            gridline-color: #e0e0e0;
            selection-background-color: #3498db;
            selection-color: white;
        }
        QHeaderView::section {
            background: #ecf0f1;
            border: 1px solid #d0d0d0;
            padding: 5px;
            font-weight: bold;
        }
        QTabWidget::pane {
            border: 1px solid #d0d0d0;
            border-radius: 4px;
        }
        QTabBar::tab {
            background: #ecf0f1;
            border: 1px solid #d0d0d0;
            padding: 8px 18px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            font-size: 13px;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom-color: white;
            font-weight: bold;
        }
        QStatusBar {
            background: #ecf0f1;
            border-top: 1px solid #d0d0d0;
            font-size: 12px;
        }
        QToolBar {
            background: #ecf0f1;
            border-bottom: 1px solid #d0d0d0;
            spacing: 8px;
            padding: 4px;
            font-size: 13px;
        }
        QToolBar QToolButton {
            font-size: 13px;
            padding: 4px 12px;
        }
        QMenuBar {
            background: #f5f5f5;
            border-bottom: 1px solid #d0d0d0;
            font-size: 13px;
        }
        QMenuBar::item:selected {
            background: #3498db;
            color: white;
        }
        QMenu {
            background: white;
            border: 1px solid #d0d0d0;
            font-size: 13px;
        }
        QMenu::item:selected {
            background: #3498db;
            color: white;
        }
        QTextEdit {
            border: 1px solid #ccd0d5;
            border-radius: 4px;
            background: white;
        }
    """)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        _log_crash(sys.exc_info())
        sys.exit(1)