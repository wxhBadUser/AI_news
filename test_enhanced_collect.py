#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版采集脚本 - 带 Web Search Fallback
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error

BASE_DIR = Path("/home/wxh1010534025/.openclaw/workspace-news")
CONFIG_FILE = BASE_DIR / "data/ai-daily/config/collector-config.json"
OUTPUT_FILE = BASE_DIR / "data/ai-daily/daily/2026-04-08.json"

def load_config():
    """加载配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_rss(url):
    """抓取 RSS"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"  ⚠️  RSS 失败: {e}")
        return None

def parse_rss(xml_content, source_id, source_name):
    """解析 RSS 提取新闻"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        for item in root.findall('.//item')[:5]:  # 只取前5条
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            description = item.find('description').text if item.find('description') is not None else ''
            
            if title and link:
                # 生成 hash
                hash_str = hashlib.md5(f"{title}{link}".encode()).hexdigest()[:12]
                
                items.append({
                    "hash": hash_str,
                    "title": title,
                    "url": link,
                    "source": source_id,
                    "source_name": source_name,
                    "pub_date": pub_date,
                    "description": description[:200] if description else "",
                    "summary_zh": f"[{source_name}] {title}",
                    "score": 3.5,
                    "status": "success",
                    "method": "rss"
                })
    except Exception as e:
        print(f"  ❌ 解析失败: {e}")
    
    return items

def web_search_fallback(source_name, keywords):
    """Web Search Fallback - 模拟搜索结果"""
    print(f"  🔄 使用 Web Search Fallback...")
    # 这里需要集成实际的 Web Search API
    # 目前返回模拟数据
    return []

def main():
    print("🚀 开始增强版采集测试...\n")
    
    # 加载配置
    config = load_config()
    sources = config['sources']
    
    all_news = []
    results = {
        "date": "2026-04-08",
        "summary": {
            "totalItems": 0,
            "successCount": 0,
            "failCount": 0,
            "failedSources": [],
            "fallbackCount": 0
        },
        "sources": {},
        "news": []
    }
    
    # 测试每个源
    for source in sources:
        source_id = source['id']
        source_name = source['name']
        url = source['url']
        source_type = source['type']
        
        print(f"📡 测试 {source_name} ({source_id})...")
        print(f"   URL: {url}")
        
        if source_type == 'rss':
            xml_content = fetch_rss(url)
            
            if xml_content:
                items = parse_rss(xml_content, source_id, source_name)
                all_news.extend(items)
                
                results['sources'][source_id] = {
                    "status": "success",
                    "method": "rss",
                    "itemsCount": len(items)
                }
                
                print(f"  ✅ RSS 成功: {len(items)} 条新闻")
            else:
                # RSS 失败，尝试 Web Search Fallback
                print(f"  ⚠️  RSS 失败，尝试 Fallback...")
                
                # 定义搜索关键词
                keywords = {
                    "deepmind-blog": "DeepMind AI latest news",
                    "google-ai-blog": "Google AI blog latest",
                    "huxiu": "虎嗅 AI 人工智能",
                    "import-ai": "Import AI newsletter latest"
                }
                
                if source_id in keywords:
                    fallback_items = web_search_fallback(source_name, keywords[source_id])
                    
                    if fallback_items:
                        all_news.extend(fallback_items)
                        results['sources'][source_id] = {
                            "status": "success",
                            "method": "web_search_fallback",
                            "itemsCount": len(fallback_items)
                        }
                        results['summary']['fallbackCount'] += 1
                        print(f"  ✅ Fallback 成功: {len(fallback_items)} 条新闻")
                    else:
                        results['sources'][source_id] = {
                            "status": "failed",
                            "method": "web_search_fallback",
                            "error": "No results from web search"
                        }
                        results['summary']['failedSources'].append(source_name)
                        print(f"  ❌ Fallback 失败: 无搜索结果")
                else:
                    results['sources'][source_id] = {
                        "status": "failed",
                        "method": "rss",
                        "error": "RSS fetch failed, no fallback configured"
                    }
                    results['summary']['failedSources'].append(source_name)
                    print(f"  ❌ 失败: 无 Fallback 配置")
        else:
            results['sources'][source_id] = {
                "status": "skipped",
                "method": source_type,
                "note": "非 RSS 源"
            }
            print(f"  ⏭️  跳过: 非 RSS 源")
        
        print()
    
    # 更新统计
    results['news'] = all_news
    results['summary']['totalItems'] = len(all_news)
    results['summary']['successCount'] = len([s for s in results['sources'].values() if s.get('status') == 'success'])
    results['summary']['failCount'] = len(results['summary']['failedSources'])
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 打印摘要
    print("=" * 60)
    print("📊 采集摘要:")
    print(f"  ✅ 成功源: {results['summary']['successCount']}/{len(sources)}")
    print(f"  🔄 Fallback 成功: {results['summary']['fallbackCount']} 个")
    print(f"  📰 采集新闻: {results['summary']['totalItems']} 条")
    print(f"  ❌ 失败源: {results['summary']['failCount']} 个")
    
    if results['summary']['failedSources']:
        print(f"\n⚠️  失败源列表:")
        for source in results['summary']['failedSources']:
            print(f"  - {source}")
    
    print(f"\n💾 数据已保存到: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
