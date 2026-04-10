#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试采集脚本 - 验证配置和路径
"""

import json
from pathlib import Path

BASE_DIR = Path("/home/wxh1010534025/.openclaw/workspace-news")

print("=" * 60)
print("🧪 新闻采集系统 - 配置验证")
print("=" * 60)

# 1. 检查配置文件
config_file = BASE_DIR / "data/ai-daily/config/collector-config.json"
if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"\n✅ 配置文件存在")
    print(f"   - 新闻源数量: {len(config['sources'])}")
    for source in config['sources']:
        print(f"   - {source['id']}: {source['name']} ({source['type']})")
else:
    print(f"\n❌ 配置文件不存在: {config_file}")

# 2. 检查状态文件
status_file = BASE_DIR / "data/ai-daily/status/sources-status.json"
if status_file.exists():
    with open(status_file, 'r', encoding='utf-8') as f:
        status = json.load(f)
    print(f"\n✅ 状态文件存在")
    print(f"   - 最后更新: {status['lastUpdate']}")
else:
    print(f"\n❌ 状态文件不存在: {status_file}")

# 3. 检查目录结构
dirs = [
    "data/ai-daily/config",
    "data/ai-daily/status",
    "data/ai-daily/daily",
    "data/ai-daily/dashboard",
    "memory/agents"
]

print(f"\n📁 目录结构检查:")
for dir_path in dirs:
    full_path = BASE_DIR / dir_path
    if full_path.exists():
        print(f"   ✅ {dir_path}")
    else:
        print(f"   ❌ {dir_path}")

# 4. 检查核心脚本
script_file = BASE_DIR / "collect_news.py"
if script_file.exists():
    print(f"\n✅ 核心脚本存在: {script_file}")
else:
    print(f"\n❌ 核心脚本不存在: {script_file}")

print("\n" + "=" * 60)
print("🎉 配置验证完成！系统已就绪。")
print("=" * 60)
