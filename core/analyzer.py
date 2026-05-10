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
    '行数': ('size', None),
}

def _is_numeric(series: pd.Series) -> bool:
    """判断 Series 是否为数值的，兼容 numpy dtype 和 pandas 扩展 dtype（如 StringDtype）。"""
    try:
        return np.issubdtype(series.dtype, np.number)
    except TypeError:
        return False


# 适用于数值类型的聚合函数
NUMERIC_AGGS = ['计数', '去重计数', '求和', '平均值', '中位数', '最大值', '最小值', '标准差', '占比', '累计占比', '排名', '百分位排名', '行数']


def is_percent_col(col_name: str) -> bool:
    """判断列名是否应该以百分比格式显示"""
    return col_name in ('占比%', '累计占比%') or '占比' in col_name or '排名' in col_name


def make_total_row(df: pd.DataFrame, agg_items: list = None) -> pd.Series:
    """生成合计行：数值列求和，占比列特殊处理"""
    # 找出无条件行数项的别名（如"回访总量"），作为占比分母
    base_col = None
    for item in agg_items or []:
        if item.get('func') == '行数' and not item.get('condition') and not item.get('show_percent'):
            base_col = item.get('alias')
            break

    # 构建占比列 -> (percent_mode, 对应数量列别名) 映射
    percent_map: dict[str, tuple[str, str]] = {}
    if agg_items:
        for item in agg_items:
            if item.get('show_percent'):
                alias = item.get('alias', '')
                if alias:
                    mode = item.get('percent_mode', 'column')
                    percent_map[f'{alias}占比'] = (mode, alias)

    totals = []
    for j, col in enumerate(df.columns):
        if col in percent_map:
            mode, qty_alias = percent_map[col]
            if mode == 'group':
                # 按组占比合计 = 该条件列合计 / 行数列合计 × 100
                if base_col and base_col in df.columns:
                    base_total = df[base_col].sum()
                    if base_total != 0:
                        totals.append((df[qty_alias].sum() / base_total * 100).round(2))
                    else:
                        totals.append('-')
                else:
                    totals.append('-')
            else:
                totals.append(df[col].sum())
        elif is_percent_col(col):
            totals.append(100.0 if col == '占比%' else '-')
        elif _is_numeric(df[col]):
            totals.append(df[col].sum())
        elif j == 0:
            totals.append('合计')
        else:
            totals.append('-')
    return pd.Series(totals, index=df.columns)


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

        if not _is_numeric(df[value_col]):
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
        size_specs = []  # 行数聚合，不依赖具体列
        for spec in agg_specs:
            func = spec.get('func')
            col = spec.get('col')
            if func == '行数':
                size_specs.append(spec)
            elif func in ('占比', '累计占比', '排名', '百分位排名'):
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

        # 处理行数聚合
        for spec in size_specs:
            alias = spec.get('alias', '行数')
            size_result = df.groupby(valid_group_cols, dropna=False).size().reset_index(name=alias)
            if result_df.empty:
                result_df = size_result
            else:
                result_df = result_df.merge(size_result, on=valid_group_cols, how='outer')

        # 第二步：计算特殊聚合
        if special_specs and not result_df.empty:
            for spec, func_type, base_alias in special_specs:
                col = spec.get('col')
                alias = spec.get('alias', f'{col}_{func_type}')

                if col not in df.columns:
                    continue

                # 检查是否为数值的列（占比、累计占比只能在数值列上计算）
                is_numeric = _is_numeric(df[col])

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

                # 尝试将 value 转换为列的实际类型
                actual_value = value
                if _is_numeric(df[col]) and isinstance(value, str):
                    try:
                        actual_value = float(value) if '.' in value else int(value)
                    except ValueError:
                        pass

                if op == '>':
                    filtered_df = filtered_df[filtered_df[col] > actual_value]
                elif op == '<':
                    filtered_df = filtered_df[filtered_df[col] < actual_value]
                elif op == '==':
                    filtered_df = filtered_df[filtered_df[col] == actual_value]
                elif op == '!=':
                    filtered_df = filtered_df[filtered_df[col] != actual_value]
                elif op == '>=':
                    filtered_df = filtered_df[filtered_df[col] >= actual_value]
                elif op == '<=':
                    filtered_df = filtered_df[filtered_df[col] <= actual_value]
                elif op == 'contains':
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(str(value), na=False)]

        return self.aggregate_with_custom_funcs(filtered_df, group_cols, agg_specs)

    def multi_conditional_aggregate(
        self,
        df: pd.DataFrame,
        group_cols: List[str],
        agg_items: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        多条件列聚合：一个表中展示多个条件下的聚合值和占比

        Args:
            df: 数据框
            group_cols: 分组列列表
            agg_items: 聚合项列表，每项为 {
                'col': str,          # 值列
                'func': str,         # 聚合函数名（如'求和'、'计数'等）
                'alias': str,        # 自定义列名
                'condition': dict,   # 筛选条件 {col: (op, value)}，None表示无筛选
                'show_percent': bool # 是否显示占比列
            }

        Returns:
            多条件列聚合结果 DataFrame
        """
        if df is None or df.empty or not agg_items:
            return pd.DataFrame()

        valid_group_cols = [c for c in group_cols if c in df.columns]
        if not valid_group_cols:
            return pd.DataFrame()

        result_dfs = []

        # 预计算每组的行数，用于"按组总数"占比模式
        group_sizes = df.groupby(valid_group_cols, dropna=False).size()

        for item in agg_items:
            col = item.get('col')
            func_name = item.get('func')
            alias = item.get('alias', f'{col}-{func_name}')
            conditions = item.get('condition') or {}
            show_percent = item.get('show_percent', False)

            if col not in df.columns:
                continue

            # 获取聚合函数
            func_info = AGG_FUNCTIONS.get(func_name)
            if func_info is None:
                continue

            func_type, _ = func_info

            # 筛选数据
            filtered_df = df
            for cond_col, (op, value) in conditions.items():
                if cond_col not in df.columns:
                    continue

                # 尝试将 value 转换为列的实际类型
                actual_value = value
                if _is_numeric(df[cond_col]) and isinstance(value, str):
                    try:
                        actual_value = float(value) if '.' in value else int(value)
                    except ValueError:
                        pass

                if op == '>':
                    filtered_df = filtered_df[filtered_df[cond_col] > actual_value]
                elif op == '<':
                    filtered_df = filtered_df[filtered_df[cond_col] < actual_value]
                elif op == '==':
                    filtered_df = filtered_df[filtered_df[cond_col] == actual_value]
                elif op == '!=':
                    filtered_df = filtered_df[filtered_df[cond_col] != actual_value]
                elif op == '>=':
                    filtered_df = filtered_df[filtered_df[cond_col] >= actual_value]
                elif op == '<=':
                    filtered_df = filtered_df[filtered_df[cond_col] <= actual_value]
                elif op == 'contains':
                    filtered_df = filtered_df[filtered_df[cond_col].astype(str).str.contains(str(value), na=False)]

            # 执行聚合
            if func_type == 'count':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].count().rename(alias).reset_index()
            elif func_type == 'nunique':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].nunique().rename(alias).reset_index()
            elif func_type == 'sum':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].sum().rename(alias).reset_index()
            elif func_type == 'mean':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].mean().rename(alias).reset_index()
            elif func_type == 'median':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].median().rename(alias).reset_index()
            elif func_type == 'max':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].max().rename(alias).reset_index()
            elif func_type == 'min':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].min().rename(alias).reset_index()
            elif func_type == 'std':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].std().rename(alias).reset_index()
            elif func_type == 'first':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].first().rename(alias).reset_index()
            elif func_type == 'last':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False)[col].last().rename(alias).reset_index()
            elif func_type == 'size':
                agg_result = filtered_df.groupby(valid_group_cols, dropna=False).size().reset_index(name=alias)
                # 无条件的行数不参与占比（组内行数/组内行数=100%，无意义）
                # 有条件过滤的行数可按组总数计算占比（条件行数/组内行数）
                if show_percent and not conditions:
                    show_percent = False
            else:
                continue

            # 计算占比（行数按组总数时不需要数值列，其他模式需要数值列做求和）
            is_size_percent = func_type == 'size' and show_percent
            if show_percent and (is_size_percent or _is_numeric(df[col])):
                percent_mode = item.get('percent_mode', 'column')
                percent_alias = f'{alias}占比'
                if percent_mode == 'group':
                    # 按组内行数计算占比（分母是组内总行数）
                    if len(valid_group_cols) == 1:
                        sizes_aligned = group_sizes.reset_index()
                        sizes_aligned.columns = [valid_group_cols[0], '_group_size']
                    else:
                        sizes_aligned = group_sizes.reset_index()
                        sizes_aligned.columns = valid_group_cols + ['_group_size']
                    merged_sizes = agg_result[valid_group_cols].merge(sizes_aligned, on=valid_group_cols, how='left')
                    group_size_values = merged_sizes['_group_size'].values
                    nonzero = group_size_values != 0
                    agg_result[percent_alias] = np.where(
                        nonzero,
                        (agg_result[alias].values / group_size_values * 100).round(2),
                        np.nan
                    )
                else:
                    # 按列总和计算占比（现有行为）
                    if func_type == 'size':
                        grand_total = agg_result[alias].sum()
                    else:
                        grand_total = filtered_df[col].sum()
                    if grand_total != 0:
                        agg_result[percent_alias] = (agg_result[alias] / grand_total * 100).round(2)
                    else:
                        agg_result[percent_alias] = np.nan

            result_dfs.append(agg_result)

        if not result_dfs:
            return pd.DataFrame()

        # 合并所有结果
        result = result_dfs[0]
        for rdf in result_dfs[1:]:
            result = result.merge(rdf, on=valid_group_cols, how='outer')

        # 排序：按第一个数值列降序
        numeric_cols = result.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            result = result.sort_values(numeric_cols[0], ascending=False, na_position='last')

        result = result.reset_index(drop=True)
        return result

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
