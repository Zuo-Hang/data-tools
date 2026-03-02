#!/usr/bin/env bash
set -euo pipefail

# 待检查的 HDFS 路径列表
HDFS_PATHS=(
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_whs_pas_behavior_2/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_anycar_odt_offline_features/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_sa/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/anycar_LinUCB_feature_extract/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_package_model_passenger_behavior_seq_feature/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_no_pkg_seq_feature/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_no_pkg_seq_feature_v3/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_finish_order_seq_feature/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/popup_window_accept_rate/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_zq_tj_uplift/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_ecr_passenger_features/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_serial_cancel_model_passenger_feature/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_driver_level_feature/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_finish_order_offline_feature/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_crm_passenger_behavior/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_as/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_order_level_v8_passenger/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_dape_driver_minute30_feature_statistics_cheap_d/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_dape_driver_minute30_feature_statistics_fast_d/online_res/data_backup"
  "/user/engine_arch/gizzle_online/offline_schedule_data/auto_hive2ddict_whs_pas_behavior_2/online_res/data_backup"
)

SUMMARY_FILE=$(mktemp)
trap "rm -f ${SUMMARY_FILE}" EXIT

# 脚本执行时的当前目录，文件将下载到此目录
SCRIPT_CWD=$(pwd)

check_path() {
  local HDFS_BASE="$1"
  local TASK_NAME="$2"
  local SUMMARY_FILE="$3"
  local DOWNLOAD_DIR="$4"

  echo "1) 获取目录中最后一个文件..."
  LAST_LINE=$(hdfs dfs -ls "${HDFS_BASE}" | tail -n 1)
  LAST_FILE_PATH=$(echo "${LAST_LINE}" | awk '{print $NF}')
  FILE_NAME=$(basename "${LAST_FILE_PATH}")

  echo "   文件: ${FILE_NAME}"
  echo "   完整路径: ${LAST_FILE_PATH}"

  # 使用任务名做前缀，避免多任务时文件名冲突
  LOCAL_FILE="${DOWNLOAD_DIR}/${TASK_NAME}_${FILE_NAME}"
  DECOMPRESSED="${DOWNLOAD_DIR}/${TASK_NAME}_${FILE_NAME%.gz}"

  echo
  echo "2) 下载 ${FILE_NAME} 到当前执行目录..."
  hdfs dfs -get "${LAST_FILE_PATH}" "${LOCAL_FILE}"
  echo "   本地路径: ${LOCAL_FILE}"

  echo
  echo "3) 解压 ${FILE_NAME} ..."
  gzip -d "${LOCAL_FILE}"
  echo "   本地路径: ${DECOMPRESSED}"

  echo
  echo "4) 查看第 100 行..."
  head -n 100 "${DECOMPRESSED}" | tail -n 1

  echo
  echo "5) 判断是否存在 merge_field..."
  if head -n 100 "${DECOMPRESSED}" | tail -n 1 | grep -q "merge_field"; then
    echo "包含"
    echo "${TASK_NAME}|存在" >> "${SUMMARY_FILE}"
  else
    echo "不包含"
    echo "${TASK_NAME}|不存在" >> "${SUMMARY_FILE}"
  fi

  echo
  echo "6) 删掉中间文件..."
  rm -f "${DECOMPRESSED}"
}

# 批量检查（文件下载到当前执行脚本的目录）
for HDFS_PATH in "${HDFS_PATHS[@]}"; do
  TASK_NAME=$(echo "${HDFS_PATH}" | sed 's|.*/offline_schedule_data/\([^/]*\)/online_res/.*|\1|')
  echo
  echo "========== 正在检查: ${HDFS_PATH} =========="
  if check_path "${HDFS_PATH}" "${TASK_NAME}" "${SUMMARY_FILE}" "${SCRIPT_CWD}"; then
    :
  else
    echo "  检查失败"
    echo "${TASK_NAME}|检查失败" >> "${SUMMARY_FILE}"
  fi
done

echo
echo "========== 检查结果汇总 =========="
printf "%-55s %s\n" "任务名" "merge_field"
printf "%-55s %s\n" "------" "----------"
while IFS='|' read -r task status; do
  printf "%-55s %s\n" "${task}" "${status}"
done < "${SUMMARY_FILE}"

echo
echo "全部完成。"
