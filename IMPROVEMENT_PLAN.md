# AI Search Engine 改进计划

## 目标
将项目从 7.5/10 提升到 8.5+/10，主要改进：
1. 补充完整文档（README、API、部署指南）
2. 拆分 main.py（732 行 → 模块化）
3. 添加 Mac 单机部署步骤
4. 稳定化（依赖锁定、CI/CD、健康检查）

## 已完成

- [x] LICENSE（MIT）
- [x] .env.example（环境变量示例）
- [x] pyproject.toml（依赖管理 + 项目元数据）
- [x] requirements.txt（版本钉住）
- [x] Dockerfile + docker-compose.yml
- [x] GitHub Actions CI（ruff + pytest）

## 任务清单

### Phase 1: 文档补充
- [x] .env.example（环境变量示例）
- [ ] README.md（项目介绍、架构、快速开始）
- [ ] docs/API.md（API 端点文档）
- [ ] docs/DEPLOY.md（部署指南，含 Mac 单机步骤）
- [ ] docs/ARCHITECTURE.md（架构图、数据流）

### Phase 2: 代码拆分
- [ ] routes/api.py（API 路由：/api/chat, /api/config, /api/health）
- [ ] routes/admin.py（Admin 路由：/admin/*）
- [ ] middleware.py（中间件：APIKeyMiddleware, CSRF, security headers）
- [ ] 重构 main.py 为入口文件（< 100 行）

### Phase 3: 稳定化
- [x] pyproject.toml（依赖管理 + 项目元数据）
- [x] Dockerfile + docker-compose.yml
- [ ] healthcheck 端点完善
- [ ] graceful shutdown 改进
- [ ] 日志配置优化

### Phase 4: 测试验证
- [ ] 确保所有现有测试通过
- [ ] 添加新模块的测试
- [ ] 端到端测试验证
