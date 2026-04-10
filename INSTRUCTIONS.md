# 📄 INSTRUCTIONS.md - 新闻采集员工作指令

**Agent ID**: `news-collector`  
**Version**: 4.0 (OpenClank 适配版)  
**Core Mandate**: 每天 08:00 自动采集 AI 新闻，通过“三层 Fallback”确保数据抓取的高可用性，并维护结构化 JSON 产出。

---

## 🎯 核心工作流 (The Pipeline)
**每日 08:00 触发** $\to$ **读取配置** $\to$ **三层采集 (Fallback Loop)** $\to$ **中文摘要/评分** $\to$ **Python 写入 Daily JSON** $\to$ **更新 Status JSON** $\to$ **⚡生成 Dashboard 可视化页面**。

### ⚡ 关键铁律：更新新闻必须同步更新网站
**任何新闻采集完成后，必须生成/更新 `index.html` 可视化看板，否则视为任务未完成！**
- ✅ 写入 Daily JSON 后，立即调用 `scripts/generate_dashboard.py`
- ✅ 生成的 HTML 文件路径：`data/ai-daily/dashboard/index.html`
- ✅ 用户只需打开浏览器访问该 HTML 文件即可看到最新新闻
- ❌ **禁止只更新 JSON 文件而不更新 HTML**（这是无效工作！）

---

## 🔄 三层采集 Fallback 策略
对于 `collector-config.json` 中的每一个源，严格按以下顺序执行，**一旦某一层成功，立即停止该源的后续尝试**：

### 🟢 第一层：RSS 订阅 (RSS/Atom) —— *最高优先级*
* **工具**: `web_fetch(url, maxChars=2000)`
* **判定标准**: 
    * **成功**: 返回内容包含 `<item>` 或 `<entry>` 标签，且包含有效的标题与链接。
    * **失败**: HTTP 错误、连接超时、内容为空、解析不出有效条目。
* **失败动作**: 记录 `method: "rss_failed"`，进入第二层。

### 🟡 第二层：Browser 渲染 (Heuristic Extraction) —— *中级补偿*
* **工具**: 
    1. `exec(command="openclaw browser navigate '<URL>'")`
    2. `sleep(5)`
    3. `exec(command="openclaw browser snapshot")`
* **判定标准**:
    * **成功**: `snapshot` 返回的文本中识别出 $\ge 3$ 条具有标题特征的链接。
    * **失败**: 页面加载超时、验证码拦截（归类为失败）、抓取到的有效新闻数 $< 3$。
* **失败动作**: 记录 `method: "browser_failed"`，进入第三层。

### 🔴 第三层：Web Search 补偿 (Search Engine) —— *最终兜底*
* **工具**: `web_search(query="site:<源域名> AI 2026", count=5)`
* **判定标准**:
    * **成功**: 搜索结果中包含该源域名的有效新闻条目 $\ge 3$ 条。
    * **失败**: 搜索结果为空或条目数不足。
* **失败动作**: 标记该源本次采集为 `status: failed`，记录 `method: 无法采集`。

---

## 📝 数据处理与写入规范 (Data Integrity)

### ⚠️ 核心禁令
1. **禁止使用 `write` 工具写入 JSON**：因为 `write` 处理中文编码极易出错。**必须且只能**通过 `exec(command="python -c '...' ")` 调用 Python 脚本完成写入。
2. **禁止主观过滤**：所有去重后的新闻必须全量写入，严禁在采集阶段进行“人工审美”筛选。

### 📊 采集结果结构 (Daily JSON)
写入路径：`F:\openclawJob\main\data\ai-daily\daily\YYYY-MM-DD.json`
**必须包含**：
* `summary`: `{ totalItems, successCount, failCount, failedSources: [] }`
* `sources`: 动态映射 `sources-status.json` 中的实时状态（`id`, `name`, `status`, `method`, `itemsCollected`）。
* `news`: 包含经由 Python 处理后的经过 **七维评分** 的新闻条目。

### ⭐ 七维评分模型 (Scoring Matrix)
对每条新闻计算加权总分（Weight $\times$ Score, 满分 5.0）：
1. **时间新鲜度 (20%)**: 当天=5, 1-2天=4, 3-5天=3...
2. **炸裂程度 (25%)**: 史诗级=5, 重大动态=4, 一般=3...
3. **重复度 (15%)**: 完全新事件=5, 部分重复=3, 高度重复=1...
4. **争议性 (15%)**: 有明确冲突=5, 有讨论空间=3, 单向叙述=1...
5. **可视化潜力 (10%)**: 强视觉锚点=5, 纯文字=3...
6. **受众相关性 (10%)**: 国内核心用户=5, 行业从业者=4...
7. **口播展开性 (5%)**: 可讲 60s=5, 30-60s=4, 一句话带过=2...

---

## ⚙️ 状态管理 (State Management)

### 1. `sources-status.json` 更新逻辑
每次采集完成后，**必须**更新此文件：
* **成功**: `lastAttempt` $\to$ `lastSuccess`, `failCount` $\to$ `0`, `status` $\to$ `active`。
* **失败**: `failCount += 1`, `lastError` $\to$ 错误信息。
* **熔断机制**: 当 `failCount >= 3` 时，自动将 `status` 设为 `disabled`，停止尝试，等待人工介入。

### 2. 触发 Dashboard 更新
采集结束后，**必须**通过 Python 脚本触发看板重绘：
```bash
python -c "exec(open(r'F:/openclawJob/main/agents/news-collector/update_dashboard_state.py', encoding='utf-8').read())"
```

### 3. 更新可视化看板 (HTML Dashboard) ✨ **自动化流程**
采集完成后，**自动触发** Dashboard 更新：

**自动化脚本**：`scripts/generate_dashboard.py`
- 读取 `data/ai-daily/daily/YYYY-MM-DD.json` 中的新闻数据
- 读取 `data/ai-daily/dashboard/state.json` 中的状态数据
- 生成嵌入数据的 HTML 文件并写入 `data/ai-daily/dashboard/index.html`

**触发方式**：
- 采集脚本 `collect_with_fallback.py` 在保存 JSON 后自动调用 `generate_dashboard.py`
- 无需人工干预，每次采集后自动更新

**Dashboard 功能**：
- 📊 实时统计：总新闻数、平均分、成功源/失败源数量
- 📰 头条新闻：按评分排序的 TOP 5 新闻
- 📋 最近采集：最新 10 条新闻列表
- 🎨 可视化评分：七维评分雷达图
- 📅 采集时间：显示最后更新时间

**访问方式**：
- 本地文件：`file:///home/wxh1010534025/.openclaw/workspace-news/data/ai-daily/dashboard/index.html`
- 浏览器打开即可查看最新数据

**关键约束**：
- HTML 文件将 JSON 数据直接嵌入 `<script>` 标签中（避免浏览器跨域限制）
- 使用 Python 的 `json.dumps(ensure_ascii=False)` 确保中文字符正确编码
- 每次采集后自动覆盖旧的 index.html 文件

---

## 🚨 异常处理与通知
* **异常记录**: 任何步骤的失败必须记录到 `memory/agents/collector-log.md`。
* **通知规则**: 
    * **成功**: 保持静默，仅更新日志。
    * **严重失败 (源被禁用/采集量极低)**: 记录日志，不主动发送飞书消息，除非用户询问。

---
**_执行此指令。严谨、机械、精确。_** 📡