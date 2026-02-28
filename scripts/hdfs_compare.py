import argparse
import os

from pyspark.sql import SparkSession

# 默认对比 process_seq_order 的输入与输出目录（与 process_seq_order.py 保持一致）
DEFAULT_INPUT_DIR = (
    "hdfs:///user/engine_arch/gizzle_online/offline_schedule_data/"
    "auto_hive2ddict_package_model_passenger_behavior_seq_feature/online_res/data_backup"
)
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT_DIR.replace("data_backup", "data")


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="对比 process_seq_order 的输入(data_backup)与输出(data)目录内容（按整行对比）"
  )
  parser.add_argument(
    "--path1",
    default=DEFAULT_INPUT_DIR,
    help="输入目录（data_backup），默认与 process_seq_order 一致",
  )
  parser.add_argument(
    "--path2",
    default=DEFAULT_OUTPUT_DIR,
    help="输出目录（data），默认与 process_seq_order 一致",
  )
  parser.add_argument(
    "--output-dir",
    help="可选：结果输出目录（HDFS 或本地），会生成 only_in_1 / only_in_2 / in_both 三个子目录",
  )
  return parser.parse_args()


def main() -> None:
  args = parse_args()

  spark = (
    SparkSession.builder.appName("HDFSFilesCompare")
    .getOrCreate()
  )

  # 读取两个路径下所有文件为文本行，去重后按“整行”对比
  df1 = spark.read.text(args.path1).select("value").distinct()
  df2 = spark.read.text(args.path2).select("value").distinct()

  only_in_1 = df1.join(df2, on="value", how="left_anti")
  only_in_2 = df2.join(df1, on="value", how="left_anti")
  in_both = df1.join(df2, on="value", how="inner")

  cnt1 = df1.count()
  cnt2 = df2.count()
  cnt_only_1 = only_in_1.count()
  cnt_only_2 = only_in_2.count()
  cnt_both = in_both.count()

  print(f"输入(data_backup) 唯一行数: {cnt1}")
  print(f"输出(data) 唯一行数: {cnt2}")
  print(f"仅在输入中的行数: {cnt_only_1}")
  print(f"仅在输出中的行数: {cnt_only_2}")
  print(f"两边都存在的行数: {cnt_both}")

  # 如需要，将结果写出
  if args.output_dir:
    base = args.output_dir.rstrip("/")
    only_in_1.write.mode("overwrite").text(os.path.join(base, "only_in_1"))
    only_in_2.write.mode("overwrite").text(os.path.join(base, "only_in_2"))
    in_both.write.mode("overwrite").text(os.path.join(base, "in_both"))
    print(f"结果已写入: {base}/only_in_1, {base}/only_in_2, {base}/in_both")

  spark.stop()


if __name__ == "__main__":
  main()

