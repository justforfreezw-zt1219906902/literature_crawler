import logging
import math
from datetime import datetime,timedelta

import pytz

logger=logging.getLogger(__name__)
def get_timestamp(date_string):
    date_format = "%Y_%m_%d"
    # 将字符串转换为datetime对象
    date_object = datetime.strptime(date_string, date_format)
    # 转换为时间戳
    timestamp = date_object.timestamp()

    return int(timestamp)

def get_timestamp2(date_string):
    date_format = "%Y-%m-%d"
    # 将字符串转换为datetime对象
    date_object = datetime.strptime(date_string, date_format)
    # 转换为时间戳
    timestamp = date_object.timestamp()

    return int(timestamp)

def get_utc_timestamp(timestamp):



    return timestamp-3600*8


print(get_timestamp("2024_09_23"))
logger.info(get_utc_timestamp(1727020800))


def split_time(start_timestamp, end_timestamp):
    delta_days = (datetime.fromtimestamp(end_timestamp) - datetime.fromtimestamp(start_timestamp)).days


    timestamps=[]
    # 按照10天的间隔来划分
    for i in range(0, math.ceil(delta_days/10)+1):

        # 计算当前时间
        current_date = datetime.fromtimestamp(start_timestamp) + timedelta(days=i)*10
        # 添加时间戳到列表

        if current_date.timestamp() > end_timestamp:
            timestamps.append(end_timestamp)
        else:
            timestamps.append(int(current_date.timestamp()))



    return timestamps;


def timestamp_format(timestamp):
    # 将时间戳转换为 datetime 对象
    dt_object = datetime.fromtimestamp(timestamp)

    # 将 datetime 对象格式化为字符串
    formatted_time = dt_object.strftime("%d %B %Y")
    return formatted_time


def timestamp_year(timestamp):
    # 将时间戳转换为 datetime 对象
    dt_object = datetime.fromtimestamp(int(timestamp))


    return dt_object.year


# time1=get_timestamp("2023_01_02")

# time2=get_timestamp("2023_02_02")
