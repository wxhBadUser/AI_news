#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试采集 - 保存示例数据
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/home/wxh1010534025/.openclaw/workspace-news")
DAILY_DIR = BASE_DIR / "data/ai-daily/daily"

# 创建今日新闻数据
today = datetime.now().strftime('%Y-%m-%d')
output_file = DAILY_DIR / f"{today}.json"

# 示例新闻数据（实际采集时会从 RSS/Web 获取）
news_data = {
    "date": today,
    "summary": {
        "totalItems": 5,
        "successCount": 5,
        "failCount": 4,
        "failedSources": ["MIT Tech Review", "VentureBeat AI", "量子位", "虎嗅", "36氪", "Import AI"]
    },
    "sources": {
        "openai-news": {
            "status": "success",
            "method": "rss",
            "itemsCount": 1
        },
        "deepmind-blog": {
            "status": "success",
            "method": "rss",
            "itemsCount": 1
        },
        "google-ai-blog": {
            "status": "success",
            "method": "rss",
            "itemsCount": 1
        },
        "mit-tech-review": {
            "status": "failed",
            "method": "rss",
            "error": "RSS feed not accessible"
        },
        "venturebeat-ai": {
            "status": "failed",
            "method": "rss",
            "error": "404 error"
        }
    },
    "news": [
        {
            "hash": "a1b2c3d4e5f6",
            "title": "OpenAI announces GPT-5 with breakthrough reasoning",
            "url": "https://openai.com/blog/gpt-5",
            "source": "openai-news",
            "pub_date": "2026-04-07T10:00:00+00:00",
            "summary_zh": "OpenAI 发布 GPT-5，具备突破性推理能力",
            "score": 4.8,
            "scores": {
                "freshness": 5,
                "explosiveness": 5,
                "uniqueness": 4,
                "controversy": 4,
                "visual": 5,
                "relevance": 5,
                "expandability": 5
            },
            "status": "success"
        },
        {
            "hash": "g7h8i9j0k1l2",
            "title": "AlphaFold 3: Predicting protein interactions",
            "url": "https://deepmind.google/blog/alphafold-3",
            "source": "deepmind-blog",
            "pub_date": "2026-04-07T14:00:00+00:00",
            "summary_zh": "DeepMind 发布 AlphaFold 3，预测蛋白质相互作用",
            "score": 4.5,
            "scores": {
                "freshness": 5,
                "explosiveness": 4,
                "uniqueness": 5,
                "controversy": 3,
                "visual": 5,
                "relevance": 5,
                "expandability": 5
            },
            "status": "success"
        },
        {
            "hash": "m3n4o5p6q7r8",
            "title": "Gemini 2.0: Multimodal AI at scale",
            "url": "https://blog.google/technology/ai/gemini-2",
            "source": "google-ai-blog",
            "pub_date": "2026-04-06T09:00:00+00:00",
            "summary_zh": "Google 发布 Gemini 2.0，大规模多模态 AI",
            "score": 4.3,
            "scores": {
                "freshness": 4,
                "explosiveness": 4,
                "uniqueness": 4,
                "controversy": 4,
                "visual": 5,
                "relevance": 5,
                "expandability": 4
            },
            "status": "success"
        }
    ]
}

# 保存文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(news_data, f, ensure_ascii=False, indent=2)

print(f"✅ 已保存测试数据到: {output_file}")
print(f"   - 成功采集: {news_data['summary']['successCount']} 条")
print(f"   - 失败源: {len(news_data['summary']['failedSources'])} 个")
