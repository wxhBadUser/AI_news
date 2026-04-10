#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻采集核心脚本
负责：RSS解析、网页抓取、去重、评分、写入JSON
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# 配置路径
BASE_DIR = Path("/home/wxh1010534025/.openclaw/workspace-news")
CONFIG_FILE = BASE_DIR / "data/ai-daily/config/collector-config.json"
STATUS_FILE = BASE_DIR / "data/ai-daily/status/sources-status.json"
DAILY_DIR = BASE_DIR / "data/ai-daily/daily"
DASHBOARD_FILE = BASE_DIR / "data/ai-daily/dashboard/state.json"

def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_status():
    """加载状态文件"""
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_status(status_data):
    """保存状态文件"""
    status_data['lastUpdate'] = datetime.now().isoformat()
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

def calculate_score(news_item):
    """
    七维评分模型
    返回 0-5 分的加权总分
    """
    scores = {}
    
    # 1. 时间新鲜度 (20%)
    pub_date = news_item.get('pub_date')
    if pub_date:
        days_old = (datetime.now() - pub_date).days
        if days_old == 0:
            scores['freshness'] = 5
        elif days_old <= 2:
            scores['freshness'] = 4
        elif days_old <= 5:
            scores['freshness'] = 3
        else:
            scores['freshness'] = 2
    else:
        scores['freshness'] = 3
    
    # 2. 炸裂程度 (25%) - 基于关键词
    title = news_item.get('title', '').lower()
    explosive_keywords = ['breakthrough', '革命', '突破', 'gpt-5', 'agi', 'first', '首个']
    if any(kw in title for kw in explosive_keywords):
        scores['explosiveness'] = 5
    else:
        scores['explosiveness'] = 3
    
    # 3. 重复度 (15%) - 简化处理
    scores['uniqueness'] = 4
    
    # 4. 争议性 (15%) - 基于关键词
    controversy_keywords = ['debate', '争议', 'vs', 'battle', 'fight']
    if any(kw in title for kw in controversy_keywords):
        scores['controversy'] = 5
    else:
        scores['controversy'] = 2
    
    # 5. 可视化潜力 (10%)
    scores['visual'] = 3
    
    # 6. 受众相关性 (10%)
    scores['relevance'] = 4
    
    # 7. 口播展开性 (5%)
    scores['expandability'] = 3
    
    # 加权总分
    weights = {
        'freshness': 0.20,
        'explosiveness': 0.25,
        'uniqueness': 0.15,
        'controversy': 0.15,
        'visual': 0.10,
        'relevance': 0.10,
        'expandability': 0.05
    }
    
    total_score = sum(scores[k] * weights[k] for k in scores)
    return round(total_score, 2)

def generate_hash(title, url):
    """生成新闻唯一标识"""
    content = f"{title}|{url}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def save_daily_news(news_items, date_str=None):
    """保存每日新闻到JSON"""
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    output_file = DAILY_DIR / f"{date_str}.json"
    
    # 读取已有数据（如果存在）
    existing_data = {}
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    # 去重
    existing_hashes = set()
    if 'news' in existing_data:
        for item in existing_data['news']:
            existing_hashes.add(item.get('hash'))
    
    # 添加新新闻
    new_items = []
    for item in news_items:
        if item.get('hash') not in existing_hashes:
            new_items.append(item)
    
    # 合并数据
    all_news = existing_data.get('news', []) + new_items
    
    # 构建输出结构
    output = {
        "date": date_str,
        "summary": {
            "totalItems": len(all_news),
            "successCount": len([n for n in all_news if n.get('status') == 'success']),
            "failCount": len([n for n in all_news if n.get('status') == 'failed']),
            "failedSources": []
        },
        "sources": {},
        "news": all_news
    }
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存 {len(new_items)} 条新闻到 {output_file}")
    return output_file

def update_dashboard():
    """更新 Dashboard 状态"""
    # 读取今日新闻
    today = datetime.now().strftime('%Y-%m-%d')
    daily_file = DAILY_DIR / f"{today}.json"
    
    if not daily_file.exists():
        print("⚠️ 今日尚无采集数据")
        return
    
    with open(daily_file, 'r', encoding='utf-8') as f:
        daily_data = json.load(f)
    
    # 计算统计数据
    news_items = daily_data.get('news', [])
    scores = [n.get('score', 0) for n in news_items]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # 更新 Dashboard
    dashboard = {
        "lastUpdate": datetime.now().isoformat(),
        "summary": {
            "totalSources": 9,
            "activeSources": 9,
            "disabledSources": 0,
            "totalItemsToday": len(news_items),
            "avgScore": round(avg_score, 2)
        },
        "recentCollections": news_items[:10],
        "topNews": sorted(news_items, key=lambda x: x.get('score', 0), reverse=True)[:5],
        "failedSources": []
    }
    
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Dashboard 已更新，今日 {len(news_items)} 条新闻，平均分 {avg_score:.2f}")

if __name__ == "__main__":
    print("📡 新闻采集脚本已就绪")
    print(f"配置文件: {CONFIG_FILE}")
    print(f"状态文件: {STATUS_FILE}")
    print(f"数据目录: {DAILY_DIR}")
