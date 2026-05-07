# Phase 1 Plan: 基础设施

## 目标
添加 matplotlib 依赖 + QSettings 持久化框架 + 窗口几何恢复，为后续功能提供基础能力。

## 任务

### 1.1 添加 matplotlib 依赖
**文件**: [requirements.txt](requirements.txt)
- 追加 `matplotlib>=3.8.0`

### 1.2 QSettings 框架 + 窗口恢复
**文件**: [ui/main_window.py](ui/main_window.py)
- `MainWindow.__init__` 末尾加 `self._init_settings()`
- `_init_settings()`: 创建 `QSettings('shujufenxi', 'data-analyzer')`，调用 `restore_window_geometry()`
- `restore_window_geometry()`: 读取 settings 中的 `window_geometry` 和 `window_state` 恢复
- `closeEvent(self, event)`: 调用 `save_window_geometry()`，然后 `super().closeEvent(event)`
- `save_window_geometry()`: 保存 `self.saveGeometry()` 和 `self.saveState()`

## 成功标准
- `ruff check .` 通过
- 应用启动不报错
- 关闭后重启，窗口位置恢复到上次位置

## 验证
1. `python -m ruff check .`
2. `python -c "from ui import MainWindow; print('OK')"`
3. 手动启动：调整窗口大小→关闭→重启→确认位置恢复
