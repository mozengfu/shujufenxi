"""AI 数据解读模块 — 支持单轮总结和多轮对话"""

from typing import Optional, Dict, List

import pandas as pd


class AISummarizer:
    """AI 数据解读器

    使用方式（单轮总结）：
        summarizer = AISummarizer(api_key='sk-xxx', model='claude-sonnet-4-6')
        summary = summarizer.summarize(df, stats, quality_report, freq_result, analysis_result)

    使用方式（多轮对话）：
        history = []
        response = summarizer.chat('这个数据有什么趋势？', history, system_prompt)
        history.append({'role': 'user', 'content': '这个数据有什么趋势？'})
        history.append({'role': 'assistant', 'content': response})
        response = summarizer.chat('能详细说明一下吗？', history, system_prompt)
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
        messages = [{'role': 'user', 'content': prompt}]
        return self._call_api(messages)

    def chat(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        system_prompt: str = '',
    ) -> str:
        """多轮对话

        Args:
            user_message: 用户当前输入
            history: 之前的对话历史（user/assistant 交替）
            system_prompt: 系统提示，包含数据上下文

        Returns:
            AI 回复
        """
        if not self.api_key:
            return '请先在"设置 → AI 配置"中配置 API Key。'

        messages = list(history) + [{'role': 'user', 'content': user_message}]
        return self._call_api(messages, system_prompt)

    def _build_chat_system_prompt(
        self,
        df: pd.DataFrame,
        stats: Optional[pd.DataFrame] = None,
        quality_report: Optional[Dict] = None,
    ) -> str:
        """构建对话用的系统提示"""
        lines = []
        lines.append('你是一位资深数据分析师，正在帮助用户分析一份数据。')
        lines.append('请用业务语言回答，用结构化的方式给出洞察，包括分组排名、趋势和可操作建议。')
        lines.append('')

        lines.append(f'数据概况：{len(df)} 行，{len(df.columns)} 列')
        lines.append('列名及类型：')
        for col in df.columns:
            lines.append(f'  - {col}: {df[col].dtype}')

        # 前 3 行样本
        lines.append('')
        lines.append('前 3 行样本：')
        lines.append(df.head(3).to_string())

        # 摘要统计
        if stats is not None and not stats.empty:
            lines.append('')
            lines.append('描述性统计摘要：')
            lines.append(stats.to_string())

        # 质量亮点
        if quality_report:
            lines.append('')
            lines.append('数据质量：')
            missing = quality_report.get('missing', {})
            if missing:
                lines.append(f'  缺失值：{len(missing)} 个列存在缺失')
            outliers = quality_report.get('outliers', {})
            if outliers:
                lines.append(f'  异常值：{len(outliers)} 个列存在异常')
            duplicates = quality_report.get('duplicates', {})
            if duplicates:
                lines.append(f'  重复行：{duplicates.get("count", 0)} 行')

        return '\n'.join(lines)

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
        lines.append('你是一位资深数据分析师。请根据以下数据和分析结果，用中文撰写一份结构化的业务洞察报告。')
        lines.append('')
        lines.append('【分析要求】')
        lines.append('')
        lines.append('一、数据概况：简要说明数据规模、核心字段含义和业务场景。')
        lines.append('')
        lines.append('二、核心发现（按主要分组维度展开）：')
        lines.append('  如果存在分组列，请围绕分组维度进行解读，包括：')
        lines.append('  1. 各组的整体表现和排名情况')
        lines.append('  2. 占比最高的前3名（TOP3），给出具体数值和占比百分比')
        lines.append('  3. 表现最差的后3名（BOTTOM3），给出具体数值和占比百分比')
        lines.append('  4. 各组之间的差异和对比分析')
        lines.append('')
        lines.append('三、趋势与异常：')
        lines.append('  1. 数据中的明显趋势、周期性变化或极值')
        lines.append('  2. 数据质量问题（缺失、异常值、重复）及其可能的影响')
        lines.append('  3. 如有频次分析结果，指出最常见的取值和分布特点')
        lines.append('')
        lines.append('四、内容分析：')
        lines.append('  结合上述所有分析，给出你的专业判断，指出值得关注的现象。')
        lines.append('')
        lines.append('五、建议：')
        lines.append('  基于分析结果给出2-4条具体、可操作的业务建议。')
        lines.append('')
        lines.append('【注意事项】')
        lines.append('- 用业务语言描述，不要只列数字，要有解读和判断')
        lines.append('- TOP3/BOTTOM3 等结论要有数据支撑，给出具体百分比')
        lines.append('- 如果数据中不包含分组列或某些信息不足，如实说明即可')
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
        """调用 AI 后端生成总结（单轮模式）"""
        messages = [{'role': 'user', 'content': prompt}]
        return self._call_api(messages)

    def _call_api(self, messages: List[Dict[str, str]], system_prompt: str = '') -> str:
        """调用 AI 后端生成回复

        支持 OpenAI 兼容格式（默认）和 Anthropic Claude 原生格式。
        先尝试 OpenAI 兼容调用，失败后自动回退到 Claude 格式。
        """
        try:
            import httpx
        except ImportError:
            return 'AI 功能依赖 httpx 库，请先运行 pip install httpx 安装。'

        # 调试日志
        log = (f'Endpoint: {self.endpoint}, Model: {self.model}, '
               f'Key len: {len(self.api_key) if self.api_key else 0}')

        # 优先尝试 OpenAI 兼容格式
        result = self._call_openai_compat(httpx, messages, system_prompt, log)
        if result is not None:
            return result

        # 回退到 Claude 原生格式
        return self._call_claude_native(httpx, messages, system_prompt, log)

    def _call_openai_compat(
        self, httpx, messages: List[Dict[str, str]], system_prompt: str = '', log: str = ''
    ) -> str | None:
        """OpenAI 兼容格式调用，失败时：
        - 401/403/5xx 直接返回错误字符串（不回退）
        - 404/连接错误返回 None（回退到 Claude 格式）
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'content-type': 'application/json',
        }
        body: dict = {
            'model': self.model,
            'max_tokens': 4096,
            'messages': messages,
        }
        if system_prompt:
            body['messages'] = [{'role': 'system', 'content': system_prompt}] + messages
        try:
            resp = httpx.post(self.endpoint, headers=headers, json=body, timeout=60.0, follow_redirects=True)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except httpx.HTTPStatusError as e:
            detail = self._extract_error_detail(e.response)
            if e.response.status_code in (401, 403):
                return f'AI 响应生成失败（HTTP {e.response.status_code}）：{detail} [{log}]'
            if e.response.status_code >= 500:
                return f'AI 服务不可用（HTTP {e.response.status_code}）：{detail} [{log}]'
            return None
        except (httpx.TimeoutException, httpx.ConnectError, KeyError, ValueError):
            return None
        except Exception:
            return None

    @staticmethod
    def _extract_error_detail(response) -> str:
        try:
            return response.json().get('error', {}).get('message', str(response.status_code))
        except Exception:
            return str(response.status_code)

    def _call_claude_native(
        self, httpx, messages: List[Dict[str, str]], system_prompt: str = '', log: str = ''
    ) -> str:
        """Claude 原生格式调用"""
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }
        body: dict = {
            'model': self.model,
            'max_tokens': 4096,
            'messages': messages,
        }
        if system_prompt:
            body['system'] = system_prompt
        try:
            resp = httpx.post(self.endpoint, headers=headers, json=body, timeout=60.0, follow_redirects=True)
            resp.raise_for_status()
            return resp.json()['content'][0]['text']
        except httpx.TimeoutException:
            return 'AI 响应生成超时，请检查网络连接或稍后重试。'
        except httpx.HTTPStatusError as e:
            detail = ''
            try:
                detail = e.response.json().get('error', {}).get('message', str(e))
            except Exception:
                detail = str(e)
            return f'AI 响应生成失败（HTTP {e.response.status_code}）：{detail}'
        except Exception as e:
            return f'AI 响应生成出错：{e}'
