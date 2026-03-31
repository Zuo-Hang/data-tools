"""
回溯接口调用脚本
调用 POST /api/backstrace，按问卷 ID 回溯数据。
"""

import json
import sys

import requests

# 写死参数
HOST = "10.192.92.75"
PORT = 8080
ACTIVITY_NAME = "ddpage_0iFzJfOV"
FROM_TIME = "2026-02-01 00:00:00"
TO_TIME = "2026-02-01 11:20:00"


def main():
    url = f"http://{HOST}:{PORT}/api/backstrace"
    payload = {
        "activity_name": ACTIVITY_NAME,
        "from": FROM_TIME,
        "to": TO_TIME,
    }
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except requests.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
