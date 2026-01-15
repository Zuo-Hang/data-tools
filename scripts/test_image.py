"""
测试识别图片
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.ollama_client import OllamaClient


def test_image():
    """测试识别图片"""
    client = OllamaClient()
    model_name = "qwen2.5vl:latest"
    image_path = Path(__file__).parent / "image" / "10340.jpg"

    if not image_path.exists():
        print(f"错误: 图片文件不存在: {image_path}")
        return

    print("=" * 60)
    print(f"测试模型: {model_name}")
    print(f"图片路径: {image_path}")
    print("=" * 60)
    print()

    # 测试 1: 详细描述图片
    print("【测试 1】详细描述图片内容")
    print("-" * 60)
    prompt = "你是一个商业分析师，核心关注竞争对手的活动策略，这是一张竞争对手的app截图，请详细提取这个页面中你认为有价值的内容。要求简洁"
    print(f"提示词: {prompt}")
    print("回复: ", end="")
    response = client.vision_chat(model_name, image_path, prompt, stream=False)
    if response:
        print(response)
    # token 信息已在 vision_chat 中输出
    print()

    # 测试 2: 提取关键信息
    print("【测试 2】提取关键信息")
    print("-" * 60)
    prompt = "请提取这张图片中的关键信息，包括所有文字、数字、日期、时间等，以json格式返回"
    print(f"提示词: {prompt}")
    print("回复: ", end="")
    response = client.vision_chat(model_name, image_path, prompt, stream=False)
    if response:
        print(response)
    # token 信息已在 vision_chat 中输出
    print()

    # 测试 3: 流式输出
    print("【测试 3】流式输出描述")
    print("-" * 60)
    prompt = "请提取这个页面上和活动相关的内容，与钱相关的尤为重要。以json格式返回"
    print(f"提示词: {prompt}")
    print("回复: ", end="")
    response = client.vision_chat(model_name, image_path, prompt, stream=False)
    if response:
        print(response)
    print()

    print("=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_image()

