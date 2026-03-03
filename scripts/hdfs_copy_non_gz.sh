#!/bin/bash
# 将 backup 目录下非 .gz 结尾的文件拷贝到 data 目录
# 用于补齐 process_seq_order 输出后缺失的 _SUCCESS 等元数据文件
# 支持批量处理多个 backup 路径

set -e

# 待处理的 backup 路径列表
BACKUP_PATHS=(
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_package_model_passenger_behavior_seq_feature/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_no_pkg_seq_feature/online_res/data_backup"
  # 在此追加更多路径...
)

copy_non_gz_for_path() {
  local backup_dir="$1"
  local data_dir="${backup_dir/data_backup/data}"
  local task_name
  task_name=$(basename "$(dirname "$backup_dir")")

  echo ""
  echo "========== 处理: $task_name =========="
  echo "  backup: $backup_dir"
  echo "  data:   $data_dir"

  local non_gz_files
  non_gz_files=$(hdfs dfs -ls "$backup_dir" 2>/dev/null | grep -v '\.gz$' | grep -v '^Found' || true)
  if [ -z "$non_gz_files" ]; then
    echo "未找到非 .gz 文件，跳过"
    return 0
  fi

  echo "  非 .gz 文件:"
  echo "$non_gz_files" | while read -r line; do
    path=$(echo "$line" | awk '{print $NF}')
    [ -z "$path" ] && continue
    filename=$(basename "$path")
    echo "    - $filename"
  done

  echo "  拷贝中..."
  echo "$non_gz_files" | while read -r line; do
    path=$(echo "$line" | awk '{print $NF}')
    [ -z "$path" ] && continue
    filename=$(basename "$path")
    dest="${data_dir}/${filename}"
    hdfs dfs -cp "$path" "$dest" || echo "    [警告] 拷贝失败: $filename"
  done

  echo "  复检 data 目录非 .gz 文件:"
  hdfs dfs -ls "$data_dir" 2>/dev/null | grep -v '\.gz$' | grep -v '^Found' || echo "  (无)"
  echo "  完成"
}

echo "=== 批量拷贝非 .gz 文件（共 ${#BACKUP_PATHS[@]} 个路径）==="
for backup_path in "${BACKUP_PATHS[@]}"; do
  copy_non_gz_for_path "$backup_path"
done
echo ""
echo "=== 全部完成 ==="
