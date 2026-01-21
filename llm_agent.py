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

请按以下 JSON 格式输出分析结果：
{{
    "summary_cn": "基于提供的{text_type}，给出一个准确、深刻的中文总结（300字以内）",
    "summary_en": "An accurate and profound English summary based on the provided {text_type} (within 150 words)",
    "analysis_source": "{text_type}", // 必须原样返回 "{text_type}"
    "quality_evaluation": "对论文 quality 的深度评价",
    "top_conference_probability": 85, // 0-100，该文章被顶级会议（如 CVPR, ICML, NeurIPS, ICLR, ACL 等）录用的可能性估算
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
                    {"role": "system", "content": "你是一个学术辅助助手，擅长分析 Arxiv 论文。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
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
