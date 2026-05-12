# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 数据分析系统 (Windows ONEDIR 模式)

用法（必须在 Windows 上执行）：
    pip install pyinstaller PyQt5 pandas openpyxl python-docx matplotlib
    pyinstaller 数据分析系统-win.spec

打包产物：dist/数据分析系统/数据分析系统.exe

注意事项：
- Windows Server 2016 等服务器系统需要安装 MSVC 运行库
  下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe
  或在打包时添加 --win-private-assemblies 参数将运行库打包进 exe
"""
import sys
import PyQt5
from pathlib import Path

sys.setrecursionlimit(10000)

qt_plugins = str(Path(PyQt5.__file__).parent / 'Qt5' / 'plugins')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (qt_plugins, 'PyQt5/Qt5/plugins'),
    ],
    hiddenimports=[
        'PyQt5.sip',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_agg',
        'httpx',
    ],
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='数据分析系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='数据分析系统',
)
