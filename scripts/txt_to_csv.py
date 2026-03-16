#!/usr/bin/env python3
"""将 2.txt (dict key 空格分隔) 转为 dict_key_list.csv 格式"""
from pathlib import Path

input_file = Path(__file__).parent / "data1" / "2.txt"
output_file = Path(__file__).parent / "data1" / "dict_key_list.csv"

lines = input_file.read_text(encoding="utf-8").strip().splitlines()
rows = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    parts = line.split(None, 1)  # 按第一个空格分割
    if len(parts) == 2:
        dict_val, key_val = parts
        rows.append((dict_val, key_val))

with open(output_file, "w", encoding="utf-8") as f:
    f.write("dict,key\n")
    for dict_val, key_val in rows:
        f.write(f'"{dict_val}","{key_val}"\n')

print(f"已转换 {len(rows)} 条记录 -> {output_file}")
