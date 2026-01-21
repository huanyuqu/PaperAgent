import os
import datetime

class ReportGenerator:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_markdown(self, analyzed_papers):
        """
        生成 Markdown 格式的论文报告
        """
        if not analyzed_papers:
            print("No papers to generate report.")
            return None

        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"Arxiv_Report_{date_str}.md"
        file_path = os.path.join(self.output_dir, filename)

        md_content = f"# 每日 Arxiv 论文推荐报告 ({date_str})\n\n"
        md_content += f"基于您的 Zotero 兴趣库为您筛选了以下 {len(analyzed_papers)} 篇论文：\n\n"
        md_content += "---\n\n"

        for p in analyzed_papers:
            source = p['analysis'].get('analysis_source', '未知来源')
            source_emoji = "📄" if "全文" in source else "📝"
            conf_prob = p['analysis'].get('top_conference_probability', 0)
            author_eval = p['analysis'].get('author_expert_evaluation', '暂无评估')
            
            md_content += f"### [{p['title']}]({p['url']})\n\n"
            md_content += f"- **分析来源:** {source_emoji} `{source}`\n"
            md_content += f"- **作者:** {', '.join(p['authors'])}\n"
            md_content += f"- **背景评估:** {author_eval}\n"
            md_content += f"- **顶会潜力:** ` {conf_prob}% `\n"
            md_content += f"- **相关度评分:** `{p['analysis']['relevance_score']}/10`\n"
            md_content += f"- **中文总结:** {p['analysis'].get('summary_cn', p['analysis'].get('summary', '无'))}\n"
            md_content += f"- **English Summary:** {p['analysis'].get('summary_en', 'N/A')}\n"
            md_content += f"- **质量评价:** {p['analysis']['quality_evaluation']}\n"
            md_content += f"- **推荐理由:** {p['analysis']['recommendation_reason']}\n"
            md_content += f"- **PDF 链接:** [下载 PDF]({p['pdf_url']})\n\n"
            md_content += "---\n\n"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"Report generated successfully: {file_path}")
            return file_path
        except Exception as e:
            print(f"Error generating report: {e}")
            return None

if __name__ == "__main__":
    generator = ReportGenerator()
    test_data = [{
        'title': 'Test Paper',
        'url': 'http://arxiv.org/abs/1234.5678',
        'pdf_url': 'http://arxiv.org/pdf/1234.5678',
        'analysis': {
            'relevance_score': 9,
            'summary': '这是一个测试总结。',
            'quality_evaluation': '质量良好。',
            'recommendation_reason': '非常匹配。'
        }
    }]
    generator.generate_markdown(test_data)
