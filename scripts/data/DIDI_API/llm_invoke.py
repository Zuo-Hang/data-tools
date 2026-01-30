"""
LLM 调用脚本
调用 POST /api/llm/invoke，发送 prompt 与 image_urls，打印请求与响应及 data 解析结果。
"""

import json
import re
import time
import requests

# 服务地址（IP 与端口通了再调用）
BASE_URL = "http://10.192.92.75:8080"
INVOKE_URL = f"{BASE_URL}/api/llm/invoke"

# 提示词，方便频繁变更
PROMPT = """
你好！你将扮演一个专业的图像数据分析智能体。你的任务是精确地从网约车司机端应用的截图中提取信息，并以指定的JSON格式输出。请严格按照以下步骤和规则进行分析。
请确保你的最终输出是一个严格合法的JSON对象，结构如下。注意返回的字符串是一个json格式，且务必不要包含json字符串内容外的任意字符，保证输出的json格式正确。最终输出的内容格式样例为：

返回的目标json举例：
{
	"activity_name": "阶梯免佣卡",
	"activity_city": "北京市",
	"activity_fence": "平谷区,密云区",
	"discount_rules": {
		"name": "订单按照对应区间政策享受优惠",
		"detail": {
			"1-8单": "减佣10%",
			"9-15单": "减佣18%",
			"16单以上": "免佣"
		}
	},
	"validity_period_start_time": "2025-09-29 00:00:00",
	"validity_period_end_time": "2025-10-08 23:59:59",
	"applicable_time_period": {
		"星期二": "12:00:00 - 23:59:59",
		"星期三": "00:00:00 - 00:59:59, 04:00:00 - 14:59:59"
	},
	"order_timeliness_type": "实时单,预约单,接机单,拼车单",
	"order_categories": "特惠单,经济型",
	"purchase_start_time": "2025-09-29 00:00:00",
	"purchase_end_time": "2025-09-29 23:59:59"
}

第一步：确定信息提取的范围 
第二步：逐行分析页面展示的数据 (生成 目标json的值)
现在，请仔细扫描界面中列出的模块，和其中的列表项，提取信息并根据列表的关键字目标json中。

核心识别规则：
对每行根据页面文字含义，字段的含义在一行的左侧，字段的值在一行的右侧。逐行分析提取以下字段：

activity_name: 固定在开始卡片中的大的文字，文本格式，如"国庆24小时免佣卡"。不存在的话返回Null
activity_city: 在活动规则中的适用城市，需要提取目标城市，文本格式
activity_fence: 在订单要求中以区结尾的所有词语，如"平谷区"、"密云区"、"延庆区"，返回列表。不存在的话返回Null
discount_rules: 这个部分为一个json结构返回，有两个字段"优惠规则"对应name字段、"优惠详情"对应detail字段。不存在即返回Null
validity_period_start_time: 订单要求中的生效时间的开始时间，存在时转化为固定的日期格式，如：2025-09-29 00:00:00。页面不存在返回Null
validity_period_end_time: 订单要求中的生效时间的结束时间，存在时转化为固定的日期格式，如：2025-09-29 23:59:59。页面不存在返回Null
applicable_time_period: 适用时段右侧的时间范围，如：00:00:00~23:59:59 ，可能存在表格形式，这时以json形式返回。页面不存在返回Null
order_timeliness_type: 订单要求中的逗号分隔的实时单、预约单、接机单、拼车单都属于订单时效品类，存在则返回列表，不存在返回Null
order_categories: 订单要求中的逗号分隔的特惠单、经济型、专车等都属于订单品类，存在则返回列表，不存在返回Null
purchase_start_time: 订单要求中的可购买时间开始时间，文本格式。存在时转化为固定的日期格式，如：2025-09-29 00:00:00。页面不存在返回Null
purchase_end_time: 订单要求中的可购买时间结束时间，文本格式。存在时转化为固定的日期格式，如：2025-09-29 23:59:59。页面不存在返回Null

请特别注意：
1、完整性: 确保提取活动模块列表中的所有可选项，不要遗漏任何一个。
输出结构：只需要输出json。

"""


def _parse_data_item(text: str):
    """从 data 项中提取 JSON：支持纯 JSON 或 ```json ... ``` 包裹。"""
    if not text or not text.strip():
        return None
    s = text.strip()
    # 去掉 ```json ... ``` 包裹
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s)
    if m:
        s = m.group(1).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def main() -> None:
    payload = {
        "prompt": PROMPT,
        "image_urls": ["https://s3-gzpu-inter.didistatic.com/sj-ar/ocr_results/活动识别测试case页面/截屏2026-01-27 17.21.14.png"],  # 可改为 ["https://example.com/a.jpg"] 等
    }

    try:
        t0 = time.perf_counter()
        resp = requests.post(
            INVOKE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        elapsed = time.perf_counter() - t0

        print("调用耗时:", f"{elapsed:.2f} 秒")
        print("状态码:", resp.status_code)
        print("响应头:")
        for k, v in resp.headers.items():
            print(f"  {k}: {v}")

        print("\n请求体:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        print("\n响应体:")
        try:
            body = resp.json()
            print(json.dumps(body, ensure_ascii=False, indent=2))

            # 解析并遍历打印 data，提升可读性
            if body.get("code") == 0 and "data" in body:
                data_list = body["data"]
                if data_list:
                    print("\n--- data 解析结果 ---")
                    for i, item in enumerate(data_list):
                        parsed = _parse_data_item(item) if isinstance(item, str) else item
                        print(f"\n  [data[{i}]]")
                        if parsed is not None:
                            print(json.dumps(parsed, ensure_ascii=False, indent=4))
                        else:
                            print(item)
        except json.JSONDecodeError:
            print(resp.text)
    except requests.exceptions.RequestException as e:
        print("请求失败:", e)


if __name__ == "__main__":
    main()
