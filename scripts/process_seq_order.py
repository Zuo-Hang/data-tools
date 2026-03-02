#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PySpark 任务：
1. 读取指定 HDFS 目录下的所有 .gz 文本文件（每行一个 JSON）。
2. 解析每行 JSON，对 fieldvalues 字段进行过滤：
   - 仅保留以 'merge_field' 开头的字符串
   - 在 fieldvalues 内部去重，保持原有顺序
3. 其他字段保持不变。
4. 将处理后的 JSON 行写入新的 HDFS 目录：
   - 如未显式指定 output-dir，则将 input-dir 中的 'data_backup' 替换为 'data'。
5. 将 Spark 输出的 part-*-uuid-c000.txt.gz 重命名为 part-00000.gz 格式，
   与 data_backup 中的 part-00199.gz 命名方式对齐。
"""

import argparse
import json
import re
import subprocess
from typing import Optional

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# 默认 HDFS 路径（可通过 --input-dir / --output-dir 覆盖）
DEFAULT_INPUT_DIR = (
    "hdfs:///user/engine_arch/gizzle_online/offline_schedule_data/"
    "auto_hive2ddict_package_model_passenger_behavior_seq_feature/online_res/data_backup"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="过滤 JSON fieldvalues 中的 merge_field* 字符串并写回 HDFS"
    )
    parser.add_argument(
        "--input-dir",
        default=DEFAULT_INPUT_DIR,
        help="输入 HDFS 目录（包含 .gz 文件），默认: data_backup 路径",
    )
    parser.add_argument(
        "--output-dir",
        help="输出 HDFS 目录（若不指定，则自动将 input-dir 中的 'data_backup' 替换为 'data'）",
    )
    return parser.parse_args()


def build_output_dir(input_dir: str, output_dir: Optional[str]) -> str:
    if output_dir:
        return output_dir
    return input_dir.replace("data_backup", "data")


def rename_output_to_legacy_format(output_dir: str) -> None:
    """
    将 Spark 输出的 part-*-uuid-c000.txt.gz 重命名为 part-*.gz，
    与 data_backup 中的 part-00199.gz 格式对齐。
    """
    # hdfs dfs -ls 可能返回带 hdfs:// 的路径，需统一处理
    result = subprocess.run(
        ["hdfs", "dfs", "-ls", output_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode != 0:
        return

    files_to_rename = []
    for line in result.stdout.strip().split("\n"):
        if not line or line.startswith("Found"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        path = parts[-1]
        # 匹配 part-00000-uuid-c000.txt.gz 或 part-00000.txt.gz
        match = re.search(r"part-(\d+)(?:-[a-f0-9-]+-c\d+)?\.txt\.gz$", path)
        if match:
            num = match.group(1).zfill(5)  # 补零为 5 位，与 part-00199.gz 格式一致
            dir_part = path.rsplit("/", 1)[0]
            new_path = f"{dir_part}/part-{num}.gz"
            if path != new_path:
                files_to_rename.append((path, new_path))

    files_to_rename.sort(key=lambda x: x[1])
    for old_path, new_path in files_to_rename:
        subprocess.run(["hdfs", "dfs", "-mv", old_path, new_path], check=True)


def filter_fieldvalues(line: str) -> str:
    """
    对一行 JSON 文本做处理：
    - 解析 JSON
    - 只保留 fieldvalues 中以 'merge_field' 开头的字符串
    - 在 fieldvalues 内部做去重，保持原有顺序
    - 其它字段保持不变
    解析失败则原样返回，避免任务整体失败。
    """
    if not line:
        return line
    try:
        obj = json.loads(line)
    except Exception:
        return line

    fv = obj.get("fieldvalues")
    if isinstance(fv, list):
        seen = set()
        new_vals = []
        for v in fv:
            if isinstance(v, str) and v.startswith("merge_field"):
                if v not in seen:
                    seen.add(v)
                    new_vals.append(v)
        obj["fieldvalues"] = new_vals

    return json.dumps(obj, ensure_ascii=False)


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir
    output_dir = build_output_dir(args.input_dir, args.output_dir)

    spark = (
        SparkSession.builder
        .appName("FilterSeqOrderFieldvalues")
        .getOrCreate()
    )

    # 1. 读取指定 HDFS 目录下所有 .gz 文本文件（Spark 会自动解压 .gz）
    #    同时记录每行所属的源文件名，用于统计输入文件数。
    df = spark.read.text(input_dir).withColumn("src_file", F.input_file_name())

    # 统计输入文件数，用于控制输出的分区数（≈输出文件数）
    num_input_files = df.select("src_file").distinct().count()
    if num_input_files <= 0:
        num_input_files = 1

    # 2~3. 对每行 JSON 的 fieldvalues 做过滤 + 去重
    filter_udf = F.udf(filter_fieldvalues, StringType())
    processed_df = df.select(filter_udf("value").alias("value"))

    # 按输入文件数设置分区数，使输出文件数与输入文件数大致一致
    out_df = processed_df.repartition(num_input_files)

    # 4. 写回新的 HDFS 目录，使用 gzip 压缩
    (
        out_df.write
        .mode("overwrite")
        .option("compression", "gzip")
        .text(output_dir)
    )

    # 5. 将 Spark 输出的 part-*-uuid-c000.txt.gz 重命名为 part-*.gz，与 data_backup 格式对齐
    rename_output_to_legacy_format(output_dir)

    spark.stop()


if __name__ == "__main__":
    main()

