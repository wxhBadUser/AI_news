#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实新闻采集脚本 - 支持按日期过滤
从 RSS 源采集今天的新闻，确保链接正确
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error

# 配置
BASE_DIR = Path("/home/wxh1010534025/.openclaw/workspace-news")
CONFIG_FILE = BASE_DIR / "data/ai-daily/config/collector-config.json"

# 设置时区（北京时间）
TZ = timezone(timedelta(hours=8))
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")
OUTPUT_FILE = BASE_DIR / f"data/ai-daily/daily/{TODAY}.json"

def load_config():
    """加载采集配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_rss(url):
    """抓取 RSS"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsCollector/1.0)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"  ⚠️  RSS 抓取失败: {e}")
        return None

def parse_date(date_str):
    """解析日期字符串，返回标准格式"""
    if not date_str:
        return None
    
    # 尝试多种日期格式
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",  # RFC 2822
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            # 转换为北京时间
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(TZ)
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    
    return None

def parse_rss(xml_content, source_id, source_name):
    """解析 RSS 提取新闻"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        all_items = root.findall('.//item')
        
        print(f"  📊 获取 {len(all_items)} 条新闻，筛选今天的...")
        
        for item in all_items:
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
            
            # 只保留今天的新闻
            if pub_date != TODAY:
                continue
            
            if title and link:
                # 生成 hash
                hash_str = hashlib.md5(f"{title}{link}".encode()).hexdigest()[:12]
                
                items.append({
                    "hash": hash_str,
                    "title": title,
                    "url": link,  # 正确的链接字段
                    "source": source_id,
                    "source_name": source_name,
                    "pub_date": pub_date,
                    "description": description[:300] if description else "",
                    "summary_zh": f"[{source_name}] {title}",
                    "score": 5.0,  # 默认评分
                    "status": "success",
                    "method": "rss"
                })
        
        print(f"  ✅ 筛选出 {len(items)} 条今天的新闻")
        
    except Exception as e:
        print(f"  ❌ 解析失败: {e}")
    
    return items

def collect_from_rss_sources(config):
    """从 RSS 源采集新闻"""
    all_news = []
    
    sources = config.get('sources', [])
    print(f"\n📡 开始采集 {len(sources)} 个源...\n")
    
    for source in sources:
        source_id = source.get('id', '')
        source_name = source.get('name', '')
        rss_url = source.get('url', '')  # 使用 url 字段
        
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
    
    # 按评分排序
    unique_news.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # 构建输出数据
    output = {
        "date": TODAY,
        "total": len(unique_news),
        "collected_at": datetime.now(TZ).isoformat(),
        "news": unique_news
    }
    
    # 确保输出目录存在
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存 JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ 采集完成！")
    print(f"📅 日期: {TODAY}")
    print(f"📊 总数: {len(unique_news)} 条新闻")
    print(f"💾 保存至: {OUTPUT_FILE}")
    print(f"{'='*60}\n")
    
    return len(unique_news)

def main():
    print("=" * 60)
    print("📡 AI 新闻采集器 - 真实数据版")
    print("=" * 60)
    print(f"📅 今天日期: {TODAY}")
    print(f"💾 输出文件: {OUTPUT_FILE}")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 从 RSS 采集
    news_list = collect_from_rss_sources(config)
    
    # 保存结果
    count = save_results(news_list)
    
    if count == 0:
        print("⚠️  今天没有采集到新闻！")
        print("可能原因：")
        print("  1. RSS 源还没有发布今天的新闻")
        print("  2. RSS 源更新延迟")
        print("  3. 需要等待更多时间")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
