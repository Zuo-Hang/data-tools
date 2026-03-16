#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PySpark 任务：检查 HDFS 路径下文件是否存在，抽样检查是否包含 merge_field<TAB> 关键字。

逻辑：
1. 检查 HDFS 目标路径是否存在且有文件
2. 若存在：对行级别内容抽样，解析 JSON fieldvalues 检查是否包含 merge_field\t
3. 若不存在 merge_field\t：输出该路径
"""

import argparse
import json
from typing import List, Optional, Tuple

from pyspark.sql import SparkSession

# 默认待检查路径（与 hdfs_check_merge_field.sh 一致）
DEFAULT_PATHS = [
    "hdfs:///user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_package_model_passenger_behavior_seq_feature/online_res/data_backup",
    "hdfs:///user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_no_pkg_seq_feature/online_res/data_backup",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检查 HDFS 路径是否存在，抽样检查 merge_field\\t 关键字"
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=DEFAULT_PATHS,
        help="待检查的 HDFS 路径列表，默认内置路径",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
        help="每个路径抽样行数，默认 500",
    )
    return parser.parse_args()


def has_merge_field_in_line(line: str) -> bool:
    """检查一行 JSON 的 fieldvalues 中是否包含以 merge_field<TAB> 开头的字符串。"""
    if not line:
        return False
    try:
        obj = json.loads(line)
    except Exception:
        return False
    fv = obj.get("fieldvalues")
    if not isinstance(fv, list):
        return False
    for v in fv:
        if isinstance(v, str) and v.startswith("merge_field\t"):
            return True
    return False


def check_path(
    spark: SparkSession, path: str, sample_size: int
) -> Tuple[str, str, bool, Optional[bool]]:
    """
    检查单个 HDFS 路径。
    返回: (path, task_name, path_exists, has_merge_field)
    has_merge_field 为 None 表示路径不存在或为空，无法检查。
    """
    jvm = spark.sparkContext._jvm
    Path = jvm.org.apache.hadoop.fs.Path
    FileSystem = jvm.org.apache.hadoop.fs.FileSystem
    conf = spark.sparkContext._jsc.hadoopConfiguration()

    uri = jvm.java.net.URI(path)
    fs = FileSystem.get(uri, conf)
    p = Path(path)

    try:
        if not fs.exists(p):
            return (path, _task_name(path), False, None)
        status = fs.getFileStatus(p)
        if not status.isDirectory():
            return (path, _task_name(path), True, None)  # 是文件非目录，暂不处理
        statuses = fs.listStatus(p)
        if not statuses:
            return (path, _task_name(path), True, None)  # 空目录
    except Exception:
        return (path, _task_name(path), False, None)

    # 路径存在且有文件，抽样检查
    try:
        df = spark.read.text(path)
        sample_rows = df.limit(sample_size).collect()
    except Exception:
        return (path, _task_name(path), True, None)

    found = any(has_merge_field_in_line(row.value) for row in sample_rows)
    return (path, _task_name(path), True, found)


def _task_name(path: str) -> str:
    """从路径提取任务名（倒数第二段）。"""
    parts = path.rstrip("/").split("/")
    return parts[-2] if len(parts) >= 2 else path


def _normalize_hdfs_path(path: str) -> str:
    """确保路径带 hdfs:// 前缀，供 Spark 和 FileSystem 使用。"""
    path = path.strip()
    if path.startswith("hdfs://"):
        return path
    return "hdfs://" + path if path.startswith("/") else "hdfs:///" + path


def main() -> None:
    args = parse_args()

    spark = (
        SparkSession.builder
        .appName("CheckMergeField")
        .config("spark.executor.memory", "2g")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )

    results: List[Tuple[str, str, bool, Optional[bool]]] = []
    for raw_path in args.paths:
        path = _normalize_hdfs_path(raw_path)
        r = check_path(spark, path, args.sample_size)
        results.append(r)

    # 输出汇总
    print("=" * 70)
    print("HDFS 路径 merge_field\\t 检查结果")
    print("=" * 70)
    printfmt = "%-50s %-12s %s"
    print(printfmt % ("任务名", "路径存在", "merge_field\\t"))
    print("-" * 70)

    not_found_paths: List[str] = []
    for path, task_name, exists, has_mf in results:
        exists_str = "是" if exists else "否"
        if has_mf is None:
            mf_str = "-" if not exists else "无法检查"
        else:
            mf_str = "存在" if has_mf else "不存在"
            if exists and not has_mf:
                not_found_paths.append(path)
        print(printfmt % (task_name[:50], exists_str, mf_str))

    print("=" * 70)
    if not_found_paths:
        print("未发现 merge_field\\t 的路径（输出）：")
        for p in not_found_paths:
            print(f"  {p}")
    else:
        print("所有可检查路径均包含 merge_field\\t，或路径不存在/为空")

    spark.stop()


if __name__ == "__main__":
    main()
