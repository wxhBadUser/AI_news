#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 新闻可视化 Dashboard 生成器
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "ai-daily"
DAILY_DIR = DATA_DIR / "daily"
DASHBOARD_DIR = DATA_DIR / "dashboard"
STATUS_FILE = DATA_DIR / "status" / "sources-status.json"

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载失败 {file_path}: {e}")
        return None

def get_latest_daily_file():
    if not DAILY_DIR.exists():
        return None
    json_files = list(DAILY_DIR.glob("*.json"))
    if not json_files:
        return None
    json_files.sort(reverse=True)
    return json_files[0]

def get_all_daily_files():
    if not DAILY_DIR.exists():
        return []
    json_files = list(DAILY_DIR.glob("*.json"))
    json_files.sort(reverse=True)
    return json_files

def generate_html(news_data, sources_status):
    date = news_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    total_count = news_data.get('total_count', 0)
    score_distribution = news_data.get('score_distribution', {})
    news_list = news_data.get('news', [])
    
    all_dates = [f.stem for f in get_all_daily_files()]
    
    # 来源状态
    sources_html = ""
    if sources_status:
        sources_dict = sources_status.get('sources', sources_status)  # 兼容两种格式
        for source_id, source_info in sources_dict.items():
            if isinstance(source_info, dict):  # 确保是字典
                status = source_info.get('status', 'unknown')
                status_color = '#10b981' if status == 'active' else '#ef4444'
                status_text = '✓ 活跃' if status == 'active' else '✗ 失效'
                sources_html += f'''
            <div class="source-card">
                <div class="source-name">{source_info.get("name", source_id)}</div>
                <div class="source-status" style="color: {status_color}">{status_text}</div>
                <div class="source-meta">采集: {source_info.get("itemsCollected", 0)} 条</div>
            </div>'''
    
    # 新闻列表
    news_html = ""
    for idx, news in enumerate(news_list, 1):
        total_score = news.get('total_score', 0)
        if total_score >= 55:
            score_class, score_color = 'high', '#10b981'
        elif total_score >= 45:
            score_class, score_color = 'medium', '#f59e0b'
        else:
            score_class, score_color = 'low', '#6b7280'
        
        scores = news.get('scores', {})
        scores_html = ""
        for score_name, score_value in scores.items():
            scores_html += f'''
            <div class="score-item">
                <span class="score-label">{score_name}</span>
                <div class="score-bar"><div class="score-fill" style="width: {score_value * 10}%"></div></div>
                <span class="score-value">{score_value}</span>
            </div>'''
        
        tags = news.get('tags', [])
        tags_html = "".join([f'<span class="tag">{tag}</span>' for tag in tags])
        
        news_html += f'''
        <div class="news-card" data-score="{score_class}">
            <div class="news-header">
                <div class="news-rank">#{idx}</div>
                <div class="news-title">{news.get("title", "无标题")}</div>
                <div class="news-score" style="background: {score_color}">{total_score}分</div>
            </div>
            <div class="news-meta">
                <span>📍 {news.get("source", "未知")}</span>
                <span>🕐 {news.get("publish_time", "").split("T")[0]}</span>
            </div>
            <div class="news-summary">{news.get("summary", "")}</div>
            <div class="news-tags">{tags_html}</div>
            <div class="news-scores"><div class="scores-title">📊 七维评分</div>{scores_html}</div>
            <div class="news-footer"><a href="{news.get('url', '#')}" target="_blank">查看原文 →</a></div>
        </div>'''
    
    dates_html = ""
    for d in all_dates:
        selected = 'selected' if d == date else ''
        dates_html += f'<option value="{d}" {selected}>{d}</option>'
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 新闻日报 - {date}</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px;}}
.container {{max-width:1400px;margin:0 auto;}}
.header {{background:white;border-radius:16px;padding:30px;margin-bottom:20px;box-shadow:0 10px 40px rgba(0,0,0,0.1);}}
.header-top {{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}}
.title {{font-size:32px;font-weight:700;color:#1a202c;}}
.stats {{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-top:20px;}}
.stat-card {{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:20px;border-radius:12px;text-align:center;}}
.stat-value {{font-size:36px;font-weight:700;margin-bottom:5px;}}
.main-content {{display:grid;grid-template-columns:1fr 300px;gap:20px;}}
.news-section {{display:flex;flex-direction:column;gap:20px;}}
.news-card {{background:white;border-radius:16px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,0.08);transition:transform 0.3s;}}
.news-card:hover {{transform:translateY(-4px);}}
.news-header {{display:flex;align-items:flex-start;gap:15px;margin-bottom:15px;}}
.news-rank {{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;}}
.news-title {{flex:1;font-size:20px;font-weight:600;color:#1a202c;}}
.news-score {{padding:8px 16px;border-radius:20px;color:white;font-weight:700;font-size:14px;}}
.news-meta {{display:flex;gap:15px;margin-bottom:15px;font-size:14px;color:#718096;}}
.news-summary {{color:#4a5568;line-height:1.6;margin-bottom:15px;}}
.news-tags {{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:15px;}}
.tag {{background:#edf2f7;color:#4a5568;padding:4px 12px;border-radius:12px;font-size:12px;}}
.news-scores {{background:#f7fafc;border-radius:12px;padding:15px;margin-bottom:15px;}}
.scores-title {{font-weight:600;color:#2d3748;margin-bottom:12px;}}
.score-item {{display:grid;grid-template-columns:100px 1fr 30px;align-items:center;gap:10px;margin-bottom:8px;}}
.score-bar {{height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;}}
.score-fill {{height:100%;background:linear-gradient(90deg,#667eea 0%,#764ba2 100%);border-radius:4px;}}
.score-value {{font-weight:600;color:#667eea;text-align:right;}}
.news-footer {{display:flex;justify-content:flex-end;}}
.news-link {{color:#667eea;text-decoration:none;font-weight:600;}}
.sidebar {{display:flex;flex-direction:column;gap:20px;}}
.sidebar-card {{background:white;border-radius:16px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,0.08);}}
.sidebar-title {{font-size:18px;font-weight:700;color:#1a202c;margin-bottom:20px;padding-bottom:10px;border-bottom:2px solid #e2e8f0;}}
.source-card {{padding:12px;background:#f7fafc;border-radius:8px;margin-bottom:10px;}}
.source-name {{font-weight:600;color:#2d3748;margin-bottom:5px;}}
.source-meta {{font-size:12px;color:#718096;}}
.distribution-item {{display:flex;justify-content:space-between;padding:10px;background:#f7fafc;border-radius:8px;margin-bottom:8px;}}
.filters {{display:flex;gap:10px;margin-bottom:20px;}}
.filter-btn {{padding:10px 20px;border:2px solid #e2e8f0;background:white;border-radius:8px;cursor:pointer;font-weight:600;}}
.filter-btn.active {{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border-color:transparent;}}
@media (max-width:1024px) {{.main-content{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<div class="container">
<div class="header">
<div class="header-top">
<h1 class="title">📡 AI 新闻日报</h1>
<div class="date-selector"><label>日期:</label><select id="dateSelect" onchange="changeDate()">{dates_html}</select></div>
</div>
<div class="stats">
<div class="stat-card"><div class="stat-value">{total_count}</div><div class="stat-label">今日采集</div></div>
<div class="stat-card"><div class="stat-value">{score_distribution.get("high", 0)}</div><div class="stat-label">高分新闻</div></div>
<div class="stat-card"><div class="stat-value">{score_distribution.get("medium", 0)}</div><div class="stat-label">中分新闻</div></div>
<div class="stat-card"><div class="stat-value">{date}</div><div class="stat-label">采集日期</div></div>
</div>
</div>
<div class="main-content">
<div class="news-section">
<div class="filters">
<button class="filter-btn active" onclick="filterNews('all')">全部</button>
<button class="filter-btn" onclick="filterNews('high')">高分</button>
<button class="filter-btn" onclick="filterNews('medium')">中分</button>
<button class="filter-btn" onclick="filterNews('low')">低分</button>
</div>
{news_html if news_html else '<div style="text-align:center;padding:60px;color:#718096;">暂无新闻数据</div>'}
</div>
<div class="sidebar">
<div class="sidebar-card">
<h3 class="sidebar-title">📊 评分分布</h3>
<div class="distribution-item"><span>🟢 高分 (≥55)</span><strong style="color:#10b981;">{score_distribution.get("high", 0)}</strong></div>
<div class="distribution-item"><span>🟡 中分 (45-54)</span><strong style="color:#f59e0b;">{score_distribution.get("medium", 0)}</strong></div>
<div class="distribution-item"><span>⚪ 低分 (&lt;45)</span><strong style="color:#6b7280;">{score_distribution.get("low", 0)}</strong></div>
</div>
<div class="sidebar-card">
<h3 class="sidebar-title">📡 采集源状态</h3>
{sources_html if sources_html else '<div style="color:#718096;">暂无状态数据</div>'}
</div>
</div>
</div>
</div>
<script>
function filterNews(score){{
const cards=document.querySelectorAll('.news-card');
const btns=document.querySelectorAll('.filter-btn');
btns.forEach(b=>b.classList.remove('active'));
event.target.classList.add('active');
cards.forEach(c=>{{c.style.display=(score==='all'||c.dataset.score===score)?'block':'none';}});
}}
function changeDate(){{
const d=document.getElementById('dateSelect').value;
window.location.href='?date='+d;
}}
</script>
</body>
</html>'''

def main():
    print("🚀 开始生成 Dashboard...")
    daily_file = get_latest_daily_file()
    if not daily_file:
        print("❌ 未找到 daily JSON 文件")
        return
    
    print(f"📄 读取: {daily_file}")
    news_data = load_json(daily_file)
    if not news_data:
        print("❌ 加载数据失败")
        return
    
    sources_status = load_json(STATUS_FILE)
    print("🎨 生成 HTML...")
    html_content = generate_html(news_data, sources_status)
    
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    output_file = DASHBOARD_DIR / f"dashboard-{news_data.get('date', 'latest')}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    latest_file = DASHBOARD_DIR / "dashboard-latest.html"
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard 已生成: {output_file}")
    print(f"✅ 最新版本已保存: {latest_file}")

if __name__ == "__main__":
    main()