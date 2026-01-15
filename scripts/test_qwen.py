"""
测试 qwen2.5vl 模型
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ollama_client import OllamaClient


def test_qwen():
    """测试 qwen2.5vl 模型"""
    client = OllamaClient()
    model_name = "qwen2.5vl:latest"

    print("=" * 60)
    print(f"测试模型: {model_name}")
    print("=" * 60)
    print()

    # 测试 1: 文本生成（非流式）
    print("【测试 1】文本生成（非流式）")
    print("-" * 60)
    prompt = "你好，请介绍一下你自己"
    print(f"提示词: {prompt}")
    print("回复: ", end="")
    response = client.generate(model_name, prompt, stream=False)
    if response:
        print(response)
    print()

    # 测试 2: 文本生成（流式）
    print("【测试 2】文本生成（流式）")
    print("-" * 60)
    prompt = "用一句话解释什么是机器学习"
    print(f"提示词: {prompt}")
    print("回复: ", end="")
    client.generate(model_name, prompt, stream=True)
    print()

    # 测试 3: 聊天模式（非流式）
    print("【测试 3】聊天模式（非流式）")
    print("-" * 60)
    messages = [
        {"role": "user", "content": "Python 和 Java 有什么区别？请简要说明"}
    ]
    print(f"用户: {messages[0]['content']}")
    print("助手: ", end="")
    response = client.chat(model_name, messages, stream=False)
    if response:
        print(response)
    print()

    # 测试 4: 聊天模式（流式）
    print("【测试 4】聊天模式（流式）")
    print("-" * 60)
    messages = [
        {"role": "user", "content": "写一首关于编程的短诗"}
    ]
    print(f"用户: {messages[0]['content']}")
    print("助手: ", end="")
    client.chat(model_name, messages, stream=True)
    print()

    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_qwen()

