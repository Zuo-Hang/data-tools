#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 online.log 中满足条件的 name 是否在 conf.log 中。
条件：日期为 2026/02/07、2026/02/08 或 2026/02/09，且完成更新为"是"
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data" / "CHECK"
ONLINE_LOG = DATA_DIR / "online.log"
CONF_LOG = DATA_DIR / "conf.log"


def load_online_names() -> set[str]:
    """从 online.log 中提取满足条件的 name：日期 2026/02/07、2026/02/08 或 2026/02/09，完成更新为"是"。"""
    names = set()
    with open(ONLINE_LOG, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return names

    # 解析表头
    header = lines[0].strip().split("\t")
    try:
        name_idx = header.index("name")
        create_time_idx = header.index("create_time")
        update_idx = header.index("是否完成脚本更新")
    except ValueError as e:
        raise ValueError(f"online.log 表头缺少必要字段: {e}") from e

    for line in lines[1:]:
        parts = line.strip().split("\t")
        if len(parts) <= max(name_idx, create_time_idx, update_idx):
            continue

        create_time = parts[create_time_idx].strip()
        is_updated = parts[update_idx].strip()

        # 日期为 2026/02/07、2026/02/08 或 2026/02/09，且完成更新为"是"
        if is_updated != "是":
            continue
        # if "2026/02/07" not in create_time and "2026/02/08" not in create_time and "2026/02/09" not in create_time:
        #     continue

        name = parts[name_idx].strip()
        if name:
            names.add(name)

    return names


def load_conf_names() -> set[str]:
    """从 conf.log 中加载 dict_list 里的所有 name。支持多个 JSON 对象拼接。"""
    with open(CONF_LOG, "r", encoding="utf-8") as f:
        content = f.read()

    names = set()
    # conf.log 可能包含多个 JSON 对象拼接（}\n\n{ 分隔）
    parts = content.strip().split("}\n\n{")
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if not part.startswith("{"):
            part = "{" + part
        if not part.endswith("}"):
            part = part + "}"
        try:
            data = json.loads(part)
            names.update(data.get("dict_list", []))
        except json.JSONDecodeError:
            continue
    return names


def main():
    online_names = load_online_names()
    conf_names = load_conf_names()

    not_in_conf = sorted(online_names - conf_names)

    print(f"online.log 中满足条件的 name 数量: {len(online_names)}")
    print(f"conf.log 中 dict_list 数量: {len(conf_names)}")
    print(f"不在 conf.log 中的 name 数量: {len(not_in_conf)}")
    print("-" * 60)
    print("不在 conf.log 中的 name 列表:")
    for name in not_in_conf:
        print(name)


if __name__ == "__main__":
    main()
