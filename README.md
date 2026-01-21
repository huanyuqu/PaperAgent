# Arxiv Paper Curation Agent

这是一个基于 Zotero 论文库自动筛选 Arxiv 论文的智能 Agent。它会每天检查 Arxiv 上的新论文，并结合您的 Zotero 收藏进行深度分析，生成包含中英文总结、顶会潜力评估及作者背景分析的 Markdown 报告。

## 隐私与安全建议 (Privacy & Security)

虽然本项目已做了充分的隐私保护处理，但仍**建议将此仓库设置为「私有仓库 (Private Repository)」**。

### 隐私保护设计
1. **研究兴趣隐私**：`zotero_interests.json` 和 `agent_state.json` 已加入 `.gitignore`。在 GitHub Actions 运行期间，这些数据通过 **Actions Cache** 机制在加密环境中流转，不会出现在 Git 提交历史中。
2. **报告安全**：生成的 `reports/` 仅在本地或 Actions 运行环境中存在，不会推送到仓库。
3. **API 安全**：敏感的 API Key 均通过环境变量或 GitHub Secrets 管理。

## GitHub Actions 自动化配置

本项目已配置 GitHub Actions，可实现每天定时自动运行并通过邮件推送报告。

### 配置步骤

1. **推送代码到 GitHub 仓库**：
   ```bash
   git remote add origin <你的仓库地址>
   git push -u origin main
   ```

2. **设置 GitHub Secrets**：
   在 GitHub 仓库页面，进入 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`，依次添加以下变量：

   | Secret 名称 | 说明 | 示例 |
   | :--- | :--- | :--- |
   | `OPENROUTER_API_KEY` | OpenRouter API Key | `sk-or-v1-xxxx` |
   | `OPENROUTER_BASE_URL` | API 地址 (可选) | `https://openrouter.ai/api/v1` |
   | `LLM_MODEL` | 使用的模型名称 | `anthropic/claude-3.5-sonnet` |
   | `LLM_REFERER` | OpenRouter 来源标识 (可选) | `https://github.com/your-username/repo` |
   | `LLM_TITLE` | OpenRouter 标题标识 (可选) | `Arxiv Paper Agent` |
   | `ZOTERO_USER_ID` | Zotero 用户 ID | `1234567` |
   | `ZOTERO_API_KEY` | Zotero API Key | `xxxx` |
   | `ZOTERO_GROUP_IDS` | 共享库 ID (逗号分隔, 可选) | `1234,5678` |
   | `ARXIV_CATEGORIES` | 关注的 Arxiv 分类 | `cs.CL,cs.AI,cs.LG` |
   | `SMTP_SERVER` | SMTP 服务器地址 | `smtp.gmail.com` |
   | `SMTP_PORT` | SMTP 端口 | `465` |
   | `SMTP_USER` | 发件邮箱账号 | `xxx@gmail.com` |
   | `SMTP_PASS` | 邮箱应用专用密码 | `xxxx xxxx xxxx xxxx` |
   | `RECIPIENT_EMAIL` | 收件人邮箱 | `target@example.com` |

   #### 💡 快速设置技巧 (使用 GitHub CLI)
   如果你安装了 [GitHub CLI (gh)](https://cli.github.com/)，可以使用以下一行命令将本地 `.env` 中的配置批量导入到 GitHub Secrets：
   ```bash
   grep -v '^#' .env | grep -v '^$' | gh secret set -f -
   ```

3. **如何获取 Gmail 应用专用密码？**
   - 登录 Google 账号，开启 **两步验证**。
   - 访问 [App passwords](https://myaccount.google.com/apppasswords) 页面。
   - 创建新应用（如 "Paper Agent"），获取 16 位专用密码。

4. **权限设置**：
   进入 `Settings` -> `Actions` -> `General`，确保 `Workflow permissions` 设置为 `Read and write permissions`。

### 运行机制
- **定时运行**：每天北京时间早上 9:00 (UTC 1:00) 自动触发。
- **增量更新 (Actions Cache)**：`agent_state.json` 和 `zotero_interests.json` 通过 GitHub Actions Cache 共享，确保每次只处理新论文，且不泄露个人数据到仓库历史。
- **报告分发**：报告通过邮件发送。如果需要查看本地生成的 Markdown 报告，可检查 Actions 运行记录或在本地运行。

## 本地运行
1. 安装依赖：`pip install -r requirements.txt`
2. 参考 `.env.example` 创建 `.env` 文件并填写配置。
3. 运行：`python main.py`
