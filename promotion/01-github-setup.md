# GitHub 仓库设置指南

## 1. 仓库描述（Description）

**英文版（推荐）：**
> Perplexica-like AI Search Engine built with Python/FastAPI. Multi-engine search, LLM-powered answers, streaming output, multi-user auth, and production-grade security.

**中文版：**
> 基于 Python/FastAPI 的 Perplexica 风格 AI 搜索引擎。多引擎聚合、LLM 智能回答、流式输出、多用户认证、生产级安全。

## 2. 仓库网站（Website）

```
https://github.com/LiuChenICBC/ai-search-engine
```

## 3. GitHub Topics

复制以下内容添加到仓库 Topics：

```
ai-search-engine
fastapi
perplexica
llm
python
search-engine
self-hosted
privacy
open-source
ai
machine-learning
searxng
duckduckgo
```

### 如何添加 Topics：
1. 进入仓库页面
2. 点击右侧齿轮图标（Edit repository topics）
3. 添加上述 Topics

## 4. 仓库徽章（Badges）

在 README 顶部添加以下徽章：

```markdown
[![CI](https://github.com/LiuChenICBC/ai-search-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/LiuChenICBC/ai-search-engine/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
```

## 5. About 部分配置

在 GitHub 仓库页面的 About 部分设置：

- **Description**: 使用上述英文描述
- **Website**: `https://github.com/LiuChenICBC/ai-search-engine`
- **Topics**: 添加上述 Topics
- **Releases**: 如果有版本发布，创建 Release

## 6. 创建 Release（可选）

```bash
# 在项目根目录执行
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

然后在 GitHub 上创建 Release，添加：
- Release title: `v1.0.0`
- Release notes: 参考 CHANGELOG 或列出主要特性
- 上传构建的 wheel 包（可选）

## 7. 仓库置顶 Issue/PR（可选）

创建一个置顶 Issue 作为 Roadmap 或 Welcome 页面：
- 标题：`Welcome to ai-search-engine! Roadmap and Contributing Guide`
- 内容包含：项目介绍、如何贡献、Roadmap
