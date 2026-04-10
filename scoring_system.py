#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻评分系统 - 七维评分
对新闻进行多维度评分，筛选热点新闻
"""

import re
from datetime import datetime, timezone, timedelta

# 时区设置
TZ = timezone(timedelta(hours=8))

# AI 相关关键词
AI_KEYWORDS = [
    # 英文关键词
    "AI", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "GPT", "LLM", "large language model", "ChatGPT",
    "OpenAI", "Claude", "Gemini", "LLaMA", "transformer", "AGI",
    "computer vision", "NLP", "natural language processing",
    "reinforcement learning", "generative AI", "diffusion model",
    "multimodal", "embedding", "fine-tuning", "RAG", "agent",
    
    # 中文关键词
    "人工智能", "机器学习", "深度学习", "神经网络", "大模型",
    "语言模型", "生成式AI", "计算机视觉", "自然语言处理",
    "强化学习", "多模态", "智能体", "AGI", "AIGC",
]

# 权威来源评分
AUTHORITY_SCORES = {
    # 顶级权威（权重 1.0）
    "openai": 1.0,
    "google": 1.0,
    "deepmind": 1.0,
    "anthropic": 1.0,
    "meta": 0.95,
    "microsoft": 0.95,
    "nvidia": 0.95,
    
    # 专业媒体（权重 0.85）
    "量子位": 0.85,
    "机器之心": 0.85,
    "新智元": 0.85,
    "36氪": 0.80,
    "infoq": 0.80,
    
    # 其他（权重 0.7）
    "default": 0.70,
}

# 重大产品/技术关键词（影响力加分）
IMPACT_KEYWORDS = [
    "GPT-5", "GPT-4", "Claude 3", "Gemini 2", "LLaMA 3",
    "Sora", "DALL-E", "Midjourney", "Stable Diffusion",
    "AGI", "breakthrough", "revolutionary", "first-ever",
    "开源", "发布", "推出", "突破", "革命性",
]


def calculate_timeliness_score(pub_date_str, max_age_days=7):
    """
    时效性评分（20%）
    - 今天的新闻：100分
    - 昨天的新闻：90分
    - 2天前：80分
    - 以此类推，最低0分
    """
    if not pub_date_str:
        return 50  # 无日期信息，给中等分数
    
    try:
        # 尝试解析日期
        formats = [
            "%Y-%m-%d",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S GMT",
            "%Y-%m-%dT%H:%M:%S%z",
        ]
        
        pub_date = None
        for fmt in formats:
            try:
                pub_date = datetime.strptime(pub_date_str.strip(), fmt)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=TZ)
                break
            except:
                continue
        
        if not pub_date:
            return 50
        
        # 计算天数差
        now = datetime.now(TZ)
        age_days = (now - pub_date).days
        
        if age_days < 0:
            return 100  # 未来日期（可能是时区问题），给满分
        elif age_days == 0:
            return 100  # 今天
        elif age_days == 1:
            return 90   # 昨天
        elif age_days == 2:
            return 80
        elif age_days <= max_age_days:
            return max(0, 100 - age_days * 10)
        else:
            return 0  # 超过 max_age_days 天，0分
            
    except Exception as e:
        return 50


def calculate_authority_score(source_name, source_id):
    """
    来源权威性评分（15%）
    """
    source_key = source_id.lower() if source_id else ""
    source_name_lower = source_name.lower() if source_name else ""
    
    # 检查权威来源列表
    for key, score in AUTHORITY_SCORES.items():
        if key in source_key or key in source_name_lower:
            return score * 100
    
    return AUTHORITY_SCORES["default"] * 100


def calculate_ai_relevance_score(title, description):
    """
    AI 相关度评分（25%）
    统计标题和摘要中的 AI 关键词数量
    """
    text = f"{title} {description}".lower()
    
    keyword_count = 0
    for keyword in AI_KEYWORDS:
        if keyword.lower() in text:
            keyword_count += 1
    
    # 最多匹配 10 个关键词即为满分
    score = min(keyword_count / 10.0, 1.0) * 100
    return score


def calculate_content_quality_score(title, description):
    """
    内容质量评分（15%）
    - 标题长度适中（10-100字符）：加分
    - 摘要长度适中（50-500字符）：加分
    - 标题包含数字/问号：加分（吸引眼球）
    """
    score = 50  # 基础分
    
    # 标题质量
    if title:
        title_len = len(title)
        if 10 <= title_len <= 100:
            score += 15
        elif title_len > 0:
            score += 5
        
        # 标题包含数字（通常表示数据/排名）
        if re.search(r'\d+', title):
            score += 10
        
        # 标题包含问号（通常表示探讨性问题）
        if '？' in title or '?' in title:
            score += 5
    
    # 摘要质量
    if description:
        desc_len = len(description)
        if 50 <= desc_len <= 500:
            score += 15
        elif desc_len > 0:
            score += 5
    
    return min(score, 100)


def calculate_position_score(position, total_items):
    """
    热度指标评分（10%）
    RSS 中的位置越靠前，分数越高
    """
    if total_items == 0:
        return 50
    
    # 第一条：100分，最后一条：50分
    score = 100 - (position / total_items) * 50
    return score


def calculate_originality_score(title, description):
    """
    原创性评分（10%）
    检测是否包含"首发"、"独家"等关键词
    """
    text = f"{title} {description}".lower()
    
    original_keywords = [
        "首发", "独家", "exclusive", "first", "breaking",
        "原创", "深度", "专访", "独家报道",
    ]
    
    for keyword in original_keywords:
        if keyword in text:
            return 100
    
    return 60  # 默认分数


def calculate_impact_score(title, description):
    """
    影响力评分（5%）
    检测是否涉及重大产品/技术发布
    """
    text = f"{title} {description}"
    
    for keyword in IMPACT_KEYWORDS:
        if keyword.lower() in text.lower():
            return 100
    
    return 60  # 默认分数


def calculate_total_score(news_item, position=0, total_items=20):
    """
    计算总分（加权平均）
    """
    title = news_item.get('title', '')
    description = news_item.get('description', '')
    pub_date = news_item.get('pub_date', '')
    source_name = news_item.get('source_name', '')
    source_id = news_item.get('source', '')
    
    # 各维度评分
    timeliness = calculate_timeliness_score(pub_date)
    authority = calculate_authority_score(source_name, source_id)
    ai_relevance = calculate_ai_relevance_score(title, description)
    content_quality = calculate_content_quality_score(title, description)
    position_score = calculate_position_score(position, total_items)
    originality = calculate_originality_score(title, description)
    impact = calculate_impact_score(title, description)
    
    # 加权平均
    total_score = (
        timeliness * 0.20 +
        authority * 0.15 +
        ai_relevance * 0.25 +
        content_quality * 0.15 +
        position_score * 0.10 +
        originality * 0.10 +
        impact * 0.05
    )
    
    return {
        "total": round(total_score, 2),
        "breakdown": {
            "timeliness": round(timeliness, 2),
            "authority": round(authority, 2),
            "ai_relevance": round(ai_relevance, 2),
            "content_quality": round(content_quality, 2),
            "position": round(position_score, 2),
            "originality": round(originality, 2),
            "impact": round(impact, 2),
        }
    }


def score_news_list(news_list):
    """
    对新闻列表进行评分
    """
    total_items = len(news_list)
    
    for i, news in enumerate(news_list):
        scores = calculate_total_score(news, position=i, total_items=total_items)
        news['score'] = scores['total']
        news['score_breakdown'] = scores['breakdown']
    
    # 按评分排序
    news_list.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return news_list


# 测试代码
if __name__ == "__main__":
    # 测试用例
    test_news = {
        "title": "OpenAI 发布 GPT-5：多模态能力大幅提升",
        "description": "OpenAI 今日宣布推出 GPT-5，这是最新的大型语言模型，具备强大的多模态能力...",
        "pub_date": "2026-04-10",
        "source_name": "OpenAI",
        "source": "openai",
    }
    
    scores = calculate_total_score(test_news)
    print("📊 评分测试:")
    print(f"总分: {scores['total']}")
    print("\n各维度得分:")
    for dim, score in scores['breakdown'].items():
        print(f"  {dim}: {score}")
