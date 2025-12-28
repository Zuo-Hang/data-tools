# 脚本包

包含项目的可执行脚本。

## 使用说明

脚本可以直接运行，例如：

```bash
python scripts/example_script.py
```

或者在项目根目录下运行：

```bash
python -m scripts.example_script
```

## 添加新脚本

1. 在 `scripts/` 目录下创建新的Python文件
2. 在文件顶部添加必要的导入和路径设置（参考 `example_script.py`）
3. 实现 `main()` 函数
4. 使用 `if __name__ == "__main__": main()` 作为入口点

