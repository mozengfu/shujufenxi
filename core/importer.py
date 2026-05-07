"""表格导入模块，支持 Excel 和 CSV 文件"""
import pandas as pd
from pathlib import Path
from typing import Optional


class TableImporter:
    """表格导入器，支持 .xlsx, .xls, .csv 格式"""

    SUPPORTED_FORMATS = ['.xlsx', '.xls', '.csv']

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.file_path: Optional[Path] = None
        self.file_type: Optional[str] = None

    def import_file(self, file_path: str) -> pd.DataFrame:
        """导入文件并返回 DataFrame"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的格式: {suffix}，支持: {self.SUPPORTED_FORMATS}")

        self.file_path = path
        self.file_type = suffix

        if suffix == '.csv':
            try:
                self.df = pd.read_csv(file_path, encoding='utf-8-sig')
            except UnicodeDecodeError:
                self.df = pd.read_csv(file_path, encoding='gbk')
        else:
            self.df = pd.read_excel(file_path)

        return self.df

    def get_info(self) -> dict:
        """获取导入文件的信息"""
        if self.df is None:
            return {}

        return {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'column_names': list(self.df.columns),
            'file_path': str(self.file_path) if self.file_path else None,
            'file_type': self.file_type,
            'memory_usage': self.df.memory_usage(deep=True).sum(),
            'dtypes': self.df.dtypes.to_dict()
        }

    def preview(self, rows: int = 5) -> pd.DataFrame:
        """预览数据前 N 行"""
        if self.df is None:
            raise ValueError("请先导入文件")
        return self.df.head(rows)