# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 数据分析系统 (ONEDIR 模式)

文件分散在 .app 包内，不被 macOS 安全机制拦截。
"""
import sys
import PyQt5
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

sys.setrecursionlimit(10000)

qt_plugins = str(Path(PyQt5.__file__).parent / 'Qt5' / 'plugins')
if not Path(qt_plugins).exists():
    # Conda 环境：插件在 conda prefix 下
    qt_plugins = '/opt/anaconda3/plugins'

# 强制打包完整的 httpx 模块（hiddenimports 不够用）
httpx_datas, httpx_bins, httpx_imports = collect_all('httpx')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (qt_plugins, 'plugins'),
    ] + httpx_datas,
    hiddenimports=[
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_agg',
    ] + httpx_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6', 'PySide6', 'PySide2', 'PySide',
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'tensorboard',
        'transformers', 'datasets', 'tokenizers',
        'sklearn', 'scipy',
        'statsmodels', 'patsy',
        'bokeh', 'plotly', 'altair', 'panel',
        'dask', 'distributed', 'cloudpickle',
        'pyarrow', 'fastparquet',
        'skimage', 'nltk', 'soundfile',
        'numba', 'llvmlite',
        'h5py', 'tables',
        'boto3', 'botocore', 's3fs', 'gcsfs',
        'fsspec',
        'sphinx', 'docutils',
        'pygments', 'babel',
        'zmq', 'cryptography', 'bcrypt', 'nacl',
        'sqlalchemy', 'alembic',
        'IPython', 'jupyter', 'jupyterlab', 'notebook', 'nbconvert',
        'tkinter', 'Tkinter', 'tk', '_tkinter',
        'rich', 'pydantic',
        'pip', 'wheel',
        'Cython', 'cx_Freeze', 'py2exe',
        'psutil',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# ONEDIR 模式：exe 只是启动器，不嵌入数据
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='数据分析系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 收集所有二进制和数据文件到目录
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='数据分析系统',
)

app = BUNDLE(
    coll,
    name='数据分析系统.app',
    icon='icon.icns',
    bundle_identifier='com.dataanalyzer.app',
    info_plist={
        'CFBundleDisplayName': '数据分析系统',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
)
