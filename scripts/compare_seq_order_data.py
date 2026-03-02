#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PySpark 任务：对比 process_seq_order 处理前后的数据。

逻辑：
1. 读取 HDFS 文件，生成 RDD
2. RDD.map：反解析 JSON 到结构体，提取 key、merge_field 值，生成 Dataset
3. 行数比对
4. Dataset.join：根据 key 关联，对比 merge_field diff
"""

import argparse
import json
from typing import List, Optional, Tuple

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, StringType, StructField, StructType

# 默认路径（与 process_seq_order 一致）
DEFAULT_BACKUP_DIR = (
    "hdfs:///user/engine_arch/gizzle_online/offline_schedule_data/"
    "auto_hive2ddict_package_model_passenger_behavior_seq_feature/online_res/data_backup"
)
DEFAULT_DATA_DIR = DEFAULT_BACKUP_DIR.replace("data_backup", "data")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="对比 process_seq_order 处理前后 data_backup 与 data 的 key、merge_field 差异"
    )
    parser.add_argument(
        "--backup-dir",
        default=DEFAULT_BACKUP_DIR,
        help="处理前目录（data_backup）",
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="处理后目录（data）",
    )
    parser.add_argument(
        "--key-field",
        default="key",
        help="JSON 中用作关联的 key 字段名，默认 key",
    )
    parser.add_argument(
        "--output-dir",
        help="可选：将 diff 结果写出到 HDFS 或本地",
    )
    return parser.parse_args()


def parse_line_to_key_and_merge_fields(
    line: str, key_field: str = "key"
) -> Optional[Tuple[str, List[str]]]:
    """
    解析一行 JSON，提取 key 和 fieldvalues 中以 merge_field 开头的字符串列表。
    与 process_seq_order 一致：去重且保持原有顺序。
    解析失败返回 None。
    """
    if not line or not line.strip():
        return None
    try:
        obj = json.loads(line)
    except Exception:
        return None

    key = obj.get(key_field)
    if key is None:
        key = str(hash(line))  # 无 key 时用整行 hash 作为 fallback

    fv = obj.get("fieldvalues")
    merge_fields = []
    seen = set()
    if isinstance(fv, list):
        for v in fv:
            if isinstance(v, str) and v.startswith("merge_field"):
                if v in seen:
                    continue
                seen.add(v)
                merge_fields.append(v)

    return (str(key), merge_fields)


def main() -> None:
    args = parse_args()

    spark = (
        SparkSession.builder
        .appName("CompareSeqOrderData")
        .getOrCreate()
    )

    schema = StructType([
        StructField("key", StringType(), False),
        StructField("merge_fields", ArrayType(StringType()), False),
    ])

    def parse_backup(line: str):
        r = parse_line_to_key_and_merge_fields(line, args.key_field)
        return r if r else ("__parse_fail__", [])

    def parse_data(line: str):
        r = parse_line_to_key_and_merge_fields(line, args.key_field)
        return r if r else ("__parse_fail__", [])

    # 1. 读取 HDFS 文件，生成 RDD
    rdd_backup = spark.sparkContext.textFile(args.backup_dir)
    rdd_data = spark.sparkContext.textFile(args.data_dir)

    # 2. RDD.map：反解析 JSON 到结构体，提取 key、merge_field 值，生成 Dataset
    backup_rows = rdd_backup.map(parse_backup)
    data_rows = rdd_data.map(parse_data)

    df_backup = spark.createDataFrame(backup_rows, schema)
    df_data = spark.createDataFrame(data_rows, schema)

    df_backup = df_backup.filter(F.col("key") != "__parse_fail__")
    df_data = df_data.filter(F.col("key") != "__parse_fail__")

    # 3. 行数比对
    cnt_backup = df_backup.count()
    cnt_data = df_data.count()

    print("=" * 60)
    print("行数比对")
    print("=" * 60)
    print(f"data_backup 行数: {cnt_backup}")
    print(f"data 行数: {cnt_data}")
    print(f"行数差异: {cnt_data - cnt_backup}")
    print()

    # 4. Dataset.join：根据 key 关联，对比 merge_field diff
    joined = df_backup.alias("b").join(
        df_data.alias("d"),
        F.col("b.key") == F.col("d.key"),
        "full_outer",
    ).select(
        F.coalesce(F.col("b.key"), F.col("d.key")).alias("key"),
        F.col("b.merge_fields").alias("backup_merge_fields"),
        F.col("d.merge_fields").alias("data_merge_fields"),
    )

    fields_to_str_udf = F.udf(
        lambda arr: "|".join(arr) if arr else "",
        StringType(),
    )
    joined = joined.withColumn("backup_str", fields_to_str_udf("backup_merge_fields"))
    joined = joined.withColumn("data_str", fields_to_str_udf("data_merge_fields"))

    only_in_backup = joined.filter(F.col("data_merge_fields").isNull())
    only_in_data = joined.filter(F.col("backup_merge_fields").isNull())
    merge_field_diff = joined.filter(
        F.col("backup_merge_fields").isNotNull()
        & F.col("data_merge_fields").isNotNull()
        & (F.col("backup_str") != F.col("data_str"))
    )
    merge_field_same = joined.filter(
        F.col("backup_merge_fields").isNotNull()
        & F.col("data_merge_fields").isNotNull()
        & (F.col("backup_str") == F.col("data_str"))
    )

    cnt_only_backup = only_in_backup.count()
    cnt_only_data = only_in_data.count()
    cnt_diff = merge_field_diff.count()
    cnt_same = merge_field_same.count()

    print("=" * 60)
    print("按 key 关联后的 merge_field 对比")
    print("=" * 60)
    print(f"仅在 data_backup 中的 key 数: {cnt_only_backup}")
    print(f"仅在 data 中的 key 数: {cnt_only_data}")
    print(f"两边都有但 merge_field 不同: {cnt_diff}")
    print(f"两边都有且 merge_field 相同: {cnt_same}")
    print()

    if cnt_diff > 0:
        print("=" * 60)
        print("merge_field 差异样例（前 5 条）")
        print("=" * 60)
        for row in merge_field_diff.limit(5).collect():
            print(f"key: {row['key']}")
            print(f"  backup: {row['backup_merge_fields']}")
            print(f"  data:   {row['data_merge_fields']}")
            print()

    if args.output_dir:
        base = args.output_dir.rstrip("/")
        only_in_backup.select("key", "backup_merge_fields").write.mode("overwrite").json(
            f"{base}/only_in_backup"
        )
        only_in_data.select("key", "data_merge_fields").write.mode("overwrite").json(
            f"{base}/only_in_data"
        )
        merge_field_diff.write.mode("overwrite").json(f"{base}/merge_field_diff")
        print(f"结果已写入: {base}/only_in_backup, {base}/only_in_data, {base}/merge_field_diff")

    spark.stop()


if __name__ == "__main__":
    main()
