#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI News Auto-Updater
每天 08:00 自动采集新闻 → 生成 Dashboard → 推送到 GitHub
"""

import subprocess
import sys
from datetime import datetime

def run_command(cmd, description):
    """执行命令并显示进度"""
    print(f"📌 {description}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {description} 完成")
        return True
    else:
        print(f"❌ {description} 失败：{result.stderr}")
        return False

def main():
    print("=" * 60)
    print("🤖 AI News Auto-Updater")
    print("=" * 60)
    
    workspace = "/home/wxh1010534025/.openclaw/workspace-news"
    
    # Step 1: 运行新闻采集（热点新闻 + 七维评分）
    success = run_command(
        f"cd {workspace} && python3 collect_hot_news.py",
        "采集热点新闻并评分"
    )
    if not success:
        print("⚠️  采集失败，尝试使用现有数据...")
    
    # Step 2: 生成 Dashboard HTML
    success = run_command(
        f"cd {workspace} && python3 scripts/generate_dashboard.py",
        "生成 Dashboard 可视化页面"
    )
    if not success:
        print("❌ Dashboard 生成失败，退出")
        sys.exit(1)
    
    # Step 3: 复制 Dashboard 到 docs 文件夹
    success = run_command(
        f"cd {workspace} && cp data/ai-daily/dashboard/*.html docs/ && cp data/ai-daily/dashboard/state.json docs/",
        "复制 Dashboard 到 docs 文件夹"
    )
    if not success:
        print("❌ 复制文件失败，退出")
        sys.exit(1)
    
    # Step 4: Git 提交并推送
    now = datetime.now().strftime("%Y-%m-%d")
    
    success = run_command(
        f"cd {workspace} && git add docs/ && git commit -m '📰 AI 新闻日报 {now}' && git push origin master",
        f"更新 GitHub Pages ({now})"
    )
    if not success:
        print("❌ Git 推送失败，退出")
        sys.exit(1)
    
    # Step 5: 发送通知（可选）
    print("\n" + "=" * 60)
    print("✅ 自动更新完成！")
    print("📲 访问链接：https://wxhbaduser.github.io/AI_news/")
    print("=" * 60)

if __name__ == "__main__":
    main()
