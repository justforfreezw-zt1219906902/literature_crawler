import logging
import os

from dotenv import load_dotenv
from oss2.credentials import EnvironmentVariableCredentialsProvider

import oss2

from app.config.config import get_env

load_dotenv()


OSS_ACCESS_KEY_ID=os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET=os.getenv('OSS_ACCESS_KEY_SECRET')

logger = logging.getLogger('oss_util')


def upload_file(object_name,file_path):
    auth = get_auth()

    # 假设config.ini位于脚本同级目录下

    BUCKET_NAME = get_env('BUCKET_NAME')
    END_POINT = get_env('END_POINT')
    # 填写Bucket所在地域对应的END_POINT。以华东1（杭州）为例，END_POINT填写为https://oss-cn-hangzhou.aliyuncs.com。
    # yourBUCKET_NAME填写存储空间名称。
    bucket = oss2.Bucket(auth, END_POINT, BUCKET_NAME)

    # 上传文件到OSS。
    # yourObjectName由包含文件后缀，不包含Bucket名称组成的Object完整路径，例如abc/efg/123.jpg。
    # yourLocalFile由本地文件路径加文件名包括后缀组成，例如/users/local/myfile.txt。
    return bucket.put_object_from_file(object_name, file_path) is not None


def file_exist(object_name):
    auth = get_auth()
    # 填写Bucket所在地域对应的END_POINT。以华东1（杭州）为例，END_POINT填写为https://oss-cn-hangzhou.aliyuncs.com。
    # yourBUCKET_NAME填写存储空间名称。

    # 假设config.ini位于脚本同级目录下

    BUCKET_NAME = get_env('BUCKET_NAME')
    END_POINT = get_env('END_POINT')
    bucket = oss2.Bucket(auth, END_POINT, BUCKET_NAME)

    # 填写Object的完整路径，Object完整路径中不能包含Bucket名称。
    exist = bucket.object_exists(object_name)
    # 返回值为true表示文件存在，false表示文件不存在。
    return exist


def get_file_md5(object_key):
    # 初始化Bucket对象
    # 假设config.ini位于脚本同级目录下
    access_key_id = get_env('OSS_ACCESS_KEY_ID')
    access_key_secret = get_env('OSS_ACCESS_KEY_SECRET')
    auth = oss2.Auth(access_key_id, access_key_secret)
    # auth = get_auth()
    BUCKET_NAME = get_env('BUCKET_NAME')
    END_POINT = get_env('END_POINT')
    bucket = oss2.Bucket(auth, END_POINT, BUCKET_NAME)

    # 获取文件的元数据

    object_meta = bucket.head_object(object_key)

    # 获取Content-MD5值
    # content_md5 = object_meta.headers.get('Content-MD5')
    Etag = object_meta.etag
    return Etag






def get_auth():
    # 读取配置文件
    
    # 假设config.ini位于脚本同级目录下

    # 从配置文件中获取Access Key ID和Access Key Secret
    # access_key_id = config.get('configName', 'ALIBABA_CLOUD_ACCESS_KEY_ID')
    #
    # access_key_secret = config.get('configName', 'ALIBABA_CLOUD_ACCESS_KEY_SECRET')

    # access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
    # BUCKET_NAME = os.getenv('BUCKET_NAME')
    # REDIS_HOST = os.getenv('REDIS_HOST')
    # access_key_secret =  os.getenv('OSS_ACCESS_KEY_SECRET')

    # 使用获取的RAM用户的访问密钥配置访问凭证
    # auth = oss2.AuthV4(access_key_id, access_key_secret)
    auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
    return auth


def get_default_bucket():
    access_key_id = get_env('OSS_ACCESS_KEY_ID')
    access_key_secret = get_env('OSS_ACCESS_KEY_SECRET')
    auth = oss2.Auth(access_key_id, access_key_secret)
    BUCKET_NAME = get_env('BUCKET_NAME')
    END_POINT = get_env('END_POINT')
    bucket = oss2.Bucket(auth, END_POINT, BUCKET_NAME)
    return bucket
