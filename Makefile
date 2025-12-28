.PHONY: help install install-dev test lint format clean

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装项目
	pip install -e .

install-dev: ## 安装开发依赖
	pip install -e ".[dev]"

test: ## 运行测试
	pytest

lint: ## 代码检查
	flake8 data_tools tests
	mypy data_tools

format: ## 代码格式化
	black data_tools tests
	isort data_tools tests

clean: ## 清理构建文件
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

