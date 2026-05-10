#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析系统 Windows 打包脚本
用法：在 Win11 上运行 python build_windows.py
"""
import os
import sys
import subprocess
import shutil

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

print("=" * 50)
print("  数据分析系统 Windows 打包")
print("=" * 50)

# 1. 检查 Python 版本
print("\n[1/4] 检查 Python 环境...")
py_version = sys.version_info
if py_version < (3, 9):
    print("错误：需要 Python 3.9+，当前 %s.%s" % (py_version.major, py_version.minor))
    sys.exit(1)
print("  Python %s.%s.%s ✓" % (py_version.major, py_version.minor, py_version.micro))

# 2. 安装依赖
print("\n[2/4] 安装依赖...")
deps = ['PyQt5', 'pandas', 'openpyxl', 'python-docx', 'pyinstaller']
for dep in deps:
    try:
        __import__(dep.lower().replace('-', '_'))
        print("  %s ✓" % dep)
    except ImportError:
        print("  安装 %s..." % dep)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
        print("  %s ✓" % dep)

# 3. PyInstaller 打包
print("\n[3/4] 开始打包...")
spec_file = os.path.join(PROJECT_DIR, 'build_windows.spec')
cmd = [sys.executable, '-m', 'PyInstaller', '--clean', spec_file]
result = subprocess.run(cmd, cwd=PROJECT_DIR)
if result.returncode != 0:
    print("打包失败！")
    sys.exit(1)

# 4. 检查结果
print("\n[4/4] 检查输出...")
dist_dir = os.path.join(PROJECT_DIR, 'dist')
exe_path = os.path.join(dist_dir, '数据分析系统.exe')
if os.path.exists(exe_path):
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print("\n  打包完成！")
    print("  路径: %s" % exe_path)
    print("  大小: %.1f MB" % size_mb)
    print("\n  可以双击运行了 ✓")
else:
    print("  未找到 exe，检查 dist 目录:")
    for f in os.listdir(dist_dir):
        print("    %s" % f)
