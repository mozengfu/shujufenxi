"""复杂报表模板系统 - 支持多层表头、数据映射、计算规则"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
import pandas as pd
import numpy as np


@dataclass
class HeaderCell:
    """表头单元格定义"""
    name: str
    rowspan: int = 1
    colspan: int = 1
    parent: Optional[str] = None
    data_field: Optional[str] = None  # 对应数据列名
    align: str = 'center'  # left/center/right


@dataclass
class CalculationRule:
    """计算规则"""
    name: str
    calc_type: str  # 'rank', 'formula', 'sum', 'avg', 'custom'
    params: Dict[str, Any] = field(default_factory=dict)
    # rank: {by: field, order: asc/desc}
    # formula: {expression: str}
    # custom: {func: callable}


@dataclass
class ConditionalFormat:
    """条件格式"""
    field: str
    rules: List[Dict[str, Any]]  # [{value: 1, style: {bg_color: 'FFD700'}}]


@dataclass
class TotalRowConfig:
    """合计行配置"""
    enabled: bool = True
    label: str = '合计'
    aggregations: Dict[str, str] = field(default_factory=dict)  # field: sum/avg/count/-


@dataclass
class ComplexReportTemplate:
    """复杂报表模板"""
    name: str
    title: str = ''
    subtitle: str = ''
    headers: List[List[HeaderCell]] = field(default_factory=list)  # 多层表头
    data_mapping: Dict[str, str] = field(default_factory=dict)  # 模板字段 -> 数据字段
    calculations: List[CalculationRule] = field(default_factory=list)
    conditional_formats: List[ConditionalFormat] = field(default_factory=list)
    total_row: TotalRowConfig = field(default_factory=TotalRowConfig)
    version: str = '1.0'

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            'name': self.name,
            'title': self.title,
            'subtitle': self.subtitle,
            'headers': [
                [
                    {
                        'name': cell.name,
                        'rowspan': cell.rowspan,
                        'colspan': cell.colspan,
                        'parent': cell.parent,
                        'data_field': cell.data_field,
                        'align': cell.align
                    }
                    for cell in row
                ]
                for row in self.headers
            ],
            'data_mapping': self.data_mapping,
            'calculations': [
                {
                    'name': calc.name,
                    'calc_type': calc.calc_type,
                    'params': calc.params
                }
                for calc in self.calculations
            ],
            'conditional_formats': [
                {
                    'field': cf.field,
                    'rules': cf.rules
                }
                for cf in self.conditional_formats
            ],
            'total_row': {
                'enabled': self.total_row.enabled,
                'label': self.total_row.label,
                'aggregations': self.total_row.aggregations
            },
            'version': self.version
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'ComplexReportTemplate':
        """从字典创建"""
        headers = [
            [HeaderCell(**cell_data) for cell_data in row]
            for row in data.get('headers', [])
        ]

        calculations = [
            CalculationRule(**calc_data)
            for calc_data in data.get('calculations', [])
        ]

        conditional_formats = [
            ConditionalFormat(**cf_data)
            for cf_data in data.get('conditional_formats', [])
        ]

        total_row_data = data.get('total_row', {})
        total_row = TotalRowConfig(**total_row_data)

        return cls(
            name=data['name'],
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            headers=headers,
            data_mapping=data.get('data_mapping', {}),
            calculations=calculations,
            conditional_formats=conditional_formats,
            total_row=total_row,
            version=data.get('version', '1.0')
        )

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'ComplexReportTemplate':
        """从 JSON 创建"""
        return cls.from_dict(json.loads(json_str))

    def save(self, file_path: str) -> None:
        """保存到文件"""
        Path(file_path).write_text(self.to_json(), encoding='utf-8')

    @classmethod
    def load(cls, file_path: str) -> 'ComplexReportTemplate':
        """从文件加载"""
        return cls.from_json(Path(file_path).read_text(encoding='utf-8'))


class ComplexReportGenerator:
    """复杂报表生成器"""

    def __init__(self, template: ComplexReportTemplate):
        self.template = template

    def generate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据模板生成报表数据
        返回处理后的 DataFrame，列名与模板表头对应
        """
        # 1. 应用数据映射
        mapped_df = self._apply_data_mapping(df)

        # 2. 执行计算规则
        calculated_df = self._apply_calculations(mapped_df)

        # 3. 重组数据以匹配模板结构
        result_df = self._restructure_data(calculated_df)

        return result_df

    def _apply_data_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用数据映射"""
        result = {}
        for template_field, data_field in self.template.data_mapping.items():
            if data_field in df.columns:
                result[template_field] = df[data_field]
            elif data_field.startswith('calculated:'):
                # 计算字段，稍后处理
                result[template_field] = None
            else:
                # 字段不存在，填充空值
                result[template_field] = pd.Series([None] * len(df), index=df.index)

        return pd.DataFrame(result, index=df.index)

    def _apply_calculations(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行计算规则"""
        result_df = df.copy()

        for calc in self.template.calculations:
            if calc.calc_type == 'rank':
                result_df = self._calc_rank(result_df, calc)
            elif calc.calc_type == 'formula':
                result_df = self._calc_formula(result_df, calc)
            elif calc.calc_type == 'sum':
                result_df = self._calc_sum(result_df, calc)
            elif calc.calc_type == 'avg':
                result_df = self._calc_avg(result_df, calc)

        return result_df

    def _calc_rank(self, df: pd.DataFrame, calc: CalculationRule) -> pd.DataFrame:
        """计算排名"""
        by_field = calc.params.get('by')
        order = calc.params.get('order', 'desc')

        if by_field and by_field in df.columns:
            ascending = (order == 'asc')
            df[calc.name] = df[by_field].rank(
                method='min',
                ascending=ascending,
                na_option='bottom'
            ).astype(int)

        return df

    def _calc_formula(self, df: pd.DataFrame, calc: CalculationRule) -> pd.DataFrame:
        """计算公式"""
        expression = calc.params.get('expression', '')

        # 替换字段引用为实际值
        for col in df.columns:
            expression = expression.replace(f'{{{col}}}', f'df["{col}"]')

        try:
            df[calc.name] = eval(expression)
        except Exception:
            df[calc.name] = None

        return df

    def _calc_sum(self, df: pd.DataFrame, calc: CalculationRule) -> pd.DataFrame:
        """计算合计"""
        fields = calc.params.get('fields', [])
        if fields:
            df[calc.name] = df[fields].sum(axis=1)
        return df

    def _calc_avg(self, df: pd.DataFrame, calc: CalculationRule) -> pd.DataFrame:
        """计算平均值"""
        fields = calc.params.get('fields', [])
        if fields:
            df[calc.name] = df[fields].mean(axis=1)
        return df

    def _restructure_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """重组数据以匹配模板表头结构"""
        # 获取所有叶子节点（实际数据列）
        leaf_fields = []
        for row in self.template.headers:
            for cell in row:
                if cell.data_field:
                    leaf_fields.append(cell.data_field)

        # 按叶子节点顺序重组数据
        result_data = {}
        for field in leaf_fields:
            if field in df.columns:
                result_data[field] = df[field]
            else:
                result_data[field] = pd.Series([None] * len(df), index=df.index)

        return pd.DataFrame(result_data, index=df.index)

    def get_header_structure(self) -> List[List[Dict]]:
        """获取表头结构，用于导出"""
        return [
            [
                {
                    'name': cell.name,
                    'rowspan': cell.rowspan,
                    'colspan': cell.colspan,
                    'align': cell.align
                }
                for cell in row
            ]
            for row in self.template.headers
        ]

    def calculate_total_row(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """计算合计行"""
        if not self.template.total_row.enabled:
            return None

        total = {}
        aggregations = self.template.total_row.aggregations

        for col in df.columns:
            agg = aggregations.get(col, '-')

            if agg == '-':
                total[col] = ''
            elif agg == 'sum':
                total[col] = df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else ''
            elif agg == 'avg':
                total[col] = df[col].mean() if pd.api.types.is_numeric_dtype(df[col]) else ''
            elif agg == 'count':
                total[col] = df[col].count()
            elif col == list(df.columns)[0]:  # 第一列通常是标签列
                total[col] = self.template.total_row.label
            else:
                total[col] = ''

        return pd.Series(total)


class TemplateLibrary:
    """模板库 - 预定义常用模板"""

    @staticmethod
    def create_broadband_outage_template() -> ComplexReportTemplate:
        """创建宽带业务不可用时长报表模板"""
        # 第一层表头
        header_row1 = [
            HeaderCell(name='单位', rowspan=2, colspan=1, data_field='单位', align='center'),
            HeaderCell(name='排名', rowspan=2, colspan=1, data_field='排名', align='center'),
            HeaderCell(name='采集用户总数', rowspan=2, colspan=1, data_field='采集用户总数', align='center'),
            HeaderCell(name='月统计中断用户数', rowspan=2, colspan=1, data_field='月统计中断用户数', align='center'),
            HeaderCell(name='总不可用时长', rowspan=1, colspan=4, align='center'),
            HeaderCell(name='(18:00-次日1:00)时长', rowspan=1, colspan=4, align='center'),
            HeaderCell(name='(6:00-18:00)时长', rowspan=1, colspan=4, align='center'),
            HeaderCell(name='(1:00-6:00)时长', rowspan=1, colspan=4, align='center'),
        ]

        # 第二层表头
        header_row2 = [
            HeaderCell(name='中断次数', parent='总不可用时长', data_field='总中断次数', align='center'),
            HeaderCell(name='中断时长', parent='总不可用时长', data_field='总中断时长', align='center'),
            HeaderCell(name='加权时长', parent='总不可用时长', data_field='总加权时长', align='center'),
            HeaderCell(name='平均不可用时长', parent='总不可用时长', data_field='总平均不可用时长', align='center'),
            HeaderCell(name='中断次数', parent='(18:00-次日1:00)时长', data_field='晚中断次数', align='center'),
            HeaderCell(name='中断时长', parent='(18:00-次日1:00)时长', data_field='晚中断时长', align='center'),
            HeaderCell(name='加权时长', parent='(18:00-次日1:00)时长', data_field='晚加权时长', align='center'),
            HeaderCell(name='平均不可用时长', parent='(18:00-次日1:00)时长', data_field='晚平均不可用时长', align='center'),
            HeaderCell(name='中断次数', parent='(6:00-18:00)时长', data_field='白天中断次数', align='center'),
            HeaderCell(name='中断时长', parent='(6:00-18:00)时长', data_field='白天中断时长', align='center'),
            HeaderCell(name='加权时长', parent='(6:00-18:00)时长', data_field='白天加权时长', align='center'),
            HeaderCell(name='平均不可用时长', parent='(6:00-18:00)时长', data_field='白天平均不可用时长', align='center'),
            HeaderCell(name='中断次数', parent='(1:00-6:00)时长', data_field='凌晨中断次数', align='center'),
            HeaderCell(name='中断时长', parent='(1:00-6:00)时长', data_field='凌晨中断时长', align='center'),
            HeaderCell(name='加权时长', parent='(1:00-6:00)时长', data_field='凌晨加权时长', align='center'),
            HeaderCell(name='平均不可用时长', parent='(1:00-6:00)时长', data_field='凌晨平均不可用时长', align='center'),
        ]

        # 数据映射
        data_mapping = {
            '单位': 'district_name',
            '排名': 'calculated:rank',
            '采集用户总数': 'total_users',
            '月统计中断用户数': 'outage_users',
            '总中断次数': 'total_outage_count',
            '总中断时长': 'total_outage_duration',
            '总加权时长': 'total_weighted_duration',
            '总平均不可用时长': 'calculated:total_avg_duration',
            '晚中断次数': 'evening_outage_count',
            '晚中断时长': 'evening_outage_duration',
            '晚加权时长': 'evening_weighted_duration',
            '晚平均不可用时长': 'calculated:evening_avg_duration',
            '白天中断次数': 'day_outage_count',
            '白天中断时长': 'day_outage_duration',
            '白天加权时长': 'day_weighted_duration',
            '白天平均不可用时长': 'calculated:day_avg_duration',
            '凌晨中断次数': 'night_outage_count',
            '凌晨中断时长': 'night_outage_duration',
            '凌晨加权时长': 'night_weighted_duration',
            '凌晨平均不可用时长': 'calculated:night_avg_duration',
        }

        # 计算规则
        calculations = [
            CalculationRule(
                name='排名',
                calc_type='rank',
                params={'by': '总加权时长', 'order': 'desc'}
            ),
            CalculationRule(
                name='总平均不可用时长',
                calc_type='formula',
                params={'expression': '{总中断时长} / {总中断次数}'}
            ),
            CalculationRule(
                name='晚平均不可用时长',
                calc_type='formula',
                params={'expression': '{晚中断时长} / {晚中断次数}'}
            ),
            CalculationRule(
                name='白天平均不可用时长',
                calc_type='formula',
                params={'expression': '{白天中断时长} / {白天中断次数}'}
            ),
            CalculationRule(
                name='凌晨平均不可用时长',
                calc_type='formula',
                params={'expression': '{凌晨中断时长} / {凌晨中断次数}'}
            ),
        ]

        # 条件格式 - 排名前三高亮
        conditional_formats = [
            ConditionalFormat(
                field='排名',
                rules=[
                    {'value': 1, 'style': {'bg_color': 'FFD700', 'font_color': '000000'}},  # 金色
                    {'value': 2, 'style': {'bg_color': 'C0C0C0', 'font_color': '000000'}},  # 银色
                    {'value': 3, 'style': {'bg_color': 'CD7F32', 'font_color': 'FFFFFF'}},  # 铜色
                ]
            )
        ]

        # 合计行配置
        total_row = TotalRowConfig(
            enabled=True,
            label='合计',
            aggregations={
                '单位': '-',
                '排名': '-',
                '采集用户总数': 'sum',
                '月统计中断用户数': 'sum',
                '总中断次数': 'sum',
                '总中断时长': 'sum',
                '总加权时长': 'sum',
                '总平均不可用时长': 'avg',
                '晚中断次数': 'sum',
                '晚中断时长': 'sum',
                '晚加权时长': 'sum',
                '晚平均不可用时长': 'avg',
                '白天中断次数': 'sum',
                '白天中断时长': 'sum',
                '白天加权时长': 'sum',
                '白天平均不可用时长': 'avg',
                '凌晨中断次数': 'sum',
                '凌晨中断时长': 'sum',
                '凌晨加权时长': 'sum',
                '凌晨平均不可用时长': 'avg',
            }
        )

        return ComplexReportTemplate(
            name='broadband_outage',
            title='宽带业务不可用时长统计报表（门户口径）',
            subtitle='统计日期: {date}',
            headers=[header_row1, header_row2],
            data_mapping=data_mapping,
            calculations=calculations,
            conditional_formats=conditional_formats,
            total_row=total_row
        )


# 预定义模板
BROADBAND_OUTAGE_TEMPLATE = TemplateLibrary.create_broadband_outage_template()