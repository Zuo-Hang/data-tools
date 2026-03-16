#!/bin/bash

# 按 dict_key_list.csv 每一行作为 multiget.sh 的入参批量执行
# 用法: ./run_multiget_batch.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV_FILE="${SCRIPT_DIR}/data1/dict_key_list.csv"
MULTIGET_SCRIPT="${SCRIPT_DIR}/multiget.sh"

if [ ! -f "$CSV_FILE" ]; then
    echo "错误: CSV 文件不存在 $CSV_FILE"
    exit 1
fi

if [ ! -x "$MULTIGET_SCRIPT" ]; then
    echo "错误: multiget.sh 不存在或不可执行 $MULTIGET_SCRIPT"
    exit 1
fi

line_num=0
while IFS= read -r line; do
    line_num=$((line_num + 1))
    [ $line_num -eq 1 ] && continue  # 跳过表头

    [ -z "$line" ] && continue

    # 解析 CSV: "dict","key"
    dict=$(echo "$line" | sed 's/^"//;s/",".*//')
    key=$(echo "$line" | sed 's/.*","//;s/"$//')

    echo "========== 第 $((line_num - 1)) 条: dict=$dict key=$key =========="
    "$MULTIGET_SCRIPT" "$dict" "$key"
done < "$CSV_FILE"

echo "========== 全部执行完成 =========="
