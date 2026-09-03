# 代码质量改进清单 (目标: 9/10)

## 当前状态: 8.5/10

### P0 - 必须修复 (阻塞 9 分)

#### 1. 重复代码 - Flash message 解析
- routes/admin.py 中 3 个端点重复解析 flash message
- 改进: 提取 `_parse_flash_messages(request)` 工具函数

#### 2. 魔法数字
- middleware.py: 3600, 5, 300, 10000 硬编码
- routes/admin.py: 64, 3600 硬编码
- 改进: 提取常量模块 `config/constants.py`

#### 3. 缺少类型注解
- routes/api.py: `get_agent()`, `create_api_routes()` 无类型
- routes/admin.py: `create_admin_routes()` 无类型
- middleware.py: 工具函数无类型
- 改进: 添加完整类型注解

#### 4. 未使用的导入
- main.py: `sys`, `Optional`
- routes/api.py: `Optional`
- 改进: 清理

#### 5. CORS 配置重复加载
- main.py 模块级加载 config.yaml 用于 CORS
- lifespan 又加载一次
- 改进: 提取 `load_config()` 函数，只加载一次

#### 6. 认证检查不一致
- routes/api.py `get_config` 手动检查 `hasattr(request.state, "user")`
- 改进: 使用 FastAPI Depends 依赖注入

#### 7. DB 文件名遗留 [已修复]
- db.py `DB_PATH` 已改为 `www_search.db`
- 旧文件 `mlx_server.db` 已删除
- DEPLOY.md 中的引用已更新为 `www_search.db`

### P1 - 应该修复

#### 8. init_admin_config 模块加载时机
- middleware.py 模块加载时就调用 init_admin_config()
- 测试导入时如果没设环境变量会崩溃
- 改进: 延迟初始化，在 main.py lifespan 中调用

#### 9. 日志级别硬编码
- 每个模块 `logger.setLevel(logging.INFO)` 重复
- 改进: 统一在 main.py 配置，子模块继承

#### 10. 信号处理器问题
- main.py 信号处理器重新发信号可能死循环
- 改进: 设置标志位防止重复处理

---

## 实施计划

### Phase 1: 常量提取
- 创建 `config/constants.py`
- 迁移所有魔法数字

### Phase 2: 工具函数提取
- 提取 `_parse_flash_messages()`
- 提取 `load_config()`
- 提取 `get_current_user()` 依赖

### Phase 3: 类型注解
- 所有公共函数添加类型注解
- 使用 `typing` 模块

### Phase 4: 清理
- 移除未使用导入
- 统一日志配置
- 修复信号处理器
- DB 文件重命名

### Phase 5: 测试验证
- 确保所有 109 个测试通过