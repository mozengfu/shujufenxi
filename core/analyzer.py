"""数据分析模块，包含描述性统计和数据质量检测"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable


# 聚合函数映射表
AGG_FUNCTIONS = {
    '计数': ('count', None),
    '去重计数': ('nunique', None),
    '求和': ('sum', np.nansum),
    '平均值': ('mean', np.nanmean),
    '中位数': ('median', np.nanmedian),
    '最大值': ('max', np.nanmax),
    '最小值': ('min', np.nanmin),
    '标准差': ('std', np.nanstd),
    '第一值': ('first', None),
    '最后值': ('last', None),
    '占比': ('percent', None),
    '累计占比': ('cumpercent', None),
    '排名': ('rank', None),
    '百分位排名': ('pct_rank', None),
}

# 适用于数值类型的聚合函数
NUMERIC_AGGS = ['计数', '去重计数', '求和', '平均值', '中位数', '最大值', '最小值', '标准差', '占比', '累计占比', '排名', '百分位排名']


class DataAnalyzer:
    """数据分析器"""

    def descriptive_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算描述性统计（全部数值列）"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        stats = pd.DataFrame({
            'count': df[numeric_cols].count(),
            'sum': df[numeric_cols].sum(),
            'mean': df[numeric_cols].mean(),
            'median': df[numeric_cols].median(),
            'std': df[numeric_cols].std(),
            'min': df[numeric_cols].min(),
            'max': df[numeric_cols].max(),
            'Q25': df[numeric_cols].quantile(0.25),
            'Q75': df[numeric_cols].quantile(0.75)
        })

        return stats.round(2)

    def describe_cols(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """对指定列做描述性统计"""
        valid_cols = [c for c in columns if c in df.columns]
        if not valid_cols:
            return pd.DataFrame()

        numeric_data = df[valid_cols].select_dtypes(include=[np.number])
        if numeric_data.empty:
            return pd.DataFrame()

        stats = pd.DataFrame({
            'count': numeric_data.count(),
            'sum': numeric_data.sum(),
            'mean': numeric_data.mean(),
            'median': numeric_data.median(),
            'std': numeric_data.std(),
            'min': numeric_data.min(),
            'max': numeric_data.max(),
            'Q25': numeric_data.quantile(0.25),
            'Q75': numeric_data.quantile(0.75)
        })

        return stats.round(2)

    def group_stats(self, df: pd.DataFrame, group_col: str, value_col: str) -> pd.DataFrame:
        """分组统计"""
        if group_col not in df.columns or value_col not in df.columns:
            raise ValueError(f"列不存在: {group_col} 或 {value_col}")

        if not np.issubdtype(df[value_col].dtype, np.number):
            return df.groupby(group_col)[value_col].agg(['count']).round(2)

        return df.groupby(group_col)[value_col].agg(['count', 'sum', 'mean', 'std']).round(2)

    def group_stats_cols(self, df: pd.DataFrame, group_col: str, value_cols: List[str]) -> pd.DataFrame:
        """对指定列分组统计"""
        if group_col not in df.columns:
            raise ValueError(f"分组列不存在: {group_col}")

        valid_value_cols = [c for c in value_cols if c in df.columns]
        if not valid_value_cols:
            return pd.DataFrame()

        numeric_data = df[valid_value_cols].select_dtypes(include=[np.number])
        if numeric_data.empty:
            return pd.DataFrame()

        result = df.groupby(group_col)[numeric_data.columns].agg(['count', 'sum', 'mean', 'std']).round(2)
        return result

    def aggregate(
        self,
        df: pd.DataFrame,
        group_cols: List[str],
        agg_specs: List[Dict[str, str]]
    ) -> pd.DataFrame:
        """
        通用分组聚合方法

        Args:
            df: 数据框
            group_cols: 分组列列表
            agg_specs: 聚合规范列表，每个元素为 {
                'col': str,       # 列名
                'func': str,      # 聚合函数名（如 '求和', '平均值'）
                'alias': str      # 可选，别名
            }

        Returns:
            分组聚合结果
        """
        if not group_cols or not agg_specs:
            return pd.DataFrame()

        valid_group_cols = [c for c in group_cols if c in df.columns]
        if not valid_group_cols:
            return pd.DataFrame()

        # 构建聚合字典：{col: [(func_str, alias), ...]}
        agg_col_map: Dict[str, List[tuple]] = {}
        alias_map: Dict[str, str] = {}

        for spec in agg_specs:
            col = spec.get('col')
            func = spec.get('func')
            alias = spec.get('alias', f'{col}_{func}')

            if col not in df.columns:
                continue

            agg_col_map.setdefault(col, []).append((func, alias))
            alias_map[alias] = (col, func)

        # groupby.agg 接受 {col: [func_str, ...]} 格式
        agg_dict = {col: [f for f, _ in items] for col, items in agg_col_map.items()}
        result = df.groupby(valid_group_cols).agg(agg_dict)

        # 展平 MultiIndex 列名
        flat_cols = []
        for col_entry in result.columns:
            # col_entry 是 (groupby_col_name, agg_func_str)
            if isinstance(col_entry, tuple):
                col_name, func_name = col_entry
            else:
                col_name, func_name = col_entry, ''
            # 找到匹配的 alias
            matched = None
            for alias, (spec_col, spec_func) in alias_map.items():
                if spec_col == col_name and spec_func == func_name:
                    matched = alias
                    break
            flat_cols.append(matched or f'{col_name}_{func_name}')

        result.columns = flat_cols
        return result.reset_index()

    def aggregate_with_custom_funcs(
        self,
        df: pd.DataFrame,
        group_cols: List[str],
        agg_specs: List[Dict[str, str]]
    ) -> pd.DataFrame:
        """
        支持自定义聚合函数的分组聚合

        Args:
            df: 数据框
            group_cols: 分组列列表
            agg_specs: 聚合规范列表，每个元素为 {
                'col': str,       # 列名
                'func': str,      # 聚合函数名
                'alias': str,     # 可选，别名
                'params': dict    # 可选，额外参数（如分位数）
            }

        Returns:
            分组聚合结果
        """
        if not group_cols or not agg_specs:
            return pd.DataFrame()

        valid_group_cols = [c for c in group_cols if c in df.columns]
        if not valid_group_cols:
            return pd.DataFrame()

        # 分离常规聚合和特殊聚合（占比、累计占比等）
        regular_specs = []
        special_specs = []  # (spec, agg_func_name, base_alias)
        for spec in agg_specs:
            func = spec.get('func')
            col = spec.get('col')
            if func in ('占比', '累计占比', '排名', '百分位排名'):
                # 找到对应的聚合别名（对于同列的常规聚合）
                base_alias = None
                for rspec in agg_specs:
                    if rspec.get('col') == col and rspec.get('func') not in ('占比', '累计占比', '排名', '百分位排名'):
                        base_alias = rspec.get('alias', f"{col}_{rspec.get('func')}")
                        break
                special_specs.append((spec, func, base_alias))
            else:
                regular_specs.append(spec)

        # 第一步：计算常规聚合
        agg_dict = {}
        alias_map = {}  # alias -> spec

        for spec in regular_specs:
            col = spec.get('col')
            func = spec.get('func')
            alias = spec.get('alias', f'{col}_{func}')

            if col not in df.columns:
                continue

            agg_func = self._get_agg_func(func, {})
            if agg_func:
                if col not in agg_dict:
                    agg_dict[col] = []
                agg_dict[col].append((agg_func, alias))
                alias_map[alias] = spec

        results = []
        if agg_dict:
            # 执行常规聚合
            for name, group in df.groupby(valid_group_cols):
                row_result = {}
                if isinstance(name, tuple):
                    for i, grp_col in enumerate(valid_group_cols):
                        row_result[grp_col] = name[i]
                else:
                    row_result[valid_group_cols[0]] = name

                for col, funcs in agg_dict.items():
                    for agg_func, alias in funcs:
                        try:
                            if callable(agg_func):
                                row_result[alias] = agg_func(group[col])
                            else:
                                row_result[alias] = group[col].agg(agg_func)
                        except Exception:
                            row_result[alias] = np.nan

                results.append(row_result)

        result_df = pd.DataFrame(results) if results else pd.DataFrame()

        # 第二步：计算特殊聚合
        if special_specs and not result_df.empty:
            for spec, func_type, base_alias in special_specs:
                col = spec.get('col')
                alias = spec.get('alias', f'{col}_{func_type}')

                if col not in df.columns:
                    continue

                # 检查是否为数值的列（占比、累计占比只能在数值列上计算）
                is_numeric = np.issubdtype(df[col].dtype, np.number)

                # 计算该列的总和/累计等用于基准计算
                if func_type == '占比':
                    if is_numeric:
                        grand_total = df[col].sum()
                        if grand_total != 0 and base_alias and base_alias in result_df.columns:
                            result_df[alias] = result_df[base_alias] / grand_total * 100
                        else:
                            result_df[alias] = np.nan
                    else:
                        result_df[alias] = np.nan

                elif func_type == '累计占比':
                    if is_numeric and base_alias and base_alias in result_df.columns:
                        grouped_sum = df.groupby(valid_group_cols)[col].sum().sort_values(ascending=False)
                        cumsum_values = grouped_sum.cumsum()
                        grand_total = df[col].sum()
                        if grand_total != 0:
                            cumsum_pct = (cumsum_values / grand_total * 100).reset_index()
                            result_df = result_df.merge(
                                cumsum_pct, on=valid_group_cols, how='left', suffixes=('', '_cumsum')
                            )
                            col_name = cumsum_pct.columns[-1]
                            result_df[alias] = result_df[col_name].fillna(np.nan)
                            if col_name != alias:
                                result_df = result_df.drop(columns=[col_name])
                        else:
                            result_df[alias] = np.nan
                    else:
                        result_df[alias] = np.nan

                elif func_type == '排名':
                    # 排名只能在数值列上计算
                    if is_numeric and base_alias and base_alias in result_df.columns:
                        result_df[alias] = result_df[base_alias].rank(method='dense')
                    else:
                        result_df[alias] = np.nan

                elif func_type == '百分位排名':
                    if is_numeric and base_alias and base_alias in result_df.columns:
                        result_df[alias] = result_df[base_alias].rank(pct=True) * 100
                    else:
                        result_df[alias] = np.nan

        # 调整列顺序：分组列在前
        if not result_df.empty:
            cols_order = valid_group_cols + [c for c in result_df.columns if c not in valid_group_cols]
            return result_df[cols_order]
        else:
            return pd.DataFrame()

    def frequency_analysis(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        频次分析

        Args:
            df: 数据框
            columns: 要分析的列

        Returns:
            频次统计结果
        """
        valid_cols = [c for c in columns if c in df.columns]
        if not valid_cols:
            return pd.DataFrame()

        if len(valid_cols) == 1:
            col = valid_cols[0]
            freq = df[col].value_counts(dropna=False).reset_index()
            freq.columns = [col, '频次']
            freq = freq.sort_values('频次', ascending=False).reset_index(drop=True)
            freq['占比%'] = (freq['频次'] / len(df) * 100).round(2)
            freq['累计占比%'] = freq['占比%'].cumsum().round(2)
            return freq
        else:
            # 多列交叉频次
            grouped = df.groupby(valid_cols, dropna=False).size().reset_index(name='频次')
            grouped = grouped.sort_values('频次', ascending=False).reset_index(drop=True)
            grouped['占比%'] = (grouped['频次'] / len(df) * 100).round(2)
            return grouped

    def _get_agg_func(self, func: str, params: Dict = None) -> Optional[Callable]:
        """获取聚合函数"""
        params = params or {}

        # 聚合函数名映射到 pandas 能识别的字符串
        STRING_FUNC_MAP = {
            '计数': 'count',
            '去重计数': 'nunique',
            '第一值': 'first',
            '最后值': 'last',
        }

        if func == '分位数':
            q = params.get('q', 0.5)
            def quantile(x):
                return x.quantile(q)
            return quantile
        elif func in STRING_FUNC_MAP:
            return STRING_FUNC_MAP[func]
        elif func in AGG_FUNCTIONS:
            _, np_func = AGG_FUNCTIONS[func]
            if np_func:
                return np_func
            return func
        else:
            return func

    def conditional_aggregate(
        self,
        df: pd.DataFrame,
        group_cols: List[str],
        agg_specs: List[Dict[str, str]],
        conditions: List[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        条件聚合

        Args:
            df: 数据框
            group_cols: 分组列列表
            agg_specs: 聚合规范列表
            conditions: 筛选条件列表，每个元素为 {
                'col': str,
                'op': str,   # '>', '<', '==', '!=', '>=', '<=', 'contains'
                'value': Any
            }

        Returns:
            条件聚合结果
        """
        if df is None or df.empty:
            return pd.DataFrame()

        filtered_df = df

        # 应用筛选条件
        if conditions:
            for cond in conditions:
                col = cond.get('col')
                op = cond.get('op')
                value = cond.get('value')

                if col not in df.columns:
                    continue

                if op == '>':
                    filtered_df = filtered_df[filtered_df[col] > value]
                elif op == '<':
                    filtered_df = filtered_df[filtered_df[col] < value]
                elif op == '==':
                    filtered_df = filtered_df[filtered_df[col] == value]
                elif op == '!=':
                    filtered_df = filtered_df[filtered_df[col] != value]
                elif op == '>=':
                    filtered_df = filtered_df[filtered_df[col] >= value]
                elif op == '<=':
                    filtered_df = filtered_df[filtered_df[col] <= value]
                elif op == 'contains':
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(str(value), na=False)]

        return self.aggregate_with_custom_funcs(filtered_df, group_cols, agg_specs)

    def detect_missing(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检测缺失值（全部列）"""
        result = {}
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_rows = df[df[col].isna()].index.tolist()
                result[col] = {
                    'count': missing_count,
                    'percentage': round(missing_count / len(df) * 100, 2),
                    'rows': missing_rows[:100]  # 最多显示100行
                }
        return result

    def detect_missing_cols(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """对指定列检测缺失值"""
        result = {}
        valid_cols = [c for c in columns if c in df.columns]

        for col in valid_cols:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_rows = df[df[col].isna()].index.tolist()
                result[col] = {
                    'count': missing_count,
                    'percentage': round(missing_count / len(df) * 100, 2),
                    'rows': missing_rows[:100]
                }
        return result

    def detect_outliers(self, df: pd.DataFrame, method: str = 'IQR') -> Dict[str, Any]:
        """检测异常值（全部数值列）"""
        result = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if method == 'IQR':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower) | (df[col] > upper)][col]
            else:  # Z-score
                std = df[col].std()
                if std == 0 or pd.isna(std):
                    continue  # 跳过无变化的列
                z_scores = np.abs((df[col] - df[col].mean()) / std)
                outliers = df[z_scores > 3][col]

            if len(outliers) > 0:
                result[col] = {
                    'count': len(outliers),
                    'lower_bound': lower if method == 'IQR' else None,
                    'upper_bound': upper if method == 'IQR' else None,
                    'values': outliers.tolist()[:100]
                }

        return result

    def detect_outliers_cols(self, df: pd.DataFrame, columns: List[str], method: str = 'IQR') -> Dict[str, Any]:
        """对指定列检测异常值"""
        result = {}
        valid_cols = [c for c in columns if c in df.columns]
        numeric_data = df[valid_cols].select_dtypes(include=[np.number])

        for col in numeric_data.columns:
            if method == 'IQR':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower) | (df[col] > upper)][col]
            else:  # Z-score
                std = df[col].std()
                if std == 0 or pd.isna(std):
                    continue
                z_scores = np.abs((df[col] - df[col].mean()) / std)
                outliers = df[z_scores > 3][col]

            if len(outliers) > 0:
                result[col] = {
                    'count': len(outliers),
                    'lower_bound': lower if method == 'IQR' else None,
                    'upper_bound': upper if method == 'IQR' else None,
                    'values': outliers.tolist()[:100]
                }

        return result

    def detect_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检测重复行"""
        dup_count = df.duplicated().sum()
        dup_rows = df[df.duplicated(keep=False)].index.tolist() if dup_count > 0 else []

        return {
            'count': dup_count,
            'percentage': round(dup_count / len(df) * 100, 2) if len(df) > 0 else 0,
            'rows': dup_rows[:100]
        }

    def detect_format_issues(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """检测格式问题（日期格式、数值格式）- 全部列"""
        issues = {}

        for col in df.columns:
            col_issues = []
            if df[col].dtype == 'object':
                # 检测日期格式问题
                sample = df[col].dropna().head(100)
                date_patterns = ['年', '月', '日', '-', '/', '.']
                if len(sample) > 0 and any(p in str(sample.iloc[0]) for p in date_patterns):
                    col_issues.append('疑似日期格式')

                # 检测数值中的非数值字符
                numeric_like = df[col].astype(str).str.contains(r'[^0-9.-]', regex=True, na=False)
                invalid_count = numeric_like.sum()
                if invalid_count > 0:
                    col_issues.append(f'含非数值字符: {invalid_count}个')

            if col_issues:
                issues[col] = col_issues

        return issues

    def detect_format_issues_cols(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, List[str]]:
        """对指定列检测格式问题"""
        issues = {}
        valid_cols = [c for c in columns if c in df.columns]

        for col in valid_cols:
            col_issues = []
            if df[col].dtype == 'object':
                # 检测日期格式问题
                sample = df[col].dropna().head(100)
                date_patterns = ['年', '月', '日', '-', '/', '.']
                if len(sample) > 0 and any(p in str(sample.iloc[0]) for p in date_patterns):
                    col_issues.append('疑似日期格式')

                # 检测数值中的非数值字符
                numeric_like = df[col].astype(str).str.contains(r'[^0-9.-]', regex=True, na=False)
                invalid_count = numeric_like.sum()
                if invalid_count > 0:
                    col_issues.append(f'含非数值字符: {invalid_count}个')

            if col_issues:
                issues[col] = col_issues

        return issues

    def full_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """完整质量报告"""
        return {
            'missing': self.detect_missing(df),
            'outliers': self.detect_outliers(df),
            'duplicates': self.detect_duplicates(df),
            'format_issues': self.detect_format_issues(df)
        }

    def compare_tables(self, df1: pd.DataFrame, df2: pd.DataFrame, key_col: str = None) -> Dict[str, Any]:
        """对比两个表格"""
        if key_col and key_col not in df1.columns:
            raise ValueError(f"关键列不存在: {key_col}")

        result = {}

        # 列差异
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)
        result['only_in_df1'] = list(cols1 - cols2)
        result['only_in_df2'] = list(cols2 - cols1)
        result['common_cols'] = list(cols1 & cols2)

        if key_col:
            # 基于关键列的行对比
            common_keys = set(df1[key_col]) & set(df2[key_col])
            result['key_match_count'] = len(common_keys)

            if len(common_keys) > 0:
                merged = df1.merge(df2, on=key_col, suffixes=('_1', '_2'), how='outer', indicator=True)
                result['only_in_df1_rows'] = int((merged['_merge'] == 'left_only').sum())
                result['only_in_df2_rows'] = int((merged['_merge'] == 'right_only').sum())
                result['in_both_rows'] = int((merged['_merge'] == 'both').sum())
        else:
            result['row_diff'] = len(df1) - len(df2)

        return result

    def _prepare_time_series(self, df: pd.DataFrame, date_col: str,
                              value_col: str, period: str) -> pd.Series:
        """将 DataFrame 转为按时间聚合的 Series"""
        if date_col not in df.columns:
            raise ValueError(f"日期列不存在: {date_col}")
        if value_col not in df.columns:
            raise ValueError(f"数值列不存在: {value_col}")

        dates = pd.to_datetime(df[date_col], errors='coerce')
        if dates.isna().all():
            raise ValueError(f"{date_col} 无法解析为日期")

        df = df.copy()
        df['_date'] = dates
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')

        if period == 'month':
            df['_period'] = df['_date'].dt.to_period('M')
        elif period == 'quarter':
            df['_period'] = df['_date'].dt.to_period('Q')
        else:
            raise ValueError(f"不支持的周期: {period}，可选 'month' 或 'quarter'")

        return df.groupby('_period')[value_col].sum()

    def yoy_analysis(self, df: pd.DataFrame, date_col: str,
                     value_col: str, period: str = 'month') -> pd.DataFrame:
        """同比分析：与上年同期对比"""
        ts = self._prepare_time_series(df, date_col, value_col, period)
        shift = 12 if period == 'month' else 4
        prev = ts.shift(shift)

        result = pd.DataFrame({
            '时间': ts.index.astype(str),
            value_col: ts.values,
            '上年同期': prev.values,
        })
        result['增减额'] = result[value_col] - result['上年同期']
        result['同比增幅%'] = (result['增减额'] / result['上年同期'].replace(0, pd.NA) * 100).round(2)
        return result.dropna(subset=['上年同期']).reset_index(drop=True)

    def mom_analysis(self, df: pd.DataFrame, date_col: str,
                     value_col: str, period: str = 'month') -> pd.DataFrame:
        """环比分析：与上一期对比"""
        ts = self._prepare_time_series(df, date_col, value_col, period)
        prev = ts.shift(1)

        result = pd.DataFrame({
            '时间': ts.index.astype(str),
            value_col: ts.values,
            '上期值': prev.values,
        })
        result['增减额'] = result[value_col] - result['上期值']
        result['环比增幅%'] = (result['增减额'] / result['上期值'].replace(0, pd.NA) * 100).round(2)
        return result.dropna(subset=['上期值']).reset_index(drop=True)
