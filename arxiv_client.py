import arxiv
import datetime
import requests
import io
import os
from pypdf import PdfReader
from typing import List

class ArxivClient:
    def __init__(self):
        self.client = arxiv.Client()

    def download_pdf_text(self, pdf_url: str, max_pages: int = 15) -> str:
        """
        下载 PDF 并提取文本
        """
        try:
            response = requests.get(pdf_url)
            if response.status_code != 200:
                return ""
            
            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)
            
            text = ""
            # 限制页数，防止全文过长超出 LLM 上下文
            num_pages = min(len(reader.pages), max_pages)
            for i in range(num_pages):
                text += reader.pages[i].extract_text() + "\n"
            
            return text
        except Exception as e:
            print(f"提取 PDF 文本失败 ({pdf_url}): {e}")
            return ""

    def fetch_by_categories(self, categories: List[str], max_results=100, since_date=None):
        """
        根据分类获取最近的论文，支持时间戳过滤
        """
        if not categories:
            return []
        
        # 构造分类查询语句，例如 cat:cs.CL OR cat:cs.AI
        query = " OR ".join([f'cat:{cat}' for cat in categories])
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        for result in self.client.results(search):
            # 如果提供了 since_date，则过滤掉之前的论文
            if since_date and result.published <= since_date:
                continue
                
            papers.append({
                'title': result.title,
                'summary': result.summary,
                'url': result.entry_id,
                'pdf_url': result.pdf_url,
                'authors': [author.name for author in result.authors],
                'published': result.published,
                'comment': result.comment if result.comment else ""
            })
        
        return papers

    def search_papers(self, keywords: List[str], max_results=20):
        """
        根据关键词搜索最近的论文
        """
        if not keywords:
            return []
        
        # 简单地将关键词拼接成查询语句，或者取前几个重要的
        query = " OR ".join([f'abs:"{k}"' for k in keywords[:5]])
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        for result in self.client.results(search):
            papers.append({
                'title': result.title,
                'summary': result.summary,
                'url': result.entry_id,
                'pdf_url': result.pdf_url,
                'authors': [author.name for author in result.authors],
                'published': result.published,
                'comment': result.comment if result.comment else ""
            })
        
        return papers

if __name__ == "__main__":
    client = ArxivClient()
    papers = client.search_papers(["Large Language Models", "Agent"])
    for p in papers[:2]:
        print(f"Title: {p['title']}")
        print(f"Published: {p['published']}")
        print("-" * 20)
