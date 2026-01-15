"""
Ollama 本地 LLM 调用脚本
支持文本生成、聊天模式和视觉模型（图片识别）
"""

import base64
import json
import sys
from pathlib import Path
from typing import Optional, Union

import requests

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ollama API 基础地址
OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaClient:
    """Ollama 客户端类"""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        """
        初始化 Ollama 客户端

        Args:
            base_url: Ollama 服务的基础 URL
        """
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _print_token_info(data: dict):
        """
        打印 token 使用信息

        Args:
            data: API 响应数据
        """
        print("\n" + "-" * 60)
        print("Token 使用明细:")
        print("-" * 60)
        
        # 输入 token 信息
        prompt_eval_count = data.get("prompt_eval_count", 0)
        prompt_eval_duration = data.get("prompt_eval_duration", 0) / 1e9  # 转换为秒
        print(f"  输入 Token 数: {prompt_eval_count:,}")
        if prompt_eval_duration > 0:
            print(f"  输入处理时间: {prompt_eval_duration:.2f} 秒")
        
        # 输出 token 信息
        eval_count = data.get("eval_count", 0)
        eval_duration = data.get("eval_duration", 0) / 1e9  # 转换为秒
        print(f"  输出 Token 数: {eval_count:,}")
        if eval_duration > 0:
            print(f"  输出生成时间: {eval_duration:.2f} 秒")
        
        # 总 token 数
        total_tokens = prompt_eval_count + eval_count
        if total_tokens > 0:
            print(f"  总 Token 数: {total_tokens:,}")
        
        # 时间信息
        total_duration = data.get("total_duration", 0) / 1e9  # 转换为秒
        load_duration = data.get("load_duration", 0) / 1e9  # 转换为秒
        if total_duration > 0:
            print(f"  总耗时: {total_duration:.2f} 秒")
        if load_duration > 0:
            print(f"  模型加载时间: {load_duration:.2f} 秒")
        
        print("-" * 60)

    def list_models(self) -> list:
        """
        获取可用的模型列表

        Returns:
            模型列表
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except requests.exceptions.RequestException as e:
            print(f"获取模型列表失败: {e}")
            return []

    def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Optional[str]:
        """
        生成文本

        Args:
            model: 模型名称
            prompt: 提示词
            stream: 是否使用流式输出
            **kwargs: 其他参数（如 temperature, top_p 等）

        Returns:
            生成的文本（非流式）或 None（流式）
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs
        }

        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                stream=stream,
                timeout=300
            )
            response.raise_for_status()

            if stream:
                # 流式输出
                last_data = None
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "response" in data:
                                print(data["response"], end="", flush=True)
                            if data.get("done", False):
                                last_data = data
                                print()  # 换行
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                # 输出 token 信息
                if last_data:
                    self._print_token_info(last_data)
                return None
            else:
                # 非流式输出
                data = response.json()
                response_text = data.get("response", "")
                # 输出 token 信息（在返回前输出，这样调用者可以先打印回复，再看到 token 信息）
                # 注意：这里先输出 token 信息，调用者会在之后打印 response_text
                self._print_token_info(data)
                return response_text
        except requests.exceptions.RequestException as e:
            print(f"生成文本失败: {e}")
            return None

    def chat(
        self,
        model: str,
        messages: list,
        stream: bool = False,
        **kwargs
    ) -> Optional[str]:
        """
        聊天模式

        Args:
            model: 模型名称
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
                     对于视觉模型，content 可以是数组格式：
                     [{"type": "text", "text": "..."}, {"type": "image", "image": "base64_string"}]
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            生成的回复（非流式）或 None（流式）
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }

        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                stream=stream,
                timeout=300
            )
            response.raise_for_status()

            if stream:
                # 流式输出
                last_data = None
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "message" in data and "content" in data["message"]:
                                print(data["message"]["content"], end="", flush=True)
                            if data.get("done", False):
                                last_data = data
                                print()  # 换行
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                # 输出 token 信息
                if last_data:
                    self._print_token_info(last_data)
                return None
            else:
                # 非流式输出
                data = response.json()
                response_text = data.get("message", {}).get("content", "")
                # 输出 token 信息
                self._print_token_info(data)
                return response_text
        except requests.exceptions.RequestException as e:
            print(f"聊天失败: {e}")
            return None

    @staticmethod
    def encode_image(image_path: Union[str, Path]) -> str:
        """
        将图片编码为 base64 字符串

        Args:
            image_path: 图片文件路径

        Returns:
            base64 编码的图片字符串
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def vision_chat(
        self,
        model: str,
        image_path: Union[str, Path],
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Optional[str]:
        """
        视觉模型聊天（图片识别）
        使用 /api/generate 端点，支持 images 字段

        Args:
            model: 视觉模型名称（如 qwen2.5vl:latest）
            image_path: 图片文件路径
            prompt: 提示词（如 "请描述这张图片"）
            stream: 是否使用流式输出
            **kwargs: 其他参数

        Returns:
            生成的回复（非流式）或 None（流式）
        """
        # 编码图片为 base64
        base64_image = self.encode_image(image_path)

        # 使用 /api/generate 端点，images 字段传递图片
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [base64_image],  # 图片数组
            "stream": stream,
            **kwargs
        }

        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                stream=stream,
                timeout=300
            )
            response.raise_for_status()

            if stream:
                # 流式输出
                last_data = None
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            if "response" in data:
                                print(data["response"], end="", flush=True)
                            if data.get("done", False):
                                last_data = data
                                print()  # 换行
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                # 输出 token 信息
                if last_data:
                    self._print_token_info(last_data)
                return None
            else:
                # 非流式输出
                data = response.json()
                response_text = data.get("response", "")
                # 输出 token 信息（在返回前输出，这样调用者可以先打印回复，再看到 token 信息）
                # 注意：这里先输出 token 信息，调用者会在之后打印 response_text
                self._print_token_info(data)
                return response_text
        except requests.exceptions.RequestException as e:
            print(f"视觉模型调用失败: {e}")
            return None


