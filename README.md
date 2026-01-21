# Arxiv Paper Curation Agent

这是一个基于 Zotero 兴趣库自动筛选 Arxiv 论文的智能 Agent。它会每天检查 Arxiv 上的新论文，并结合您的 Zotero 收藏进行深度分析，生成包含中英文总结、顶会潜力评估及作者背景分析的 Markdown 报告。

## 隐私与安全建议 (Privacy & Security)

:warning: **强烈建议将此仓库设置为「私有仓库 (Private Repository)」**。

### 为什么建议私有？
1. **研究兴趣隐私**：`zotero_interests.json` 会记录您的论文收藏标题和 LLM 生成的用户画像，`reports/` 包含为您定制的科研分析，这些信息可能属于您的学术隐私。
2. **状态持久化**：为了实现增量更新，Agent 需要将运行状态提交回仓库。在私有仓库中，这些状态文件的变动对外界不可见。
3. **API 安全**：虽然敏感的 API Key 已通过 GitHub Secrets 管理，但私有仓库能提供多一层的安全防护。

## GitHub Actions 自动化配置

本项目已配置 GitHub Actions，可实现每天定时自动运行并推送报告。

### 配置步骤

1. **推送代码到 GitHub 仓库**：
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <你的仓库地址>
   git push -u origin main
   ```

2. **设置 GitHub Secrets**：
   在 GitHub 仓库页面，进入 `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`，依次添加以下变量：

   | Secret 名称 | 说明 | 示例 |
   | :--- | :--- | :--- |
   | `OPENROUTER_API_KEY` | OpenRouter API Key | `sk-or-v1-xxxx` |
   | `OPENROUTER_BASE_URL` | OpenRouter API 地址 | `https://openrouter.ai/api/v1` |
   | `LLM_MODEL` | 使用的模型名称 | `google/gemini-2.0-flash-exp:free` |
   | `ZOTERO_USER_ID` | Zotero 用户 ID | `1234567` |
   | `ZOTERO_GROUP_IDS` | 共享库 ID (逗号分隔) | `1234,5678` |
   | `ZOTERO_API_KEY` | Zotero API Key | `xxxx` |
   | `ARXIV_CATEGORIES` | 关注的 Arxiv 分类 (逗号分隔) | `cs.CL,cs.AI,cs.LG` |
| `SMTP_SERVER` | SMTP 服务器地址 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | Gmail 邮箱账号 | `xxx@gmail.com` |
| `SMTP_PASS` | Gmail 应用专用密码 | `xxxx xxxx xxxx xxxx` |
| `RECIPIENT_EMAIL` | 收件人邮箱 | `target@example.com` |

### 如何获取 Gmail 应用专用密码 (App Password)？
1. 登录您的 Google 账号，开启 **两步验证 (2-Step Verification)**。
2. 访问 [App passwords](https://myaccount.google.com/apppasswords) 页面。
3. 创建一个新的应用名称（例如 "Paper Agent"），Google 会生成一个 16 位的专用密码。
4. 将该密码填入 `.env` 或 GitHub Secrets 的 `SMTP_PASS` 中。

3. **权限设置**：  进入 `Settings` -> `Actions` -> `General`，确保 `Workflow permissions` 设置为 `Read and write permissions`，这样 Actions 才能自动提交更新后的报告和缓存状态。

### 运行机制
- **定时运行**：每天北京时间早上 9:00 (UTC 1:00) 自动触发。
- **状态持久化 (Actions Cache)**：为了保护隐私，`agent_state.json` 和 `zotero_interests.json` 不会提交到 Git 仓库，而是通过 GitHub Actions 的 Cache 机制在多次运行之间共享。这既保证了增量更新的效率，又确保了您的研究兴趣不会出现在代码提交历史中。
- **报告生成**：新报告将保存在 `reports/` 目录下（本地可见，GitHub Actions 运行后不会推送到仓库）。

## 本地运行
1. 安装依赖：`pip install -r requirements.txt`
2. 配置 `.env` 文件。
3. 运行：`python main.py`
