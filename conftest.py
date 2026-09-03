"""Pytest 共享配置和 fixtures"""

import os
import sys

# 设置测试环境变量（在所有测试之前）
os.environ.setdefault("WWW_SEARCH_ADMIN_PASSWORD", "test_password")
os.environ.setdefault("WWW_SEARCH_SECRET_KEY", "test_secret_key_for_testing_32chars")

sys.path.insert(0, os.path.dirname(__file__))


def pytest_configure(config):
    """Pytest 启动时初始化 admin 配置"""
    from middleware import init_admin_config

    try:
        init_admin_config()
    except RuntimeError:
        pass  # 可能已经初始化过了
