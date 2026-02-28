#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "用法: $0 <BASE_PATH>"
  echo "示例: $0 /user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_package_model_passenger_behavior_seq_feature/online_res"
  exit 1
fi

BASE_PATH="$1"
DATA_PATH="${BASE_PATH}/data"
BACKUP_PATH="${BASE_PATH}/data_backup"

echo "BASE_PATH = ${BASE_PATH}"
echo "DATA_PATH = ${DATA_PATH}"
echo "BACKUP_PATH = ${BACKUP_PATH}"

# 路径存在性检查
if ! hdfs dfs -test -e "${DATA_PATH}"; then
  echo "HDFS 路径不存在: ${DATA_PATH}"
  exit 1
fi

echo
echo "1) 查看文件数..."
hdfs dfs -ls "${DATA_PATH}"

echo
echo "2) 查看文件总大小..."
hdfs dfs -du -s -h "${DATA_PATH}"

echo
echo "3) 备份 data 到 data_backup..."
hdfs dfs -mv "${DATA_PATH}" "${BACKUP_PATH}"

echo
echo "4) 检查备份文件列表..."
hdfs dfs -ls "${BACKUP_PATH}"

echo
echo "5) 检查备份总大小..."
hdfs dfs -du -s -h "${BACKUP_PATH}"

echo
echo "完成。"

