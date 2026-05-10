# Windows 打包与部署指南

## 问题：天翼云电脑 (Windows Server 2016) DLL 加载失败

错误信息：
```
ImportError: DLL load failed while importing QtWidgets: 找不到指定的模块。
```

### 根因

1. **原 spec 文件仅支持 macOS** — 使用了 `BUNDLE`（创建 `.app`）和 `icon.icns`
2. **Windows Server 2016 缺少 MSVC 运行库** — PyQt6 的 Qt6 DLL 依赖 Visual C++ 2015-2022 运行库

## 打包步骤（必须在 Windows 上执行）

> PyInstaller 不支持跨平台编译，macOS 上打包的产物无法在 Windows 运行。

### 1. 准备 Windows 环境

```powershell
# 安装 Python（推荐 3.10-3.13，勾选 "Add to PATH"）
# 验证
python --version

# 安装依赖
pip install PyQt6 pandas openpyxl python-docx matplotlib pyinstaller
```

### 2. 获取代码

```powershell
# 从 git 仓库克隆
git clone <仓库地址>
cd shujufenxi

# 或直接复制项目文件夹
```

### 3. 执行打包

```powershell
# 使用 Windows 专用 spec 文件
pyinstaller 数据分析系统-win.spec
```

产物位置：`dist/数据分析系统/数据分析系统.exe`

### 4. 部署到天翼云电脑

将整个 `dist/数据分析系统/` 目录复制到云电脑（包含所有子文件和 DLL）。

## 解决 DLL 加载失败的两种方案

### 方案 A：安装 MSVC 运行库（推荐，最简单）

在云电脑上下载并安装：
- 下载：https://aka.ms/vs/17/release/vc_redist.x64.exe
- 双击安装，重启后运行 exe

### 方案 B：将运行库打包进 exe

在 Windows 打包时添加参数：

```powershell
# 方式 1：使用 --win-private-assemblies
pyinstaller --win-private-assemblies 数据分析系统-win.spec

# 方式 2：手动收集 MSVC DLL（如果方式 1 不生效）
# 在 spec 文件的 Analysis 中添加：
#   binaries=[
#       ('C:/Windows/System32/msvcp140.dll', '.'),
#       ('C:/Windows/System32/vcruntime140.dll', '.'),
#       ('C:/Windows/System32/vcruntime140_1.dll', '.'),
#   ],
```

## 打包后验证

打包完成后，检查 `dist/数据分析系统/` 目录中应包含：

- `数据分析系统.exe` — 主程序
- `PyQt6/Qt6/plugins/platforms/qwindows.dll` — Windows 平台插件（必须有）
- `PyQt6/Qt6/bin/Qt6Widgets.dll` — Qt 核心 DLL（必须有）
- `PyQt6/Qt6/bin/Qt6Gui.dll`
- `PyQt6/Qt6/bin/Qt6Core.dll`
- `_internal/` 目录 — Python 字节码和依赖

## 常见错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `DLL load failed while importing QtWidgets` | 缺 MSVC 运行库 或 qwindows.dll 缺失 | 安装 vc_redist 或检查 plugins/platforms 目录 |
| `could not find or load the Qt platform plugin "windows"` | qwindows.dll 位置不对 | 检查 `PyQt6/Qt6/plugins/platforms/` 是否存在 |
| 双击无反应 | 使用了 console=False，崩溃不可见 | 临时改用 `pyinstaller --console 数据分析系统-win.spec` 查看错误 |
