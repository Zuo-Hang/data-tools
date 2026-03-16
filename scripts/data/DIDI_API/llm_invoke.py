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

# 提示词，方便频繁变更（勿用 f-string，内容含 {} 会报错）
PROMPT = """
你好！你将扮演一个专业的图像数据分析智能体。你的任务是精确地从网约车应用的截图中提取行程和价格信息，并以指定的JSON格式输出。请严格按照以下步骤和规则进行分析。
请确保你的最终输出是一个严格合法的JSON对象，结构如下。注意返回的字符串是一个json的数组格式，且务必不要包含json字符串内容外的任意字符，保证输出的json格式正确。最终输出的内容格式样例为：

{
    "start_point": "山东现代学院(北门)",
    "end_point": "马西村委会",
    "order_estimated_distance": "21.8",
    "order_estimated_time": "33",
    "creation_time": "2025-06-10 17:15:50",
    "vehicles": [
    {  
      "supplier": "顺风车",
      "price": "18.37",
      "price_type": "一口价",
      "discount_type": "优惠已减6元",
      "discount_amount": "6",
      "extra_price": ""
    },
    {
      "supplier": "极速拼车",
      "price": "35.5/48-59",
      "price_type": "一口价",
      "discount_type": "拼成省16.9元",
      "discount_amount": "16.9",
      "extra_price": "2.30"
    },
    {
        "supplier": "特惠快车",
        "price": "34.1",
        "price_type": "一口价",
        "discount_type": "优惠8.52元",
        "discount_amount": "8.52",
        "extra_price": "2"
    },
    {
        "supplier": "有象约车",
        "price": "46",
        "price_type": "预估",
        "discount_type": "特惠 已优惠5元",
        "discount_amount": "5",
        "extra_price": "2.30"
    },
    {
        "supplier": "老兵打车",
        "price": "46",
        "price_type": "预估",
        "discount_type": "特惠 已优惠2元",
        "discount_amount": "2",
        "extra_price": "3.30"
    },
    {
        "supplier": "及时用车",
        "price": "49",
        "price_type": "预估",
        "discount_type": "特惠 已优惠5元",
        "discount_amount": "5",
        "extra_price": "0.5"
    }
  ]
}

分析步骤与规则

第一步：分析全局行程信息 (生成 json对象的关键字段)

如果图片包含地图视图，请从地图区域提取以下全局信息。如果图片不含地图，则将对应值留空字符串 ""。
start_point (起点): 路线的起点(起点是路线一端的绿色圆点)，如果起点在地图页面上，记录为起点位置,如果图中没有标注，则填写为""。
end_point (终点): 路线的终点(终点是路线一端的橙色圆点)，如果终点在地图页面上，记录终点位置，如果图中没有标注，则填写为""。
order_estimated_distance (预估里程):注意仅在有地图的图片上识别该字段。在推荐路线上找到里程数。以"|"为分隔符，固定格式是 “X公里|Y分钟”，提取X；注意，不要将分隔符‘|’识别为数字1;
order_estimated_time (订单预估时间): 
1.在地图页面提取，通常以“分钟”为单位。固定格式是 “X公里|Y分钟”，提取Y；注意，不要将竖线(‘|’)识别为 '1'。比如，4.3公里|7分钟，提取"7",不是"17"。注意，忽略”已选车型应答约Z秒“信息，不要将Z填入order_estimated_time，填写"";
2.如果没有识别到order_estimated_distance (预估里程)，默认填写order_estimated_time为“”;
creation_time (截图时间): 提取图片中明确标注的日期和时间，格式化为 YYYY-MM-DD HH:MM:SS。



第二步：逐行分析车辆选项 (生成 vehicle 数组)

现在，请仔细扫描界面中列出的每一个可供选择的打车服务。对于每一个可选项，提取一组信息并作为一个对象添加到 vehicle 数组中。

核心识别规则：
识别可选项 vs 分组标签:
可选项 (行项目) 是用户可以直接选择并看到价格的条目。它们通常包含一个图标/Logo、一个服务名称 (大号黑体字) 和一个价格。例如：“顺风车”、“极速拼车”、“特惠快车”、“有象约车”。
分组标签 (侧边栏) 是位于最左侧、用于分类的小字，例如“特惠”、“顺风车”、“经济”、“特快”、“轻享”、“出租车”。这些是类别，绝不是服务名称，请务必忽略它们！
对每个可选项，提取以下字段：

supplier (供应商名称):
提取该行项目中最主要的、大号加粗的黑色字体。这代表了供应商或服务类型。
重要：再次确认，这绝不是左侧边栏的灰色分类标签。例如，在“经济”这个分组下，supplier应该是“有象约车”、“老兵打车”等，而不是“经济”。

price (价格):
提取服务名称右侧的大号加粗价格数字。
单一价格: 如 34.1元，提取 34.1。
价格范围: 如 48.05-59.1元，提取 48.05-59.1。
拼车价格: 对于“极速拼车”这类服务，通常会显示两个价格。请按 “拼成价/未拼成价” 的格式记录。例如，如果显示“拼成 35.5元”和“未拼成 48-59元”，则记录为 35.5/48-59。

price_type (价格类型):
检查价格附近是否有“预估”、“约”等字样。如果有，则为 "预估价"。
如果价格附近有“一口价”字样，或没有任何标识（对于固定价格的服务），则默认为 "一口价"。

discount_type (优惠描述):
查找价格下方或附近的小号、通常为灰色或红色的文字。完整记录描述性文本。不存在的话填写为""。
例如：“已优惠¥6”、“最高优惠¥10”。
如果没有，则留空字符串 ""。

discount_amount (优惠金额):
从 discount_type 中提取纯数字。
例如，从“优惠已减6元”中提取 6，从“拼成省16.9元”中提取 16.9。
如果没有优惠金额，则记录 0。

extra_price (额外费用):
提取价格附近可能存在的额外费用信息，例如“含燃油费”、“含保险费”等。如果有，则提取对应金额；
例如：从“含节假日服务费2.0元” 中提取的2.0元
如果没有，则留空字符串 ""。

请特别注意：
完整性: 确保提取了列表中的所有可选项，不要遗漏任何一个。
底部价格栏: 忽略屏幕最下方蓝色按钮上方的总预估价（如 "预估 34.1元起"），它只是一个参考，不代表任何一个具体服务。
如果order_estimated_time (订单预估时间)单位为小时，请转换为分钟为单位；
如果order_estimated_distance (预估里程)单位为米，请转换为公里为单位；
如果路线的起终点在地图上，start_point、end_point记录为"";
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
        "image_urls": ["https://s3-gzpu-inter.didistatic.com/sj-ar/ocr_results/冒泡测试case页面/TX/Screenshot_20260306_171959_com.hy.clone.jpg"],
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
