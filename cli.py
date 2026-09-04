#!/usr/bin/env python3
"""AI Search Engine CLI - 命令行版 AI 搜索"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.research import ResearchAgent


def run_search(query: str, config_path: str = "config.yaml"):
    """执行搜索并打印结果"""
    agent = ResearchAgent(config_path)

    print(f"\n🔍 搜索: {query}\n")

    # 流式输出
    for event in agent.research_stream(query):
        if event["type"] == "status":
            print(f"  {event['text']}")
        elif event["type"] == "answer_chunk":
            print(event["text"], end="", flush=True)
        elif event["type"] == "done":
            print("\n")


def main():
    parser = argparse.ArgumentParser(
        description="ai-search-engine - Perplexica-like AI Search Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python cli.py "LLM 推理框架对比"
  python cli.py "2025年最好的开源大语言模型"
  python cli.py "Mac M4 Max 128GB 能跑多大的本地 LLM"

配置:
  编辑 config.yaml 设置 LLM API 地址和模型
  默认使用 Ollama (http://localhost:11434/v1)

Web UI:
  python main.py  # 启动 Web 界面 (http://localhost:8700)
        """,
    )
    parser.add_argument("query", help="搜索问题")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")

    args = parser.parse_args()
    run_search(args.query, args.config)


if __name__ == "__main__":
    main()
