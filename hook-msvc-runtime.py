"""PyInstaller runtime hook — 在 import 任何模块前预加载 MSVC 运行库 DLL。
Windows Server 2016 等系统默认不带这些 DLL，必须在 PyQt6 加载前手动加载。
"""
import sys
import os
from pathlib import Path
import ctypes

if sys.platform != 'win32':
    pass
else:
    # 确定 DLL 搜索目录
    if getattr(sys, 'frozen', False):
        _dll_dirs = [
            Path(sys._MEIPASS),
            Path(sys._MEIPASS) / 'PyQt6' / 'Qt6' / 'bin',
            Path(sys._MEIPASS) / 'PyQt6',
            Path(sys.executable).parent,
        ]
    else:
        _dll_dirs = []

    for _d in _dll_dirs:
        if _d.exists():
            try:
                os.add_dll_directory(str(_d))
            except (OSError, ValueError):
                pass

    # 关键：用 ctypes 手动预加载 MSVC 运行库，这样后续 Qt6 DLL 能找到它们
    _msvc_dlls = [
        'vcruntime140.dll',
        'vcruntime140_1.dll',
        'msvcp140.dll',
        'msvcp140_1.dll',
        'msvcp140_2.dll',
        'concrt140.dll',
    ]
    for _msvc in _msvc_dlls:
        for _dd in _dll_dirs:
            _candidate = _dd / _msvc
            if _candidate.exists():
                try:
                    ctypes.CDLL(str(_candidate))
                except Exception:
                    pass
