"""图表组件 - 基于 matplotlib 嵌入 PyQt6"""
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
from typing import List, Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout


# 设置中文字体
_zh_fonts = [f.name for f in fm.fontManager.ttflist
             if any(k in f.name for k in ['Songti', 'Heiti', 'Hiragino Sans GB',
                                           'WenQuanYi', 'SimHei', 'Microsoft Yahei',
                                           'PingFang', 'STHeiti', 'STSong'])]
_chosen = _zh_fonts[0] if _zh_fonts else 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = [_chosen, 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class ChartWidget(QWidget):
    """图表组件，封装 matplotlib FigureCanvas + 工具栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self._current_figure = None  # 保存当前 fig 供导出用

    def clear(self):
        """清空图表"""
        self.figure.clear()
        self.canvas.draw_idle()
        self._current_figure = None

    def get_figure(self) -> Optional[Figure]:
        """获取当前 Figure（用于导出到 Word）"""
        return self._current_figure

    def draw_histogram(self, df: pd.DataFrame, col: str):
        """绘制单列直方图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        data = df[col].dropna()
        if not np.issubdtype(data.dtype, np.number):
            ax.text(0.5, 0.5, '非数值列，无法绘制直方图',
                    ha='center', va='center', transform=ax.transAxes)
        else:
            ax.hist(data, bins=30, edgecolor='white', alpha=0.7)
            ax.set_xlabel(col)
            ax.set_ylabel('频次')
            ax.set_title(f'{col} 分布')
            ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self._current_figure = self.figure

    def draw_boxplot(self, df: pd.DataFrame, columns: List[str]):
        """绘制多列箱线图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        numeric_data = df[columns].select_dtypes(include=[np.number])
        if numeric_data.empty:
            ax.text(0.5, 0.5, '没有数值列，无法绘制箱线图',
                    ha='center', va='center', transform=ax.transAxes)
        else:
            bp = ax.boxplot([numeric_data[c].dropna() for c in numeric_data.columns],
                            labels=numeric_data.columns, patch_artist=True)
            # 着色
            for patch in bp['boxes']:
                patch.set_facecolor('#4A90D9')
                patch.set_alpha(0.6)
            ax.set_title('箱线图 - 异常值检测')
            ax.grid(True, alpha=0.3)
            # 倾斜 X 轴标签避免重叠
            for label in ax.get_xticklabels():
                label.set_rotation(30)
                label.set_ha('right')
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self._current_figure = self.figure

    def draw_bar_chart(self, data, title: str = '柱状图'):
        """绘制柱状图

        Args:
            data: pd.Series 或 pd.DataFrame（第一列为类别，第二列为值）
            title: 图表标题
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if isinstance(data, pd.DataFrame):
            if data.empty:
                ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=ax.transAxes)
            else:
                first_col = data.columns[0]
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    val_col = numeric_cols[0]
                    labels = data[first_col].astype(str).tolist()
                    values = data[val_col].values
                    bars = ax.bar(range(len(labels)), values, color='#4A90D9', alpha=0.7)
                    ax.set_xticks(range(len(labels)))
                    ax.set_xticklabels(labels, rotation=45, ha='right')
                    ax.set_xlabel(first_col)
                    ax.set_ylabel(val_col)
                    # 数值标注
                    for bar, v in zip(bars, values):
                        if not np.isnan(v):
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                                    f'{v:.1f}', ha='center', va='bottom', fontsize=8)
        elif isinstance(data, pd.Series):
            if data.empty:
                ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=ax.transAxes)
            else:
                values = data.values
                labels = data.index.astype(str).tolist()
                bars = ax.bar(range(len(labels)), values, color='#4A90D9', alpha=0.7)
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=45, ha='right')
                for bar, v in zip(bars, values):
                    if not np.isnan(v):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                                f'{v:.1f}', ha='center', va='bottom', fontsize=8)

        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self._current_figure = self.figure

    def draw_grouped_bar(self, df: pd.DataFrame, group_col: str, value_cols: List[str]):
        """绘制分组柱状图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if df.empty or not value_cols:
            ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=ax.transAxes)
            self.figure.tight_layout()
            self.canvas.draw_idle()
            return

        numeric_cols = [c for c in value_cols if np.issubdtype(df[c].dtype, np.number)]
        if not numeric_cols or group_col not in df.columns:
            ax.text(0.5, 0.5, '无法绘制分组图（缺少数值列或分组列）',
                    ha='center', va='center', transform=ax.transAxes)
            self.figure.tight_layout()
            self.canvas.draw_idle()
            return

        labels = df[group_col].astype(str).tolist()
        x = np.arange(len(labels))
        n = len(numeric_cols)
        width = 0.8 / n
        colors = ['#4A90D9', '#D94A4A', '#4AD94A', '#D9D94A', '#D94AD9']

        for i, col in enumerate(numeric_cols):
            values = df[col].values
            offset = (i - n/2 + 0.5) * width
            ax.bar(x + offset, values, width, label=col, color=colors[i % len(colors)], alpha=0.7)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_title('分组对比')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self._current_figure = self.figure