def main():
    """主函数 - 示例用法"""
    client = OllamaClient()

    # 1. 列出可用模型
    print("=" * 50)
    print("可用模型列表:")
    print("=" * 50)
    models = client.list_models()
    if models:
        for model in models:
            model_name = model.get("name", "未知")
            print(f"  - {model_name}")
    else:
        print("  未找到可用模型")
    print()

    # 2. 示例：文本生成（非流式）
    print("=" * 50)
    print("示例 1: 文本生成（非流式）")
    print("=" * 50)
    # 自动获取第一个可用模型
    model_name = models[0].get("name", "llama3:latest") if models else "llama3:latest"
    prompt = "请用一句话介绍人工智能"
    print(f"提示词: {prompt}")
    print("回复: ", end="")
    response = client.generate(model_name, prompt, stream=False)
    if response:
        print(response)
    print()

    # 3. 示例：文本生成（流式）
    print("=" * 50)
    print("示例 2: 文本生成（流式）")
    print("=" * 50)
    prompt = "写一首关于春天的短诗"
    print(f"提示词: {prompt}")
    print("回复: ", end="")
    client.generate(model_name, prompt, stream=True)
    print()

    # 4. 示例：聊天模式（非流式）
    print("=" * 50)
    print("示例 3: 聊天模式（非流式）")
    print("=" * 50)
    messages = [
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
    print(f"用户: {messages[0]['content']}")
    print("助手: ", end="")
    response = client.chat(model_name, messages, stream=False)
    if response:
        print(response)
    print()

    # 5. 示例：聊天模式（流式）
    print("=" * 50)
    print("示例 4: 聊天模式（流式）")
    print("=" * 50)
    messages = [
        {"role": "user", "content": "Python 和 Java 有什么区别？"}
    ]
    print(f"用户: {messages[0]['content']}")
    print("助手: ", end="")
    client.chat(model_name, messages, stream=True)
    print()


if __name__ == "__main__":
    main()

