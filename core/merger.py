"""多表合并模块"""
import pandas as pd
from typing import List


class TableMerger:
    """多表合并器"""

    def merge_by_key(self, dfs: List[pd.DataFrame], key: str, how: str = 'inner') -> pd.DataFrame:
        """按关键列合并（类似 VLOOKUP）"""
        if not dfs:
            raise ValueError("至少需要一个 DataFrame")

        if key not in dfs[0].columns:
            raise ValueError(f"关键列不存在: {key}")

        result = dfs[0]
        for df in dfs[1:]:
            if key not in df.columns:
                raise ValueError(f"关键列不存在: {key}")
            result = result.merge(df, on=key, how=how, suffixes=('', '_y'))

        return result

    def append_rows(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """行追加合并（相同结构表合并）"""
        if not dfs:
            raise ValueError("至少需要一个 DataFrame")

        return pd.concat(dfs, ignore_index=True)

    def preview_merge(self, df1: pd.DataFrame, df2: pd.DataFrame, key: str, how: str = 'inner') -> dict:
        """合并预览"""
        if key not in df1.columns or key not in df2.columns:
            return {'error': f'关键列不存在: {key}'}

        preview = df1.merge(df2, on=key, how=how, suffixes=('_1', '_2'))

        return {
            'df1_rows': len(df1),
            'df2_rows': len(df2),
            'result_rows': len(preview),
            'result_columns': len(preview.columns),
            'preview_data': preview.head(10).to_dict('records')
        }