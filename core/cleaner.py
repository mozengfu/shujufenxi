"""数据清洗模块"""
import pandas as pd
import numpy as np
from typing import List, Any, Optional


class DataCleaner:
    """数据清洗器"""

    def convert_type(self, df: pd.DataFrame, col: str, to_type: str) -> pd.DataFrame:
        """
        数据类型转换

        Args:
            df: 数据框
            col: 列名
            to_type: 目标类型 ('int', 'float', 'str', 'date', 'datetime')

        Returns:
            转换后的数据框
        """
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

        result = df.copy()

        if to_type == 'int':
            numeric_data = pd.to_numeric(result[col], errors='coerce')
            # 如果有空值，转为 float 以保留空值（int 无法表示空值）
            if numeric_data.isna().any():
                result[col] = numeric_data.astype(np.float64)
            else:
                result[col] = numeric_data.astype(np.int64)
        elif to_type == 'float':
            result[col] = pd.to_numeric(result[col], errors='coerce')
        elif to_type == 'str':
            result[col] = result[col].astype(str)
        elif to_type == 'date':
            result[col] = pd.to_datetime(result[col], errors='coerce')
        elif to_type == 'datetime':
            result[col] = pd.to_datetime(result[col], errors='coerce')

        return result

    def split_column(
        self,
        df: pd.DataFrame,
        col: str,
        sep: str,
        new_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        按分隔符拆分列

        Args:
            df: 数据框
            col: 要拆分的列名
            sep: 分隔符
            new_cols: 新列名列表（可选）

        Returns:
            拆分后的数据框
        """
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

        result = df.copy()

        # 拆分列（保留 NaN 行）
        mask = result[col].notna()
        if mask.any():
            split_data = result.loc[mask, col].astype(str).str.split(sep, expand=True)
        else:
            # 全为 NaN，生成空结果
            split_data = pd.DataFrame()

        num_parts = split_data.shape[1] if not split_data.empty else 0

        # 生成新列名
        if new_cols is None:
            base_name = col.replace('_', '').replace(' ', '')
            new_cols = [f'{base_name}_{i+1}' for i in range(num_parts)]

        # 确保 new_cols 长度足够
        while len(new_cols) < num_parts:
            new_cols.append(f'{col}_part{len(new_cols)+1}')

        # 删除原列，添加新列
        result = result.drop(columns=[col])
        for i, new_col in enumerate(new_cols[:num_parts]):
            result[new_col] = split_data[i]

        return result

    def add_prefix_suffix(
        self,
        df: pd.DataFrame,
        col: str,
        prefix: str = '',
        suffix: str = ''
    ) -> pd.DataFrame:
        """
        添加前缀/后缀

        Args:
            df: 数据框
            col: 列名
            prefix: 前缀
            suffix: 后缀

        Returns:
            处理后的数据框
        """
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

        result = df.copy()
        # 保留 NaN，只对非空值操作
        mask = result[col].notna()
        result.loc[mask, col] = prefix + result.loc[mask, col].astype(str) + suffix
        return result

    def remove_chars(self, df: pd.DataFrame, col: str, chars: str) -> pd.DataFrame:
        """
        移除指定字符

        Args:
            df: 数据框
            col: 列名
            chars: 要移除的字符（会被当作整体移除）

        Returns:
            处理后的数据框
        """
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

        result = df.copy()
        # 保留 NaN，只对非空值操作
        mask = result[col].notna()
        result.loc[mask, col] = result.loc[mask, col].astype(str).str.replace(chars, '', regex=False)
        return result

    def replace_values(
        self,
        df: pd.DataFrame,
        col: str,
        old_val: str,
        new_val: str
    ) -> pd.DataFrame:
        """
        替换值

        Args:
            df: 数据框
            col: 列名
            old_val: 被替换的值
            new_val: 替换后的值

        Returns:
            处理后的数据框
        """
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

        result = df.copy()
        # 保留 NaN，只对非空值操作
        mask = result[col].notna()
        result.loc[mask, col] = result.loc[mask, col].astype(str).replace(old_val, new_val)
        return result

    def trim_whitespace(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """
        去除首尾空白字符

        Args:
            df: 数据框
            col: 列名

        Returns:
            处理后的数据框
        """
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

        result = df.copy()
        # 保留 NaN，只对非空值操作
        mask = result[col].notna()
        result.loc[mask, col] = result.loc[mask, col].astype(str).str.strip()
        return result

    def fillna_with_value(self, df: pd.DataFrame, col: str, value: Any) -> pd.DataFrame:
        """
        用指定值填充缺失值

        Args:
            df: 数据框
            col: 列名
            value: 填充值

        Returns:
            处理后的数据框
        """
        if col not in df.columns:
            raise ValueError(f"列不存在: {col}")

        result = df.copy()
        result[col] = result[col].fillna(value)
        return result

    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        删除重复行

        Args:
            df: 数据框
            subset: 用于识别重复的列

        Returns:
            去重后的数据框
        """
        if subset is None:
            return df.drop_duplicates()
        else:
            valid_subset = [c for c in subset if c in df.columns]
            if not valid_subset:
                return df.drop_duplicates()
            return df.drop_duplicates(subset=valid_subset)
