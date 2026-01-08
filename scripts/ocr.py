import json
import logging
import re
import sys
import threading
import uuid
import requests
import time
import base64
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

# 滴滴OCR识别错误改正用字典，需要更多测试补充
from fastapi import HTTPException
from requests import Timeout

CONV_DICT = {'消点宝经济型': '捎点宝经济型', '消点宝出行': '捎点宝出行', '背操出行': '曹操出行', '费操出行': '曹操出行'}
executor = ThreadPoolExecutor(max_workers=30)
lock = threading.Lock()


def cv2_to_base64(images):
    return [base64.b64encode(image).decode('utf-8') for image in images]


def didi_ocr(urls, option=False) -> dict:
    """
    此方法接收url组成的列表
    方法返回处理后的OCR字典列表，元素是每一个url通过滴滴OCR接口传回的字典
    """
    t0 = time.time()
    # logging.info("[didi_ocr]请求图片{}".format(urls[0]))
    images = []
    for url in urls:
        if url is not None:
            response = ocr_get_image_by_url(url)
            if response is not None:
                images.append(response.content)
            else:
                logging.error("[didi_ocr]无法获取图片，url={}".format(url))
    t1 = time.time()
    logging.info("[didi_ocr]请求图片耗时{}".format(t1 - t0))
    images_res = ocr_base_api(images, option)
    t2 = time.time()
    logging.info("[didi_ocr]请求模型耗时{}".format(t2 - t1))
    return images_res


def convert_point(didi_point):
    """
    此方法将滴滴内部OCR接口返回的某一文本转换为AliOcr格式
    传入示例：
    {'confidence': 0.9921839833259583, 'text': '下午3：56', 'text_region': [[538, 7], [704, 10], [703, 53], [537, 50]]}
    传出示例：
    {'h': 37.0, 'text': '下午3:56', 'w': 165.0, 'x': 538.0, 'y': 16.0}
    """
    x = []
    y = []
    for point in didi_point['text_region']:
        x_point, y_point = point
        x.append(x_point)
        y.append(y_point)

    x.sort()
    y.sort()

    w = 0.5 * (x[-1] + x[-2] - x[0] - x[1])
    h = 0.5 * (y[-1] + y[-2] - y[0] - y[1])

    x = 0.5 * (x[0] + x[1])
    y = 0.5 * (y[0] + y[1])

    h = y + h
    w = w + x

    text = didi_point['text']
    confidence = None
    if 'confidence' in didi_point:
        confidence = didi_point['confidence']
    if text in CONV_DICT.keys():
        text = CONV_DICT[text]
    return {'h': h, 'text': text, 'w': w, 'x': x, 'y': y, 'c': round(confidence,3)}



def convert_output(url_list, ali_points_list):
    """
    此方法从ali_points_list（相当于ocrLocations）中提取所有的词汇，生成ocrData
    """
    ocr_data = [','.join([point['text'] for point in line]) for line in ali_points_list]
    ret = dict()
    for i in range(len(url_list)):
        ret[url_list[i]] = (ocr_data[i], ali_points_list[i])
    print(ret)
    return ret


def ocr_base_api(image_file, option=False) -> dict:
    """
    此方法通过滴滴API使用POST获取OCR结果，并以json方式返回
    从示例中修改得来，示例见https://cooper.didichuxing.com/knowledge/2199520887308/2199992074776

    线下测试 URL 为 http://10.196.25.16:8068/predict/ocr_system
    线上使用 URL 为 http://10.82.128.7:17100/predict/ocr_system
    新线上用 URL 为 http://10.66.96.24:16019/predict/ocr_system
    """
    prod_v1 = "http://10.82.128.7:17100/predict/ocr_system"
    prod_v2 = "http://10.66.96.24:16019/predict/ocr_system"
    # 大版本升级，解决历史存在的主要case
    # prod_v3 = "http://10.82.128.7:17165/predict/ocr_system"

    dev_url_v0727 = "http://10.191.36.69:8068/predict/ocr_system"
    dev_v3 = "http://10.196.24.13:8068/predict/ocr_system"

    ocr_system_url = prod_v2
    if 'DEV' == os.getenv("OCR_PROFILE"):
        ocr_system_url = dev_v3

    headers = {"Content-type": "application/json"}
    img = image_file
    # 一个img没拿到就全部gg是否有些离谱，可能要限制每次吞吐量
    if img is None:
        logging.error("[didi_ocr]error in loading image:{}".format(image_file))
        return {}

    # 发送HTTP请求
    start_time = time.time()
    data = {'images': cv2_to_base64(img)}
    try:
        r = requests.post(url=ocr_system_url, headers=headers, data=json.dumps(data))
    except Exception as e:
        logging.error("[didi_ocr]DIDI 解析失败 ||e={}".format(e))
        return dict()
    elapse = time.time() - start_time
    # print('runtime =', elapse)

    return r.json()

def ocr_get_image_by_url(url, timeout_conf=None):
    """
    获取图片，支持URL和本地文件路径
    """
    # 检查是否是本地文件路径
    file_path = Path(url)
    if file_path.exists() and file_path.is_file():
        # 本地文件路径，直接读取
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            # 创建一个类似requests.Response的对象
            class LocalFileResponse:
                def __init__(self, content):
                    self.content = content
            return LocalFileResponse(content)
        except Exception as e:
            logging.error("[didi_ocr]读取本地文件失败，path={}, error={}".format(url, e))
            return None
    
    # URL路径，使用requests获取
    if timeout_conf is None or len(timeout_conf) <= 0:
        # 超时时间，单位秒
        timeout_conf = [5, 10, 15]
    for i, timeout_second in enumerate(timeout_conf):
        try:
            r = requests.get(url=url, timeout=timeout_second)
            r.raise_for_status()  # 检查是否请求成功
            return r  # 如果成功，返回响应
        except Timeout:
            logging.error("[didi_ocr]获取图片超时,次数{},等待时间{},url={}".format(i, timeout_second, url))
            time.sleep(3)
            pass
        except Exception as e:
            logging.error("[didi_ocr]获取图片失败，url={}, error={}".format(url, e))
            break
    logging.error("[didi_ocr]获取图片失败，url={}".format(url))
    return None


class DidiOcrCli:
    def single_scan(self, urls):
        try:
            didi_ret = didi_ocr(urls, False)
            ali_points = [[convert_point(point) for point in line] for line in didi_ret['results']]
            print(json.dumps(ali_points, ensure_ascii=False))
        except Exception as e:
            logging.error("[[didi_ocr]]single_scan err:{}".format(e.__str__()))
            raise e

if __name__ == '__main__':
    urls = set()
    urls.add(
        sys.argv[1]
    )
    os.environ['OCR_PROFILE'] = 'DEV'

    client = DidiOcrCli()
    client.single_scan(list(urls))
