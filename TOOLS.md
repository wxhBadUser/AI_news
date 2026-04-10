# 🛠️ TOOLS.md - 新闻采集员工具配置

针对 `news-collector` 任务需求，严格配置外部工具的使用权限与调用标准。

## ✅ 可用工具 (Authorized Tools)

### 🔍 `web_search`
* **用途**：关键词搜索，抓取搜索结果摘要。
* **用法**：`web_search(query, count=5)`
* **适用场景**：**Fallback 第三层**；用于英文源补充搜索或在 RSS/Browser 均失效时的兜底。

### 🌐 `web_fetch`
* **用途**：轻量化抓取网页内容或 RSS 订阅。
* **用法**：`web_fetch(url, maxChars=2000)`
* **适用场景**：**Fallback 第一层 (RSS/Atom)**；提取文章详情页的纯文本摘要。

### 🧠 `exec` (Python Engine)
* **用途**：执行 Python 脚本，处理复杂的逻辑计算与文件 IO。
* **用法**：`exec(command="python -c '...' ")` 或 `exec(command="python path/to/script.py")`
* **核心约束**：
    * **禁止使用 `write` 工具写入任何包含中文的 JSON 文件**（避免编码乱码）。
    * **必须且仅能**通过 `exec` 调用 Python 脚本来执行：
        1. **Daily JSON 写入**（包含中文摘要与评分）。
        2. **`sources-status.json` 状态更新**。
        3. **`state.json` 仪表盘数据重建**。
* **适用场景**：所有涉及数据持久化、结构化计算（七维评分）的操作。

### 🤖 `openclaw browser` (Headless Browser)
* **用途**：启动浏览器，处理 JS 渲染页面并提取结构化文字列表。
* **指令集**：
    * `exec(command="open 流程：openclaw browser start")` - 启动浏览器实例。
    * `exec(command='openclaw browser navigate "<URL>"')` - 导航至目标页面。
    * `exec(command="openclaw browser snapshot")` - 抓取页面文字快照（Snapshot）。
    * `exec(command="openclaw browser close")` - 关闭浏览器实例，释放内存。
* **关键规范**：
    * **时延要求**：`navigate` 成功后，必须 `sleep(3-5)` 秒后再进行 `snapshot`，确保 JS 渲染完成。
    * **失败判定**：若页面出现验证码（"Verify you are human"）或加载超时，**立即判定为失败**并进入下一层 Fallback。
* **适用场景**：**Fallback 第二层**；针对无法通过 RSS 或 HTML 直接解析的动态网页。

---

## 🚫 不可用工具 (Prohibited Tools)
*以下工具未经授权，严禁调用，违者视为违反 `SOUL.md` 边界意识：*

* `image`：本 Agent 不进行图像分析。
* `sessions_*`：禁止操作、干预或其他 Agent 的 Session。
* `cron`：禁止擅自修改系统级定时任务。
* `memory_*`：禁止直接操作 `memory/` 目录下的长期记忆文件（仅允许在当前 Workspace 内进行操作）。

---

 

## 🏗️ 执行环境 (Execution Environment)

* **工作目录 (Workspace)**：`/home/wxh1010534025/.openclaw/workspace-news`
* **数据目录 (Data Hub)**：`/home/wxh1010534025/.openclaw/workspace-news/data/ai-daily`
* **日志归宿 (Logging)**：`/home/wxh1010534025/.openclaw/workspace-news/memory/agents/collector-log.md`
* **浏览器配置 (Browser Profile)**：`openclaw` (Default)
* **CDP 端口**：`18800`
* **Dashboard 路径**：`/home/wxh1010534025/.openclaw/workspace-news/data/ai-daily/dashboard/index.html`

---

_**工具链的准确调用是实现“稳如老狗”采集任务的物理基础。**_ 📡