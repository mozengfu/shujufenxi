"""AI 数据解读模块 — 预留接口，后续接入真实 API 只需修改 summarize 方法"""

from typing import Optional, Dict

import pandas as pd


class AISummarizer:
    """AI 数据解读器

    使用方式：
        summarizer = AISummarizer(
            api_key='sk-xxx',
            model='claude-sonnet-4-6',
            endpoint='https://api.anthropic.com/v1/messages'  # 可选
        )
        summary = summarizer.summarize(df, stats, quality_report, freq_result, analysis_result)

    接入不同后端只需修改 _call_ai() 方法。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
    ):
        self.api_key = api_key
        self.model = model or 'claude-sonnet-4-6'
        self.endpoint = endpoint

    def summarize(
        self,
        df: pd.DataFrame,
        stats: Optional[pd.DataFrame] = None,
        quality_report: Optional[Dict] = None,
        freq_result: Optional[pd.DataFrame] = None,
        analysis_result: Optional[pd.DataFrame] = None,
        context: str = '',
    ) -> str:
        """根据分析结果生成 AI 文字总结

        Args:
            df: 原始数据
            stats: 描述性统计结果
            quality_report: 数据质量报告
            freq_result: 频次分析结果
            analysis_result: 用户当前分析的结果 DataFrame
            context: 用户补充的分析背景

        Returns:
            AI 生成的总结文字
        """
        if not self.api_key:
            return (
                'AI 总结功能已预留接口。请在设置中配置 API Key 后使用。\n\n'
                '支持的接口：Claude API / OpenAI / DeepSeek 等。\n'
                '配置方式：在核心目录下创建 .env 文件，设置 AI_API_KEY 和 AI_MODEL 变量。'
            )

        prompt = self._build_prompt(df, stats, quality_report, freq_result, analysis_result, context)
        return self._call_ai(prompt)

    def _build_prompt(
        self,
        df: pd.DataFrame,
        stats: Optional[pd.DataFrame],
        quality_report: Optional[Dict],
        freq_result: Optional[pd.DataFrame],
        analysis_result: Optional[pd.DataFrame],
        context: str,
    ) -> str:
        """构建 AI 解读用的 prompt"""
        lines = []
        lines.append('你是一位资深数据分析师。请根据以下数据和分析结果，用中文写一段业务洞察总结。')
        lines.append('要求：')
        lines.append('1. 用业务语言，不要罗列数字')
        lines.append('2. 指出数据反映出的关键现象和趋势')
        lines.append('3. 给出可操作的建议')
        lines.append('4. 控制在 200 字以内')
        lines.append('')

        # 数据概况
        lines.append(f'数据概况：{len(df)} 行，{len(df.columns)} 列')
        lines.append(f'列名：{", ".join(df.columns.tolist())}')

        if stats is not None and not stats.empty:
            lines.append('')
            lines.append('描述性统计：')
            lines.append(stats.to_string())

        if quality_report:
            missing = quality_report.get('missing', {})
            outliers = quality_report.get('outliers', {})
            duplicates = quality_report.get('duplicates', {})
            lines.append('')
            lines.append('数据质量：')
            if missing:
                lines.append(f'  缺失值：{len(missing)} 个列存在缺失')
            if outliers:
                lines.append(f'  异常值：{len(outliers)} 个列存在异常')
            if duplicates:
                lines.append(f'  重复行：{duplicates.get("count", 0)} 行')

        if freq_result is not None and not freq_result.empty:
            lines.append('')
            lines.append('频次分析：')
            lines.append(freq_result.head(10).to_string())

        if analysis_result is not None and not analysis_result.empty:
            lines.append('')
            lines.append('用户当前分析结果：')
            lines.append(analysis_result.head(10).to_string())

        if context:
            lines.append('')
            lines.append(f'用户补充说明：{context}')

        return '\n'.join(lines)

    def _call_ai(self, prompt: str) -> str:
        """调用 AI 后端生成总结

        接入不同 AI 服务只需修改此方法。

        Claude API 示例：
            import httpx
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            }
            body = {
                'model': self.model,
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': prompt}],
            }
            resp = httpx.post(self.endpoint, headers=headers, json=body)
            return resp.json()['content'][0]['text']

        OpenAI 示例：
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.endpoint)
            resp = client.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}])
            return resp.choices[0].message.content
        """
        # TODO: 接入真实 API
        return 'AI 总结功能待接入。请在 AISummarizer._call_ai() 方法中配置真实 API。'
