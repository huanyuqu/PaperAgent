import logging
import json
import os
import datetime
from zotero_client import ZoteroClient
from arxiv_client import ArxivClient
from llm_agent import LLMAgent
from report_generator import ReportGenerator
from email_sender import EmailSender

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PaperAgent:
    def __init__(self):
        self.zotero = ZoteroClient()
        self.arxiv = ArxivClient()
        self.llm = LLMAgent()
        self.report = ReportGenerator()
        self.email = EmailSender()
        self.debug_dir = "debug"
        self.state_file = "agent_state.json"
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)

    def _get_last_run_time(self):
        """获取上次运行时间"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    last_run_str = state.get('last_run_time')
                    if last_run_str:
                        return datetime.datetime.fromisoformat(last_run_str)
            except Exception as e:
                logging.error(f"读取状态文件失败: {e}")
        return None

    def _save_last_run_time(self, timestamp):
        """保存当前运行时间"""
        try:
            state = {'last_run_time': timestamp.isoformat()}
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logging.error(f"保存状态文件失败: {e}")

    def _save_debug_data(self, data, filename):
        """保存调试数据到 JSON 文件"""
        file_path = os.path.join(self.debug_dir, filename)
        try:
            # 处理 datetime 对象，使其可 JSON 序列化
            def datetime_handler(x):
                if hasattr(x, 'isoformat'):
                    return x.isoformat()
                return str(x)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=datetime_handler)
            logging.info(f"调试数据已保存至: {file_path}")
        except Exception as e:
            logging.error(f"保存调试数据 {filename} 失败: {e}")

    def run(self):
        logging.info("开始执行每日论文推荐任务...")
        
        # 获取上次运行时间
        last_run_time = self._get_last_run_time()
        current_run_time = datetime.datetime.now(datetime.timezone.utc)
        
        if last_run_time:
            logging.info(f"上次运行时间: {last_run_time.isoformat()}")
        else:
            logging.info("首次运行，将获取最近的论文。")

        # 1. 从 Arxiv 获取指定分类的新论文
        categories_str = os.getenv('ARXIV_CATEGORIES', 'cs.DC,cs.AR')
        categories = [c.strip() for c in categories_str.split(',')]
        logging.info(f"正在从 Arxiv 抓取分类论文: {categories}...")
        
        # 增加 max_results 以确保在增量抓取时不会漏掉
        raw_papers = self.arxiv.fetch_by_categories(categories, max_results=100, since_date=last_run_time)
        self._save_debug_data(raw_papers, "1_arxiv_raw_papers.json")
        logging.info(f"抓取到 {len(raw_papers)} 篇自上次运行以来的新论文。")

        if not raw_papers:
            logging.warning("未能从 Arxiv 获取到论文，请检查网络或分类设置。")
            return

        # 2. 从 Zotero 获取兴趣主题作为筛选标准
        logging.info("正在从 Zotero 获取兴趣主题...")
        topics, is_updated, cached_profile = self.zotero.get_recent_paper_topics(limit=50)
        self._save_debug_data(topics, "2_zotero_topics.json")
        
        if not topics:
            logging.warning("未能从 Zotero 获取到主题，将使用默认推荐逻辑。")
            user_interests = "General AI and Computer Science"
        else:
            # 如果 Zotero 兴趣有更新，或者还没有生成过画像，则调用 LLM 生成
            if is_updated or not cached_profile:
                logging.info("检测到兴趣更新或画像缺失，正在生成 LLM 兴趣画像总结...")
                user_interests = self.llm.summarize_interests(topics)
                self.zotero.update_summarized_profile(user_interests)
                logging.info(f"新生成的兴趣画像: {user_interests}")
            else:
                logging.info("使用缓存的兴趣画像。")
                user_interests = cached_profile
                logging.info(f"当前兴趣画像: {user_interests}")

        # 3. 使用 LLM 根据兴趣筛选和分析论文
        analyzed_papers = []
        for paper in raw_papers:
            logging.info(f"正在进行初步筛选: {paper['title']}")
            # 第一步：基于摘要进行初步筛选
            analysis = self.llm.analyze_paper(paper, user_interests)
            
            if analysis:
                # 过滤低质量或不相关的论文
                if analysis.get('is_low_quality', False) or analysis.get('relevance_score', 0) < 7:
                    logging.info(f"初步筛选跳过论文: {paper['title']} (Score: {analysis.get('relevance_score', 0)})")
                    continue
                
                # 第二步：对于初步筛选通过的论文，下载全文进行深度分析
                logging.info(f"初步筛选通过，正在下载全文进行深度分析: {paper['title']}")
                full_text = self.arxiv.download_pdf_text(paper['pdf_url'])
                
                if full_text:
                    # 使用全文进行二次深度分析
                    deep_analysis = self.llm.analyze_paper(paper, user_interests, full_text=full_text)
                    if deep_analysis:
                        paper['analysis'] = deep_analysis
                        analyzed_papers.append(paper)
                        logging.info(f"深度分析完成: {paper['title']}")
                else:
                    # 如果全文下载失败，保留初次分析结果
                    logging.warning(f"全文下载失败，使用摘要分析结果: {paper['title']}")
                    paper['analysis'] = analysis
                    analyzed_papers.append(paper)
        
        self._save_debug_data(analyzed_papers, "3_analyzed_papers.json")

        # 4. 生成并发送报告
        if analyzed_papers:
            # 按相关度排序
            analyzed_papers.sort(key=lambda x: x['analysis']['relevance_score'], reverse=True)
            
            # 生成本地 Markdown 报告
            report_md_path = self.report.generate_markdown(analyzed_papers)
            
            # 读取 Markdown 内容用于发送邮件
            with open(report_md_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # 发送邮件
            logging.info("正在发送邮件报告...")
            subject = f"Arxiv Daily Paper Curation - {datetime.date.today().isoformat()}"
            self.email.send_report(subject, report_content)
            logging.info(f"报告已保存至: {report_md_path}")
        else:
            logging.info("没有找到符合条件的论文，未生成报告。")

        # 任务成功完成后，更新运行时间
        self._save_last_run_time(current_run_time)
        logging.info("任务执行完毕，已更新运行时间。")

if __name__ == "__main__":
    agent = PaperAgent()
    agent.run()
