"""
手动下载 DINOv2 模型的辅助脚本
用于解决 SSL 证书验证失败或网络问题
"""

import sys
import ssl
import urllib.request
import os


def setup_ssl_context():
    """设置 SSL 上下文，允许不验证证书（仅用于模型下载）"""
    # 创建不验证证书的 SSL 上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


def download_model():
    """下载 DINOv2 模型"""
    print("开始下载 DINOv2 模型...")
    print("注意: 这可能需要一些时间，模型文件较大")
    
    # 设置 SSL 上下文（临时禁用证书验证）
    ssl_context = setup_ssl_context()
    
    # 临时设置全局 SSL 上下文
    old_context = ssl._create_default_https_context
    ssl._create_default_https_context = lambda: ssl_context
    
    try:
        import torch
        
        print("\n正在加载模型（会自动下载）...")
        model = torch.hub.load(
            'facebookresearch/dinov2',
            'dinov2_vits14',
            source='github',
            trust_repo=True,
            skip_validation=True
        )
        
        print("\n✓ 模型下载成功！")
        print(f"模型类型: {type(model)}")
        print("\n模型已缓存在本地，后续可以直接使用")
        
        return model
    
    except Exception as e:
        print(f"\n错误: 下载失败 - {e}")
        print("\n替代方案:")
        print("1. 使用 pip 安装 dinov2 包:")
        print("   pip install dinov2")
        print("\n2. 手动从 Hugging Face 下载:")
        print("   pip install transformers")
        print("   然后使用 transformers 库加载模型")
        raise
    
    finally:
        # 恢复原始的 SSL 上下文
        ssl._create_default_https_context = old_context


if __name__ == "__main__":
    try:
        download_model()
        print("\n完成！")
    except Exception as e:
        print(f"\n下载失败: {e}")
        sys.exit(1)

