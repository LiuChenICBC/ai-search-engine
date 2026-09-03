#!/usr/bin/env python3
"""自包含的 web_search 工具，基于 DuckDuckGo Search (ddgs)，完全免费无需 API key。"""

import sys
import json
from ddgs import DDGS


def search(query: str, max_results: int = 10) -> list[dict]:
    """搜索并返回结果列表。"""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
            )
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python web_search.py <查询关键词> [最大结果数]", file=sys.stderr)
        sys.exit(1)

    query = " ".join(sys.argv[1:-1]) if len(sys.argv) > 2 else sys.argv[1]
    max_results = (
        int(sys.argv[-1]) if len(sys.argv) > 2 and sys.argv[-1].isdigit() else 10
    )

    results = search(query, max_results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
