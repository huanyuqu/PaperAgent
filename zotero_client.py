import os
import re
import json
from pyzotero import zotero
from dotenv import load_dotenv

load_dotenv()

class ZoteroClient:
    def __init__(self):
        self.api_key = os.getenv('ZOTERO_API_KEY')
        self.user_id = os.getenv('ZOTERO_USER_ID')
        self.group_ids_str = os.getenv('ZOTERO_GROUP_IDS', '')
        self.cache_file = "zotero_interests.json"
        
        self.zot_instances = []
        
        # 初始化个人库实例
        if self.user_id:
            self.zot_instances.append(zotero.Zotero(self.user_id, 'user', self.api_key))
            
        # 初始化所有共享库实例
        if self.group_ids_str:
            group_ids = [gid.strip() for gid in self.group_ids_str.split(',') if gid.strip()]
            for gid in group_ids:
                self.zot_instances.append(zotero.Zotero(gid, 'group', self.api_key))

    def _is_noise(self, text):
        """
        判断是否为 ID 格式的噪声（如 Arxiv ID 2509.00531v1）
        """
        # 匹配类似 1234.5678v1 的格式
        arxiv_pattern = r'^\d{4}\.\d{4,5}(v\d+)?$'
        if re.match(arxiv_pattern, text):
            return True
        # 匹配纯数字
        if text.isdigit():
            return True
        return False

    def _load_cache(self):
        """加载本地缓存的兴趣主题和版本号"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取 Zotero 缓存失败: {e}")
        return {"interests": [], "library_versions": {}, "summarized_profile": ""}

    def _save_cache(self, interests, library_versions, summarized_profile=None):
        """保存兴趣主题和版本号到本地"""
        try:
            cache = self._load_cache()
            data = {
                "interests": list(set(interests)),
                "library_versions": library_versions,
                "summarized_profile": summarized_profile if summarized_profile else cache.get("summarized_profile", "")
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存 Zotero 缓存失败: {e}")

    def get_recent_paper_topics(self, limit=50):
        """
        增量式获取 Zotero 兴趣主题
        返回: (all_interests, is_updated, cached_profile)
        """
        cache = self._load_cache()
        cached_interests = cache.get("interests", [])
        library_versions = cache.get("library_versions", {})
        cached_profile = cache.get("summarized_profile", "")
        
        new_interests = []
        updated_versions = library_versions.copy()
        is_updated = False
        
        is_first_run = not os.path.exists(self.cache_file)
        
        for zot in self.zot_instances:
            lib_key = f"{zot.library_type}:{zot.library_id}"
            last_version = library_versions.get(lib_key, 0)
            
            try:
                # 获取当前库的最新版本号
                current_version = zot.items(limit=1)[0]['version'] if zot.items(limit=1) else last_version
                
                # 如果是第一次运行，或者版本有更新
                if is_first_run or current_version > last_version:
                    is_updated = True
                    # 如果是第一次运行，我们可能需要抓取更多条目来构建初始画像
                    fetch_limit = 200 if is_first_run else limit
                    
                    # 使用 since 参数进行增量抓取（如果不是第一次运行）
                    if last_version > 0:
                        items = zot.everything(zot.items(since=last_version))
                    else:
                        items = zot.top(limit=fetch_limit)
                    
                    for item in items:
                        # 获取标题
                        title = item.get('data', {}).get('title', '')
                        if title and not self._is_noise(title):
                            new_interests.append(title)
                        
                        # 获取标签
                        tags = item.get('data', {}).get('tags', [])
                        for tag in tags:
                            tag_text = tag.get('tag', '')
                            if tag_text and not self._is_noise(tag_text):
                                new_interests.append(tag_text)
                    
                    updated_versions[lib_key] = current_version
                else:
                    print(f"Zotero 库 {lib_key} 无更新 (version: {last_version})")
                    
            except Exception as e:
                print(f"获取 Zotero 库 {lib_key} 更新失败: {e}")
        
        # 合并旧兴趣和新兴趣
        all_interests = list(set(cached_interests + new_interests))
        
        # 如果有新内容，更新缓存（此时暂不更新 profile，由 main.py 总结后更新）
        if is_updated:
            self._save_cache(all_interests, updated_versions, cached_profile)
        
        return all_interests, is_updated, cached_profile

    def update_summarized_profile(self, profile):
        """手动更新缓存中的总结画像"""
        cache = self._load_cache()
        self._save_cache(cache['interests'], cache['library_versions'], profile)

if __name__ == "__main__":
    client = ZoteroClient()
    topics, updated, profile = client.get_recent_paper_topics()
    print(f"Found {len(topics)} topics from Zotero. Updated: {updated}")
    print(f"Current Profile: {profile}")
    for t in topics[:10]:
        print(f"- {t}")
