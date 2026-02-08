"""
解析免佣卡相关日志（a.log）的 params 字段，导出为 CSV。

使用方式（示例）：
    python scripts/no_commission_card_parse.py
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional


# 日志文件路径 & 输出 CSV 路径（可按需修改）
# 当前日志文件名为 a.log，如后续固定为 no_commission_card.log，可同步调整此处
LOG_PATH = Path(__file__).parent / "data" / "a.log"
OUTPUT_CSV_PATH = Path(__file__).parent / "data" / "no_commission_card_params.csv"

# CSV 字段顺序（严格按业务结构体的 json tag 排列）
# 注意：按你的要求，将 image_url 放在第一个字段
FIELDNAMES = [
    "image_url",
    "estimate_id",
    "province",
    "city_name",
    "driver_platform",
    "activity_type",
    "activity_breakdown",
    "activity_zone_image_urls",
    "activity_detail_image_urls",
    "driver_category",
    "submit_time",
    "submit_timestamp_ms",
    "event_time",
    "is_recognized",
    "activity_name_result",
    "activity_city_result",
    "activity_fence",
    "discount_rules",
    "validity_period_start_time",
    "validity_period_end_time",
    "applicable_time_period",
    "order_timeliness_type",
    "order_categories",
    "dis_range",
    "purchase_start_time",
    "purchase_end_time",
    "reduce_after_price",
    "est_price",
]


def _extract_params_from_json_line(obj: Dict) -> Optional[Dict]:
    """从整行 JSON 日志对象中提取 params 字段。"""
    params = obj.get("params")
    if isinstance(params, dict):
        return params
    return None


def _extract_params_from_text_line(line: str) -> Optional[Dict]:
    """
    从普通文本日志中提取 params 部分。

    支持两种常见形式：
    1. 行本身是 JSON，且包含 "params": {...}
    2. 行中包含类似 `params={...}` 或 `params: {...}`，并且 {...} 是 JSON 格式
    """
    text = line.strip()
    if not text:
        return None

    # 1. 整行尝试按 JSON 解析
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        obj = None

    if isinstance(obj, dict):
        params = _extract_params_from_json_line(obj)
        if params is not None:
            return params

    # 2. 从行内提取 params={...} / "params": {...}
    #   - 先找 "params": {...}
    m = re.search(r'"params"\s*:\s*(\{.*\})', text)
    if not m:
        #   - 再找 params={...} 或 params: {...}
        m = re.search(r'\bparams\s*[:=]\s*(\{.*\})', text)

    if not m:
        return None

    candidate = m.group(1)
    # 尝试解析为 JSON；如果日志里用的是单引号，可以做一次替换再试
    for value in (candidate, candidate.replace("'", '"')):
        try:
            obj = json.loads(value)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    return None


def _iter_params_from_log(lines: Iterable[str]) -> List[Dict]:
    """
    遍历日志行，提取所有 params 字段。

    需求：按照 activity_detail_image_urls 去重，
    相同 activity_detail_image_urls 的多行只保留一行（保留最后出现的一行）。
    """
    # key: activity_detail_image_urls, value: 对应的 params
    by_detail_image: Dict[Optional[str], Dict] = {}

    for line in lines:
        params = _extract_params_from_text_line(line)
        if not params:
            continue

        key = params.get("activity_detail_image_urls")
        # 后出现的记录会覆盖之前相同 key 的记录
        by_detail_image[key] = params

    return list(by_detail_image.values())


def _write_params_to_csv(params_list: List[Dict], output_path: Path) -> None:
    """将一组 params 字典写入 CSV，列顺序固定为 FIELDNAMES。"""
    if not params_list:
        print("未从日志中解析出任何 params，未生成 CSV。")
        return

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for params in params_list:
            # 按固定字段顺序写入，缺失字段留空
            row = {k: params.get(k, "") for k in FIELDNAMES}
            writer.writerow(row)

    print(f"已将 {len(params_list)} 条 params 写入 CSV：{output_path}")


def main() -> None:
    if not LOG_PATH.exists():
        print(f"日志文件不存在：{LOG_PATH}")
        return

    print(f"读取日志文件：{LOG_PATH}")
    with LOG_PATH.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    params_list = _iter_params_from_log(lines)
    print(f"解析到 params 条数：{len(params_list)}")

    _write_params_to_csv(params_list, OUTPUT_CSV_PATH)


if __name__ == "__main__":
    main()

