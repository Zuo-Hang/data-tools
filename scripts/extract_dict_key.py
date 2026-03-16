#!/usr/bin/env python3
"""
从 Untitled-25.txt 中提取每个 curl 请求的 dict 和 key，生成 CSV 文件
"""
import re
import sys
from pathlib import Path


def extract_dict_key(content: str) -> list[tuple[str, str]]:
    """从文本中提取 dict 和 key 对"""
    # 匹配 keys":[{"key": "xxx", "dict": "yyy"}] 格式
    pattern = r'"keys":\s*\[\s*\{\s*"key":\s*"([^"]+)"\s*,\s*"dict":\s*"([^"]+)"'
    matches = re.findall(pattern, content)
    results = [(dict_val, key_val) for key_val, dict_val in matches]
    # 过滤无效 dict（如粘贴错误产生的 dict_curl... 等）
    return [(d, k) for d, k in results if d.startswith("dict_auto_hive2ddict")]


def main():
    input_file = Path(__file__).parent / "data1" / "Untitled-25.txt"
    output_file = Path(__file__).parent / "data1" / "dict_key_list.csv"

    if not input_file.exists():
        print(f"错误: 输入文件不存在 {input_file}", file=sys.stderr)
        sys.exit(1)

    content = input_file.read_text(encoding="utf-8")
    results = extract_dict_key(content)

    # 去重，保持顺序
    seen = set()
    unique_results = []
    for d, k in results:
        if (d, k) not in seen:
            seen.add((d, k))
            unique_results.append((d, k))

    # 写入 CSV
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("dict,key\n")
        for dict_val, key_val in unique_results:
            f.write(f'"{dict_val}","{key_val}"\n')

    print(f"已提取 {len(unique_results)} 条记录，保存到 {output_file}")


if __name__ == "__main__":
    main()
