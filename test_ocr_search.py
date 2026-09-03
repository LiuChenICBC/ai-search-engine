#!/usr/bin/env python3
"""搜索 OCR 测试图片并测试 img2text.py"""

import os
import sys
import json
import requests
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from search import search_all

# 搜索关键词
queries = [
    "low resolution blurry text image OCR test",
    "glare reflection text image OCR dataset",
    "低分辨率 模糊 反光 文字 图片 测试",
    "ICDAR text image low quality",
]

output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

all_results = []
for q in queries:
    print(f"\n=== 搜索: {q} ===")
    results = search_all(q, max_results=10)
    for r in results:
        all_results.append({
            "query": q,
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
        })
        print(f"  - {r.title[:60]}: {r.url}")

# 保存搜索结果
with open(output_dir / "search_results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\n共找到 {len(all_results)} 条结果，已保存到 output/search_results.json")
