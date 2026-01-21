import logging
import os
import json
import datetime
from main import PaperAgent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FastTestAgent(PaperAgent):
    def run_test(self, limit_papers=2):
        logging.info(f"🚀 开始快速测试模式 (仅处理 {limit_papers} 篇论文)...")
        
        # 1. 快速获取 Arxiv 论文
        categories_str = os.getenv('ARXIV_CATEGORIES', 'cs.CL,cs.AI')
        categories = [c.strip() for c in categories_str.split(',')]
        logging.info(f"正在从 Arxiv 抓取论文: {categories}...")
        
        # 仅获取少量论文用于测试
        raw_papers = self.arxiv.fetch_by_categories(categories, max_results=limit_papers)
        logging.info(f"获取到 {len(raw_papers)} 篇待测试论文。")

        if not raw_papers:
            logging.error("未获取到论文，测试停止。")
            return

        # 2. 模拟/快速获取兴趣点
        # 如果 zotero_interests.json 存在则读取，否则使用模拟数据，避免第一次运行太慢
        if os.path.exists("zotero_interests.json"):
            logging.info("读取本地 Zotero 缓存...")
            with open("zotero_interests.json", "r") as f:
                cache = json.load(f)
                user_interests = cache.get("summarized_profile")
                if not user_interests:
                    user_interests = ", ".join(cache.get("interests", [])[:10])
        else:
            logging.info("未发现缓存，使用模拟兴趣点进行快速测试...")
            user_interests = "Large Language Models, AI Agents, Machine Learning"

        # 3. 分析（处理前 limit_papers 篇，包含全文分析）
        analyzed_papers = []
        for paper in raw_papers[:limit_papers]:
            logging.info(f"🧪 正在快速初步筛选: {paper['title']}")
            # 第一步：初步筛选
            analysis = self.llm.analyze_paper(paper, user_interests)
            
            if analysis:
                logging.info(f"🧪 初步筛选通过，正在下载全文进行深度分析测试: {paper['title']}")
                full_text = self.arxiv.download_pdf_text(paper['pdf_url'])
                
                if full_text:
                    # 使用全文进行二次深度分析
                    deep_analysis = self.llm.analyze_paper(paper, user_interests, full_text=full_text)
                    if deep_analysis:
                        paper['analysis'] = deep_analysis
                        analyzed_papers.append(paper)
                        logging.info(f"✅ 全文深度分析完成: {paper['title']}")
                else:
                    logging.warning(f"⚠️ 全文下载失败，回退至摘要分析: {paper['title']}")
                    paper['analysis'] = analysis
                    analyzed_papers.append(paper)
        
        # 4. 生成并发送测试报告
        if analyzed_papers:
            logging.info(f"正在生成测试报告...")
            report_path = self.report.generate_markdown(analyzed_papers)
            
            # 读取内容发送邮件测试
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            logging.info("正在发送测试邮件...")
            subject = f"🚀 Paper Agent Test Run - {datetime.date.today().isoformat()}"
            success = self.email.send_report(subject, report_content)
            
            if success:
                logging.info(f"✅ 测试成功！报告已生成并发送邮件。")
            else:
                logging.info(f"⚠️ 报告已生成，但邮件发送失败，请检查 .env 配置。")
            
            logging.info(f"报告本地路径: {report_path}")
        else:
            logging.info("未产生分析结果，请检查 Arxiv 分类或 LLM 配置。")

if __name__ == "__main__":
    # 确保环境加载
    from dotenv import load_dotenv
    load_dotenv()
    
    test_agent = FastTestAgent()
    # 仅测试 2 篇论文，且不下载全文，只看摘要和中英文输出是否正常
    test_agent.run_test(limit_papers=2)
