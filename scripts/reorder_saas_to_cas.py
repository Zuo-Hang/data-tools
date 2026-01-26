"""
将 `scripts/data/saas.log` 中的字段顺序重排为 CAS 所需顺序，并生成 `.cas` 文件。

当前 saas.log 字段顺序（按索引 0 开始）：
0  estimate_id
1  supplier_name
2  driver_id
3  driver_last_name
4  car_type
5  car_number
6  product_type
7  start_date
8  end_date
9  summary_order_count
10 driver_cancel_count
11 online_duration
12 peak_online_duration
13 ok_server_day_count
14 serve_duration
15 income_amount
16 reward_amount
17 images
18 performance_order_count
19 source_type
20 city_name
21 activity_name
22 city_illegal
23 platform
24 week_number
25 platform_income_total
26 base_fare
27 reward
28 other
29 channel_reward
30 代码占位字段

目标 CAS 字段顺序：
images
estimate_id
supplier_name
driver_id
driver_last_name
car_type
car_number
product_type
start_date
end_date
summary_order_count（完单量）
driver_cancel_count(司机取消量)
online_duration（出车时长）
peak_online_duration（高峰出车时长）
ok_server_day_count
serve_duration（服务时长）
income_amount（订单流水）
reward_amount（奖励金额）
performance_order_count（完单量）
source_type
city_name
activity_name
city_illegal
platform
"""

import sys
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "scripts" / "data"
DEFAULT_INPUT = DATA_DIR / "saas.log"
# 默认输出 CSV 文件
DEFAULT_OUTPUT = DATA_DIR / "saas.csv"


ORIGINAL_FIELDS: List[str] = [
    "estimate_id",
    "supplier_name",
    "driver_id",
    "driver_last_name",
    "car_type",
    "car_number",
    "product_type",
    "start_date",
    "end_date",
    "summary_order_count",
    "driver_cancel_count",
    "online_duration",
    "peak_online_duration",
    "ok_server_day_count",
    "serve_duration",
    "income_amount",
    "reward_amount",
    "images",
    "performance_order_count",
    "source_type",
    "city_name",
    "activity_name",
    "city_illegal",
    "platform",
    "week_number",
    "platform_income_total",
    "base_fare",
    "reward",
    "other",
    "channel_reward",
    "placeholder",
]


TARGET_ORDER: List[str] = [
    "images",
    "estimate_id",
    "supplier_name",
    "driver_id",
    "driver_last_name",
    "car_type",
    "car_number",
    "product_type",
    "start_date",
    "end_date",
    "summary_order_count",
    "driver_cancel_count",
    "online_duration",
    "peak_online_duration",
    "ok_server_day_count",
    "serve_duration",
    "income_amount",
    "reward_amount",
    "performance_order_count",
    "source_type",
    "city_name",
    "activity_name",
    "city_illegal",
    "platform",
]


def build_index_mapping() -> List[int]:
    """
    根据字段名构建从目标顺序到原始顺序的索引映射。

    Returns:
        一个列表，列表中第 i 个元素是 TARGET_ORDER[i] 在原始字段中的索引。
    """
    field_to_index = {name: idx for idx, name in enumerate(ORIGINAL_FIELDS)}
    indices: List[int] = []
    for name in TARGET_ORDER:
        if name not in field_to_index:
            raise ValueError(f"目标字段 '{name}' 不在原始字段列表中，请检查字段定义")
        indices.append(field_to_index[name])
    return indices


