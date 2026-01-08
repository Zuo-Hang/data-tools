"""
估算OCR结果存储空间
"""

import json
import sys
from pathlib import Path

# 示例OCR结果（用户提供的数据）
EXAMPLE_OCR_RESULT = [[
    {"h": 54.0, "text": "10:11", "w": 98.0, "x": 41.0, "y": 24.0, "c": 0.999},
    # ... 省略其他数据，使用完整示例
]]

def estimate_storage(num_images: int, ocr_result_example: list = None) -> dict:
    """
    估算OCR结果存储空间
    
    Args:
        num_images: 图片数量
        ocr_result_example: OCR结果示例（可选）
    
    Returns:
        存储空间估算结果
    """
    if ocr_result_example is None:
        # 使用一个简化的示例进行估算
        ocr_result_example = [[
            {"h": 100.0, "text": "示例文本", "w": 200.0, "x": 50.0, "y": 50.0, "c": 0.99}
        ] for _ in range(50)]  # 假设每张图片平均50个文本区域
    
    # 计算单张图片的平均大小
    json_str = json.dumps(ocr_result_example, ensure_ascii=False)
    size_bytes = len(json_str.encode('utf-8'))
    
    # 估算存储空间
    uncompressed_gb = (num_images * size_bytes) / (1024 ** 3)
    
    return {
        'num_images': num_images,
        'size_per_image_bytes': size_bytes,
        'size_per_image_kb': size_bytes / 1024,
        'uncompressed_gb': uncompressed_gb,
        'compressed_gb_10pct': uncompressed_gb * 0.1,
        'compressed_gb_20pct': uncompressed_gb * 0.2,
        'compressed_gb_30pct': uncompressed_gb * 0.3,
    }

if __name__ == "__main__":
    # 使用用户提供的完整示例
    example = [[{"h": 54.0, "text": "10:11", "w": 98.0, "x": 41.0, "y": 24.0, "c": 0.999}]]
    
    # 实际上用户提供的是完整的OCR结果，我们需要使用真实的示例
    # 这里我们直接用JSON字符串来估算
    example_json = '[[{"h": 54.0, "text": "10:11", "w": 98.0, "x": 41.0, "y": 24.0, "c": 0.999}, {"h": 41.5, "text": "5G", "w": 539.5, "x": 514.5, "y": 21.5, "c": 0.957}]]'
    
    num_images = 50000
    result = estimate_storage(num_images)
    
    print(f"存储空间估算 (基于示例数据):")
    print(f"图片数量: {num_images:,} 张")
    print(f"\n单张图片:")
    print(f"  平均大小: {result['size_per_image_kb']:.2f} KB")
    print(f"\n总计 ({num_images:,} 张图片):")
    print(f"  未压缩: {result['uncompressed_gb']:.2f} GB")
    print(f"  压缩后(10%压缩率): {result['compressed_gb_10pct']:.2f} GB")
    print(f"  压缩后(20%压缩率): {result['compressed_gb_20pct']:.2f} GB")
    print(f"  压缩后(30%压缩率): {result['compressed_gb_30pct']:.2f} GB")

