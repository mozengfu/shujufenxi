"""Word 报告生成模块"""
import tempfile
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches
from matplotlib.figure import Figure


class WordReporter:
    """Word 报告生成器"""

    def __init__(self):
        self.doc = None

    def create_document(self) -> Document:
        """创建新文档"""
        self.doc = Document()
        return self.doc

    def add_title(self, title: str, level: int = 0) -> None:
        """添加标题"""
        if self.doc is None:
            self.create_document()

        if level == 0:
            heading = self.doc.add_heading(title, level=1)
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            self.doc.add_heading(title, level=level)

    def add_paragraph(self, text: str) -> None:
        """添加段落"""
        if self.doc is None:
            self.create_document()
        self.doc.add_paragraph(text)

    def add_table_from_df(self, df: pd.DataFrame, header: bool = True) -> None:
        """从 DataFrame 添加表格"""
        if self.doc is None:
            self.create_document()

        rows = len(df) + (1 if header else 0)
        cols = len(df.columns)

        table = self.doc.add_table(rows=rows, cols=cols)
        table.style = 'Table Grid'

        # 表头
        if header:
            for idx, col_name in enumerate(df.columns):
                cell = table.rows[0].cells[idx]
                cell.text = str(col_name)
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 数据
        for row_idx, (_, row) in enumerate(df.iterrows(), 1 if header else 0):
            for col_idx, value in enumerate(row):
                table.rows[row_idx].cells[col_idx].text = str(value) if pd.notna(value) else ''

    def add_stats_report(self, stats: pd.DataFrame, title: str = '描述性统计报告') -> None:
        """添加统计报告"""
        if self.doc is None:
            self.create_document()

        self.add_title(title, level=1)
        self.add_paragraph('')
        self.add_table_from_df(stats)
        self.add_paragraph('')

    def add_quality_report(self, quality_report: Dict[str, Any]) -> None:
        """添加数据质量报告"""
        if self.doc is None:
            self.create_document()

        self.add_title('数据质量报告', level=1)
        self.add_paragraph('')

        # 缺失值
        if quality_report.get('missing'):
            self.add_title('缺失值检测', level=2)
            missing_data = []
            for col, info in quality_report['missing'].items():
                missing_data.append({
                    '列名': col,
                    '缺失数量': info['count'],
                    '缺失百分比': f"{info['percentage']}%"
                })
            if missing_data:
                self.add_table_from_df(pd.DataFrame(missing_data))
            self.add_paragraph('')

        # 异常值
        if quality_report.get('outliers'):
            self.add_title('异常值检测', level=2)
            outlier_data = []
            for col, info in quality_report['outliers'].items():
                outlier_data.append({
                    '列名': col,
                    '异常数量': info['count'],
                    '下界': info.get('lower_bound'),
                    '上界': info.get('upper_bound')
                })
            if outlier_data:
                self.add_table_from_df(pd.DataFrame(outlier_data))
            self.add_paragraph('')

        # 重复行
        if quality_report.get('duplicates'):
            dup = quality_report['duplicates']
            self.add_title('重复行检测', level=2)
            self.add_paragraph(f"重复行数: {dup['count']} ({dup['percentage']}%)")
            if dup.get('rows'):
                self.add_paragraph(f"行号: {', '.join(map(str, dup['rows'][:50]))}")
            self.add_paragraph('')

    def add_comparison_report(self, comparison: Dict[str, Any]) -> None:
        """添加对比分析报告"""
        if self.doc is None:
            self.create_document()

        self.add_title('对比分析报告', level=1)
        self.add_paragraph('')

        if 'key_match_count' in comparison:
            self.add_paragraph(f"关键列匹配数: {comparison['key_match_count']}")
            self.add_paragraph(f"仅在表1: {comparison.get('only_in_df1_rows', 0)} 行")
            self.add_paragraph(f"仅在表2: {comparison.get('only_in_df2_rows', 0)} 行")
            self.add_paragraph(f"两表都有: {comparison.get('in_both_rows', 0)} 行")
        else:
            self.add_paragraph(f"行数差异: {comparison.get('row_diff', 0)}")

        self.add_paragraph('')

        # 列差异
        if comparison.get('only_in_df1') or comparison.get('only_in_df2'):
            self.add_title('列差异', level=2)
            if comparison.get('only_in_df1'):
                self.add_paragraph(f"仅在表1: {', '.join(comparison['only_in_df1'])}")
            if comparison.get('only_in_df2'):
                self.add_paragraph(f"仅在表2: {', '.join(comparison['only_in_df2'])}")
            self.add_paragraph('')

    def add_chart(self, fig: Figure, title: str = '图表') -> None:
        """将 matplotlib 图表嵌入文档"""
        if self.doc is None:
            self.create_document()

        # 先用临时文件保存图片，再插入
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            fig.savefig(tmp_path, dpi=150, bbox_inches='tight')
            self.add_title(title, level=1)
            self.doc.add_picture(str(tmp_path), width=Inches(5.5))
            self.add_paragraph('')
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def save(self, file_path: str) -> None:
        """保存文档"""
        if self.doc is None:
            raise ValueError("文档未创建")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(file_path)