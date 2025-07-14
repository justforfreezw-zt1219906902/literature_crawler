import logging
import socket
import time
from datetime import datetime
from urllib.request import urlopen

import requests

from tqdm import tqdm

from app.util.text_deal import read_strings_from_file, write_strings_to_file
from app.util.url_util import is_download

logger=logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
}


def get_http_data(url, headers=headers,task_id=None,doi=None,protocol_id=None):
    max_retries=3
    timeout=100
    delay=2
    for attempt in range(max_retries + 1):
        try:
            res = requests.get(url, headers=headers,timeout=timeout)

            res.raise_for_status()  # 检查HTTP响应状态
        except Exception as e:
            if attempt == max_retries:
                return None
            else:
                logger.error(
                    f' connect fail: {url} ,redownlaod ({attempt + 1}/{max_retries})：{e},task_id:{task_id},doi:{doi},protocol_id:{protocol_id}')
            time.sleep(delay)

    if res.status_code == 200:
        content = res.content
        str_data = content.decode('utf-8')
    elif res.status_code == 403:
        return
    return str_data

def get_http_html(url,task_id=None):
    max_retries = 5
    timeout = 50
    delay = 2
    logger.info(f'start to crawl {url}')
    for attempt in range(max_retries + 1):
        try:
            res = requests.get(url,headers=headers,timeout=timeout)

            res.raise_for_status()  # 检查HTTP响应状态
        except Exception as e:
            if attempt == max_retries:
                logger.error(
                    f' connect fail: {url} ,max attempt')
                return None
            else:
                logger.error(
                    f' connect fail: {url} ,reconnect ({attempt + 1}/{max_retries})：{e}')
            time.sleep(delay)

    if res.status_code == 200:
        content = res.text
        str_data = content
    elif res.status_code == 403:
        logger.error(f' request url :{url} ,which code is 403,,task_id:{task_id}')
    elif res.status_code == 404:
        content = res.text
        str_data = content
    return str_data
def download_video(url,path,task_id=None,doi=None,protocol_id=None):
    if not is_download(url):
        logger.error(
            "ERROR, something went wrong" + f'can not download {url} ,task_id:{task_id},doi:{doi},protocol_id:{protocol_id}')
        return False
    logger.info(f'start to download video url: {url} ,,task_id:{task_id},doi:{doi},protocol_id:{protocol_id}')
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(path, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            logger.error("ERROR, something went wrong "+f'download {url} fail,task_id:{task_id},doi:{doi},protocol_id:{protocol_id}')
            return False
        return True
    else:
        logger.error(f'download request url :{url} ,which code is 403,,task_id:{task_id},doi:{doi},protocol_id:{protocol_id}')
        return False


def download_file(url, path,task_id=None,doi=None,protocol_id=None):
    max_retries = 3
    delay = 0.2
    timeout=60
    chunk_size = 21920  # 每次读取8KB的数据
    if not is_download(url):
        logger.error(
            "ERROR, something went wrong" + f' can not download {url} ,task_id:{task_id},doi:{doi},protocol_id:{protocol_id}')
        return False
    logger.info(f'start to download non-video url: {url} ,task_id:{task_id},doi:{doi},protocol_id:{protocol_id}')

    for attempt in range(max_retries + 1):
        for attempt in range(max_retries + 1):
            try:
                # 开始记录时间
                response = requests.get(url, stream=True, timeout=timeout)

                if response.status_code == 200:
                    with open(path, 'wb') as out_file:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                out_file.write(chunk)
                    return True

                else:
                    logger.error(
                        f"download fail: {response.status_code}, URL: {url}, task_id: {task_id}, doi: {doi}, protocol_id: {protocol_id}")
                    return False

            except Exception as e:
                # raise e
                if attempt == max_retries:
                    logger.error(f"download {url} error: {e}, task_id: {task_id}, doi: {doi}, protocol_id: {protocol_id}.")
                    logger.error(
                        f"download non-video URL: {url}, all three attempts all fail, task_id: {task_id}, doi: {doi}, protocol_id: {protocol_id}.")
                    return False
                else:
                    logger.error(
                        f"download fail: {url}, redownload ({attempt + 1}/{max_retries}): {e}, task_id: {task_id}, doi: {doi}, protocol_id: {protocol_id}.")
                    time.sleep(delay)
                continue


    return True


