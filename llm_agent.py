import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENROUTER_BASE_URL') or os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1'),
            default_headers={
                "HTTP-Referer": os.getenv('LLM_REFERER') or 'https://github.com/your-username/your-repo',
                "X-Title": os.getenv('LLM_TITLE') or 'Arxiv Paper Agent',
            }
        )
        self.model = os.getenv('LLM_MODEL', 'anthropic/claude-3.5-sonnet')

    def summarize_interests(self, topics):
        """
        根据 Zotero 的原始话题/标题列表，生成简洁的用户兴趣画像
        """
        if not topics:
            return "General AI and Computer Science"
            
        topics_str = "\n".join([f"- {t}" for t in topics[:200]]) # 最多取 200 条进行总结
        
        prompt = f"""
你是一个专业的科研助理。以下是从用户的 Zotero 论文库中提取的论文标题和标签列表。
请分析这些数据，并总结出用户目前的核心研究兴趣和关注的领域。

要求：
1. 总结要精炼，不超过 300 字。
2. 涵盖主要的学术关键词、研究方向和可能感兴趣的技术手段。
3. 使用中文输出。

原始数据列表：
{topics_str}

请直接输出总结后的用户画像内容：
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个擅长总结学术背景的助手。"},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error summarizing interests: {e}")
            return "General AI and Computer Science"

    def _parse_json(self, text):
        """
        更加鲁棒地解析 LLM 返回的 JSON 字符串
        """
        if not text:
            return None
            
        # 1. 移除 Markdown 代码块标识
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 2. 尝试修复常见的 JSON 错误
            try:
                import re
                
                # a. 处理未转义的控制字符（特别是换行符）
                # 很多 LLM 会在字符串中间直接打换行符，这在 JSON 中是不合法的
                # 我们将其替换为空格，这样不会破坏 JSON 结构
                fixed_text = re.sub(r'\n', ' ', text)
                
                # b. 修复未转义的反斜杠 (针对 LaTeX)
                # JSON 只允许特定的转义序列: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
                # 剩下的反斜杠（如 \alpha, \sum）都必须转义为 \\
                # 我们排除掉可能是合法转义的情况。注意：\beta 中的 \b 会被误判为退格符，
                # 我们通过正则排除掉后面跟着字母的情况（如果是 \beta，我们希望它变成 \\beta）
                fixed_text = re.sub(r'\\(?!(u[0-9a-fA-F]{4}|["\\/]|[bfnrt]([^a-zA-Z]|$)))', r'\\\\', fixed_text)
                
                # 特殊处理：如果 LaTeX 中出现了 \beta, \alpha 等，且 \b 被错误识别为 backspace
                # 这是一个权衡。在论文场景下，\beta 远比退格符常见。
                # 如果发现 \x08 (backspace)，很可能是 \beta 被误转义了
                # 但在原始字符串中它是 \b，所以我们可以在转义前先处理一下
                
                # c. 移除尾随逗号
                fixed_text = re.sub(r',\s*([\]}])', r'\1', fixed_text)
                
                # 尝试解析修复后的结果
                try:
                    return json.loads(fixed_text)
                except:
                    # d. 尝试处理单引号 (如果 JSON 还是解析失败)
                    better_fixed = re.sub(r"'(\w+)':", r'"\1":', fixed_text)
                    better_fixed = re.sub(r":\s*'([^']*)'", r': "\1"', better_fixed)
                    return json.loads(better_fixed)
            except Exception as e2:
                print(f"JSON repair failed for content: {text[:200]}...")
                print(f"Error details: {e2}")
                return None

    def analyze_paper(self, paper_info, user_interests, full_text=None):
        """
        分析单篇论文：总结、评价质量、打分
        """
        context_text = full_text if full_text else paper_info['summary']
        text_type = "全文提取内容" if full_text else "摘要"

        prompt = f"""
你是一个资深的学术论文分析专家和计算机科学家。请根据以下论文信息和用户的兴趣主题，对论文进行深度分析。

用户兴趣主题：
{user_interests}

论文信息：
标题: {paper_info['title']}
作者: {", ".join(paper_info['authors'])}
备注: {paper_info.get('comment', '无')}
{text_type}:
{context_text}

请注意：如果提供的是全文提取内容，请基于全文进行更深入的分析，而不仅仅是摘要。

请严格按以下 JSON 格式输出分析结果。不要包含任何额外的解释文字，确保所有的反斜杠都已经正确转义（特别是数学公式或特殊符号），并且不要在最后一个字段后加逗号。

{{
    "summary_cn": "基于提供的{text_type}，给出一个准确、深刻的中文总结（300字以内）",
    "summary_en": "An accurate and profound English summary based on the provided {text_type} (within 150 words)",
    "analysis_source": "{text_type}",
    "quality_evaluation": "对论文 quality 的深度评价",
    "top_conference_probability": 85,
    "author_expert_evaluation": "评估作者是否为该领域的知名专家，以及文章是否来自于顶级名校或顶尖研究机构（如 Google, OpenAI, Stanford 等）",
    "relevance_score": 10,
    "is_low_quality": false,
    "recommendation_reason": "结合全文给出的推荐理由或不推荐理由"
}}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个学术辅助助手，擅长分析 Arxiv 论文。你必须仅输出有效的 JSON。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            result = self._parse_json(content)
            if result:
                # 确保关键字段存在
                required_fields = ['recommendation_reason', 'quality_evaluation', 'relevance_score']
                for field in required_fields:
                    if field not in result:
                        result[field] = '无' if field != 'relevance_score' else 0
                return result
            else:
                print(f"Failed to parse LLM JSON response: {content[:200]}...")
                return None
        except Exception as e:
            print(f"Error analyzing paper with LLM: {e}")
            return None

if __name__ == "__main__":
    agent = LLMAgent()
    test_paper = {
        'title': 'Attention Is All You Need',
        'summary': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...',
        'authors': ['Ashish Vaswani', 'Noam Shazeer'],
        'comment': '15 pages'
    }
    result = agent.analyze_paper(test_paper, "Transformer, NLP, Deep Learning")
    print(json.dumps(result, indent=2, ensure_ascii=False))