def reorder_line(line: str, indices: List[int], field_to_index: dict) -> str:
    """
    将一行按照给定索引顺序重排字段。
    使用字段名到索引的映射，确保每一行都能正确映射所有字段。
    先映射 TARGET_ORDER 中的字段，然后追加原始数据中不在 TARGET_ORDER 中的其他字段。

    Args:
        line: 原始行（以制表符分隔）
        indices: 目标字段在原始字段中的索引列表
        field_to_index: 字段名到原始数据索引的映射字典

    Returns:
        重排后的行（以逗号分隔的 CSV 行）
    """
    cols = line.rstrip("\n").split("\t")
    original_cols_count = len(cols)
    
    # 构建字段名到实际值的映射（基于原始数据的实际字段数）
    # 如果原始数据字段数少于 ORIGINAL_FIELDS，只映射实际存在的字段
    field_values = {}
    for idx, field_name in enumerate(ORIGINAL_FIELDS):
        if idx < original_cols_count:
            field_values[field_name] = cols[idx]
        else:
            field_values[field_name] = ""
    
    # 按照 TARGET_ORDER 的顺序，从 field_values 中获取值
    reordered = []
    for field_name in TARGET_ORDER:
        if field_name in field_values:
            value = field_values[field_name]
        else:
            # 如果字段不在映射中，使用空字符串
            value = ""
        reordered.append(value)
    
    # 追加原始数据中不在 TARGET_ORDER 中的其他字段
    # 这些字段按照它们在 ORIGINAL_FIELDS 中的顺序追加
    target_field_set = set(TARGET_ORDER)
    for idx, field_name in enumerate(ORIGINAL_FIELDS):
        if field_name not in target_field_set:
            # 这个字段不在 TARGET_ORDER 中，需要追加
            if idx < original_cols_count:
                reordered.append(cols[idx])
            else:
                reordered.append("")
    
    # 如果原始数据中有超出 ORIGINAL_FIELDS 定义的字段，也追加它们
    if original_cols_count > len(ORIGINAL_FIELDS):
        for idx in range(len(ORIGINAL_FIELDS), original_cols_count):
            reordered.append(cols[idx])
    
    # 简单 CSV：使用逗号分隔，需要处理字段中的逗号和引号
    # 如果字段包含逗号、引号或换行符，需要用引号括起来，并转义引号
    csv_cols = []
    for col in reordered:
        if ',' in col or '"' in col or '\n' in col or '\r' in col:
            # 转义引号：将 " 替换为 ""
            escaped = col.replace('"', '""')
            csv_cols.append(f'"{escaped}"')
        else:
            csv_cols.append(col)
    
    return ",".join(csv_cols)


def convert_file(input_path: Path, output_path: Path) -> None:
    """
    将输入文件按新字段顺序重排，写入 CSV 输出文件。
    """
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    indices = build_index_mapping()
    # 构建字段名到索引的映射，用于每行数据映射
    field_to_index = {name: idx for idx, name in enumerate(ORIGINAL_FIELDS)}

    output_path.parent.mkdir(parents=True, exist_ok=True)

    line_count = 0
    # 构建完整的表头：TARGET_ORDER 中的字段 + 不在 TARGET_ORDER 中的其他字段
    target_field_set = set(TARGET_ORDER)
    additional_fields = []
    for field_name in ORIGINAL_FIELDS:
        if field_name not in target_field_set:
            additional_fields.append(field_name)
    full_header = TARGET_ORDER + additional_fields
    
    with input_path.open("r", encoding="utf-8") as fin, output_path.open(
        "w", encoding="utf-8"
    ) as fout:
        # 写入表头（按目标字段顺序 + 其他字段）
        header = ",".join(full_header)
        fout.write(header + "\n")

        for line in fin:
            # 跳过空行
            if not line.strip():
                continue
            reordered = reorder_line(line, indices, field_to_index)
            fout.write(reordered + "\n")
            line_count += 1

    print(f"已将 {line_count} 行从 {input_path} 重排并写入 {output_path}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="将 scripts/data/saas.log 的字段顺序重排为 CSV 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认输入/输出路径（生成 scripts/data/saas.csv）
  python scripts/reorder_saas_to_cas.py

  # 指定输入和输出文件
  python scripts/reorder_saas_to_cas.py \\
      --input scripts/data/saas.log \\
      --output scripts/data/saas.csv
        """,
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT),
        help="输入 saas.log 文件路径（默认: scripts/data/saas.log）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="输出 CSV 文件路径（默认: scripts/data/saas.csv）",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        convert_file(input_path, output_path)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


