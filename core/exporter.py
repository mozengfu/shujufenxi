"""Excel 导出模块"""
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


class ExcelExporter:
    """Excel 导出器"""

    def __init__(self):
        self.header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.header_font = Font(color="FFFFFF", bold=True)
        self.center_align = Alignment(horizontal="center", vertical="center")

    def export_dataframe(self, df: pd.DataFrame, file_path: str, sheet_name: str = 'Sheet1') -> None:
        """导出 DataFrame 到 Excel"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        df.to_excel(file_path, sheet_name=sheet_name, index=False, engine='openpyxl')

    def export_with_format(self, df: pd.DataFrame, file_path: str, sheet_name: str = 'Sheet1') -> None:
        """带格式导出 DataFrame 到 Excel"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        # 应用格式
        from openpyxl import load_workbook
        wb = load_workbook(file_path)
        ws = wb[sheet_name]

        # 表头格式
        for cell in ws[1]:
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.alignment = self.center_align

        # 列宽自适应
        for col_idx, column in enumerate(df.columns, 1):
            col_data = df[column].astype(str)
            max_len = max(
                len(str(column)),
                col_data.str.len().max() if len(df) > 0 else 0
            )
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 50)

        wb.save(file_path)

    def export_stats_report(self, stats: pd.DataFrame, file_path: str, title: str = '描述性统计报告') -> None:
        """导出统计报告"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 标题
            pd.DataFrame({'报告': [title]}).to_excel(writer, sheet_name='统计', index=False, startrow=0)

            # 统计数据
            stats.to_excel(writer, sheet_name='统计', index=True, startrow=2)

        # 应用格式
        from openpyxl import load_workbook
        wb = load_workbook(file_path)
        ws = wb['统计']

        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:D1')

        for cell in ws[3]:
            cell.fill = self.header_fill
            cell.font = self.header_font
            cell.alignment = self.center_align

        wb.save(file_path)

    def export_quality_report(self, quality_report: Dict[str, Any], file_path: str) -> None:
        """导出数据质量报告"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 缺失值
            if quality_report.get('missing'):
                missing_data = []
                for col, info in quality_report['missing'].items():
                    missing_data.append({
                        '列名': col,
                        '缺失数量': info['count'],
                        '缺失百分比': f"{info['percentage']}%",
                        '行号': ', '.join(map(str, info['rows'][:20]))
                    })
                pd.DataFrame(missing_data).to_excel(writer, sheet_name='缺失值', index=False)

            # 异常值
            if quality_report.get('outliers'):
                outlier_data = []
                for col, info in quality_report['outliers'].items():
                    outlier_data.append({
                        '列名': col,
                        '异常数量': info['count'],
                        '下界': info.get('lower_bound'),
                        '上界': info.get('upper_bound'),
                        '值': ', '.join(map(str, info['values'][:10]))
                    })
                pd.DataFrame(outlier_data).to_excel(writer, sheet_name='异常值', index=False)

            # 重复行
            if quality_report.get('duplicates'):
                dup = quality_report['duplicates']
                pd.DataFrame([{
                    '重复行数': dup['count'],
                    '占比': f"{dup['percentage']}%",
                    '行号': ', '.join(map(str, dup['rows'][:20]))
                }]).to_excel(writer, sheet_name='重复行', index=False)

        # 应用格式
        from openpyxl import load_workbook
        wb = load_workbook(file_path)

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for cell in ws[1]:
                cell.fill = self.header_fill
                cell.font = self.header_font

        wb.save(file_path)

    def export_comparison(self, comparison_result: Dict[str, Any], file_path: str) -> None:
        """导出对比分析结果"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # 基本对比信息
            comparison_df = pd.DataFrame([
                {'对比项': 'df1行数', 'df2行数': comparison_result.get('df1_rows', comparison_result.get('row_diff', 0))},
                {'对比项': 'df2行数', 'df2行数': comparison_result.get('df2_rows', '')},
                {'对比项': '结果行数', 'df2行数': comparison_result.get('result_rows', '')},
            ])
            comparison_df.to_excel(writer, sheet_name='对比结果', index=False)

            # 列差异
            col_diff = []
            if comparison_result.get('only_in_df1'):
                col_diff.append({'类型': '仅在表1', '列名': ', '.join(comparison_result['only_in_df1'])})
            if comparison_result.get('only_in_df2'):
                col_diff.append({'类型': '仅在表2', '列名': ', '.join(comparison_result['only_in_df2'])})
            if col_diff:
                pd.DataFrame(col_diff).to_excel(writer, sheet_name='列差异', index=False)

        # 应用格式
        from openpyxl import load_workbook
        wb = load_workbook(file_path)

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for cell in ws[1]:
                cell.fill = self.header_fill
                cell.font = self.header_font

        wb.save(file_path)