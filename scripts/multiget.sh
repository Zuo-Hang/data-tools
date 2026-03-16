#!/bin/bash

# 用法: ./multiget.sh <dict> <key>
# 示例: ./multiget.sh my_dict my_key

if [ $# -lt 2 ]; then
    echo "用法: $0 <dict> <key>"
    echo "示例: $0 my_dict my_key"
    exit 1
fi

DICT="$1"
KEY="$2"

echo "=== 请求 colonyType=5 (10.202.164.153) ==="
curl "http://10.202.164.153:8062/dufe/engine/v1/multiget" \
  --data "{\"colonyType\":\"5\", \"type\":\"\", \"query\": {\"rtname\":\"\", \"ver\":1, \"cip\": \"127.0.0.1\", \"combo\": \"gizzle-trigger\", \"keys\":[{\"key\": \"${KEY}\", \"dict\": \"${DICT}\"}]}}"

echo -e "\n"

echo "=== 请求 colonyType=10 (10.141.24.98) ==="
curl "http://10.141.24.98:8062/dufe/engine/v1/multiget" \
  --data "{\"colonyType\":\"10\", \"type\":\"\", \"query\": {\"rtname\":\"\", \"ver\":1, \"cip\": \"127.0.0.1\", \"combo\": \"gizzle-trigger\", \"keys\":[{\"key\": \"${KEY}\", \"dict\": \"${DICT}\"}]}}"

echo -e "\n"
