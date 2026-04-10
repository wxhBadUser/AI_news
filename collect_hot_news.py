#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点新闻采集脚本 - 每个源取前 5-8 条热点新闻
支持七维评分系统，按评分排序输出
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import sys

# 添加工作目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from scoring_system import score_news_list

# 配置
BASE_DIR = Path("/home/wxh1010534025/.openclaw/workspace-news")
CONFIG_FILE = BASE_DIR / "data/ai-daily/config/collector-config.json"

# 时区设置
TZ = timezone(timedelta(hours=8))
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")
OUTPUT_FILE = BASE_DIR / f"data/ai-daily/daily/{TODAY}.json"

# 每个源采集的新闻数量
NEWS_PER_SOURCE = 6  # 取前 6 条热点新闻


def load_config():
    """加载采集配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def fetch_rss(url):
    """抓取 RSS"""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsCollector/2.0)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"  ⚠️  RSS 抓取失败: {e}")
        return None


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(TZ)
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    
    return None


def parse_rss(xml_content, source_id, source_name, max_items=NEWS_PER_SOURCE):
    """
    解析 RSS 提取新闻
    取前 max_items 条热点新闻（RSS 中位置靠前的通常是热点）
    """
    items = []
    try:
        root = ET.fromstring(xml_content)
        all_items = root.findall('.//item')
        
        # 只取前 max_items 条（热点新闻）
        hot_items = all_items[:max_items]
        
        print(f"  📊 获取 {len(all_items)} 条，取前 {len(hot_items)} 条热点")
        
        for idx, item in enumerate(hot_items, 1):
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate')
            desc_elem = item.find('description')
            
            if title_elem is None or link_elem is None:
                continue
            
            title = title_elem.text or ''
            link = link_elem.text or ''
            pub_date_raw = pub_date_elem.text if pub_date_elem is not None else ''
            description = desc_elem.text if desc_elem is not None else ''
            
            # 解析日期
            pub_date = parse_date(pub_date_raw)
            
            if title and link:
                # 生成 hash
                hash_str = hashlib.md5(f"{title}{link}".encode()).hexdigest()[:12]
                
                items.append({
                    "hash": hash_str,
                    "title": title,
                    "url": link,
                    "source": source_id,
                    "source_name": source_name,
                    "pub_date": pub_date or TODAY,
                    "description": description[:500] if description else "",
                    "summary_zh": f"[{source_name}] {title}",
                    "status": "success",
                    "method": "rss",
                    "position": idx,  # 记录在 RSS 中的位置
                })
        
        print(f"  ✅ 提取 {len(items)} 条热点新闻")
        
    except Exception as e:
        print(f"  ❌ 解析失败: {e}")
    
    return items


def collect_from_rss_sources(config):
    """从 RSS 源采集热点新闻"""
    all_news = []
    
    sources = config.get('sources', [])
    print(f"\n📡 开始采集 {len(sources)} 个源的热点新闻...\n")
    
    for source in sources:
        source_id = source.get('id', '')
        source_name = source.get('name', '')
        rss_url = source.get('url', '')
        
        if not rss_url:
            print(f"⏭️  {source_name}: 无 RSS URL，跳过")
            continue
        
        print(f"📰 {source_name} ({source_id})")
        print(f"   🔗 {rss_url}")
        
        # 抓取 RSS
        xml_content = fetch_rss(rss_url)
        if xml_content:
            items = parse_rss(xml_content, source_id, source_name)
            all_news.extend(items)
        else:
            print(f"  ⚠️  跳过此源")
        
        print()
    
    return all_news


def save_results(news_list):
    """保存采集结果"""
    # 去重
    seen_hashes = set()
    unique_news = []
    for news in news_list:
        if news['hash'] not in seen_hashes:
            seen_hashes.add(news['hash'])
            unique_news.append(news)
    
    # 评分并排序
    print("📊 正在进行七维评分...")
    scored_news = score_news_list(unique_news)
    
    # 构建输出数据
    output = {
        "date": TODAY,
        "total": len(scored_news),
        "collected_at": datetime.now(TZ).isoformat(),
        "news": scored_news
    }
    
    # 确保输出目录存在
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存 JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 统计信息
    print(f"\n{'='*60}")
    print(f"✅ 采集完成！")
    print(f"📅 日期: {TODAY}")
    print(f"📊 总数: {len(scored_news)} 条新闻")
    print(f"💾 保存至: {OUTPUT_FILE}")
    
    # 显示评分分布
    high_score = len([n for n in scored_news if n.get('score', 0) >= 80])
    mid_score = len([n for n in scored_news if 60 <= n.get('score', 0) < 80])
    low_score = len([n for n in scored_news if n.get('score', 0) < 60])
    
    print(f"\n📈 评分分布:")
    print(f"  🔥 高分 (≥80): {high_score} 条")
    print(f"  📊 中分 (60-79): {mid_score} 条")
    print(f"  📉 低分 (<60): {low_score} 条")
    
    # 显示 Top 5
    print(f"\n🏆 Top 5 热点新闻:")
    for i, news in enumerate(scored_news[:5], 1):
        print(f"  {i}. [{news['score']:.1f}分] {news['title'][:50]}...")
        print(f"     📰 {news['source_name']} | 🔗 {news['url'][:60]}...")
    
    print(f"{'='*60}\n")
    
    return len(scored_news)


def main():
    print("=" * 60)
    print("📡 AI 热点新闻采集器 - 七维评分版")
    print("=" * 60)
    print(f"📅 今天日期: {TODAY}")
    print(f"📊 每个源取前 {NEWS_PER_SOURCE} 条热点")
    print(f"💾 输出文件: {OUTPUT_FILE}")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 从 RSS 采集热点新闻
    news_list = collect_from_rss_sources(config)
    
    if not news_list:
        print("⚠️  没有采集到任何新闻！")
        return 1
    
    # 保存结果（包含评分和排序）
    count = save_results(news_list)
    
    return 0


if __name__ == "__main__":
    exit(main())
