"""
MQ 发送脚本
调用 POST /api/mq/send，发送 topic 与 content，打印请求与响应。
"""

import json
import time
import requests

# 服务地址
BASE_URL = "http://10.192.92.75:8080"
SEND_URL = f"{BASE_URL}/api/mq/send"

# 入参，方便频繁变更
TOPIC = "ocr_backstrace"
CONTENT = '{"orderId":"123","type":"backstrace"}'  # JSON 字符串，整段作为 MQ 消息体


def main() -> None:
    payload = {
        "topic": TOPIC,
        "content": CONTENT,
    }

    try:
        t0 = time.perf_counter()
        resp = requests.post(
            SEND_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        elapsed = time.perf_counter() - t0

        print("调用耗时:", f"{elapsed:.2f} 秒")
        print("状态码:", resp.status_code)
        print("请求体:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        print("\n响应体:")
        try:
            body = resp.json()
            print(json.dumps(body, ensure_ascii=False, indent=2))
            code = body.get("code")
            msg = body.get("msg", "")
            if code == 0:
                print("\n--- 发送成功 ---")
            else:
                print(f"\n--- 发送失败 --- code: {code}, msg: {msg}")
        except json.JSONDecodeError:
            print(resp.text)
    except requests.exceptions.RequestException as e:
        print("请求失败:", e)


if __name__ == "__main__":
    main()
