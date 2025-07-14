import json
import logging
import os
import time

from bs4 import BeautifulSoup
from flask import current_app
from datetime import datetime
from app.config.config import get_env
from app.service import count_key, success_count_key, fail_list_key, success_list_key, fail_count_key, total_count_key, \
    crawl_list

from app.util.nature_protocol_crawl_util import get_list_last_page, get_page_all_data_list, get_data_from_html, \
    get_all_resource_from_html
from extensions.ext_database import db
from app.models.crawl_data import OriginalDataProtocolIO, ProtocolIoResources, OriginalDataNatureProtocol, \
    NatureProtocolResources

from app.util.download import get_http_data, download_file, download_video, get_http_html
from app.util.oss_util import upload_file, get_file_md5, file_exist
from app.util.protocol_io_util import get_pdf_attrs, get_documents_attrs, get_resource_attrs
from app.util.redis_util import add_to_array, \
    batch_hash_set, get_array
from app.util.text_deal import get_file_extension, compress_html_to_string
from app.util.time_deal import get_timestamp, split_time
import uuid

from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)


def crawl_nature_protocol(task_id, task_setup):
    with current_app.app_context():

        # 2021_01_01 ->2024_08_14
        session = db.session
        time1 = None
        time2 = None
        issue = None
        volume = task_setup['volume']
        if volume:
            issue = task_setup['issue']
        else:
            start_time = task_setup['start_time']
            end_time = task_setup['end_time']
            if not end_time:
                time2 = int(datetime.utcnow().timestamp())
            else:
                time2 = get_timestamp(end_time)
            time1 = get_timestamp(start_time)
        conflict_strategy = task_setup['conflict_strategy']

        # time1_utc = get_utc_timestamp(time1)

        # time2_utc = get_utc_timestamp(time2)
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}', {success_count_key: 0, fail_count_key: 0, total_count_key: 0},
                           360000)

        data = nature_protocol_basic_crawl(session, time1, time2, volume, issue, conflict_strategy, task_id)

    return data


def nature_protocol_basic_crawl(session, time1, time2, volume, issue, conflict_strategy, task_id):
    if not redis_client.exists(f'{crawl_list}{task_id}'):
        if volume:
            list_uri = f'https://www.nature.com/nprot/volumes/{volume}/issues/{issue}'
            str_data = get_http_html(list_uri)
            soup = BeautifulSoup(str_data, 'html.parser')
            title = soup.find('title')
            title = title.get_text()
            if 'Not Found' in title:
                data = {'code': 400,
                        'msg': f" volume not exist or issue not exist"}
                return data
        else:
            if time1 > time2:
                data = {'code': 400,
                        'msg': f" start time is greater than end time"}
                return data

        total_list = get_nature_protocol_total_list(issue, task_id, time1, time2, volume)
        for item in total_list:
            add_to_array(f'{crawl_list}{task_id}', json.dumps(item))
    else:
        total_list = [json.loads(item.decode()) for item in redis_client.lrange(f'{crawl_list}{task_id}', 0, -1)]

    redis_client.hset(f'{count_key}{task_id}', total_count_key, len(total_list))
    success_list = get_array(f'{success_list_key}{task_id}')
    fail_list = get_array(f'{fail_list_key}{task_id}')
    for data in total_list:
        data_doi = str(data['doi'])
        original_data = OriginalDataNatureProtocol.query.filter_by(doi=data_doi).first()
        if original_data:
            if original_data.id in success_list or original_data.id in fail_list:
                continue
            if conflict_strategy == 'skip':
                # redis 执行完一篇文章
                add_to_array(f'{success_list_key}{task_id}', original_data.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                continue
        else:
            original_data = OriginalDataNatureProtocol(
                **data
            )
            original_data.id=str(uuid.uuid4())
            db.session.add(original_data)
            db.session.commit()
            time.sleep(0.1)

        try:

            doi_prefix = data_doi.split('/')[-1]
            url = f'https://www.nature.com/articles/{doi_prefix}'
            str_data = get_http_html(url, task_id)
            logger.info(f'start crawl data , taskId is {task_id},  doi is {data_doi} id is {original_data.id}')
            resource_list = NatureProtocolResources.query.filter_by(doi=data_doi).all()

            resource_list_name = [e.original_path for e in resource_list]

            resource_filter_name_list = get_filter_resource_list_name(resource_list_name)
            original_data = OriginalDataNatureProtocol.query.filter_by(doi=data_doi).first()
            original_data.uri = url
            original_data.content = str_data
            if conflict_strategy == 'update':
                original_data.update_time = datetime.utcnow()

            db.session.commit()
            time.sleep(0.1)

            download_list = get_all_resource_from_html(str_data)

            filter_uri_set = set()
            download_filter_list = []
            for resource in download_list:
                if resource[1] not in filter_uri_set:
                    download_filter_list.append(resource)
                    filter_uri_set.add(resource[1])

            bucket_name = get_env('BUCKET_NAME')
            file_number = 0
            for e in download_filter_list:
                name = e[0]
                uri = e[1]
                description = e[2]
                alt = e[3]
                if uri is None:
                    continue
                if name is None:
                    continue
                if '?' in uri:
                    compare_uri = uri.split('?')[0]
                else:
                    compare_uri = uri
                if compare_uri not in resource_filter_name_list:
                    if name.split('.')[0] not in data_doi:
                        normal_uri = str(uri).split('?')[0]
                        name = normal_uri.split('/')[-1].split('.')[0] + str(
                            file_number) + '.' + normal_uri.split('.')[-1]

                    if 'full' in uri:
                        path_file_folder = './app/static/file/attachments/full/'
                        oss_path = f'literature/nature_protocol/{data_doi}/attachments/full/' + name
                    else:
                        path_file_folder = './app/static/file/'
                        oss_path = f'literature/nature_protocol/{data_doi}/attachments/' + name
                    path = path_file_folder + name
                    type = get_file_extension(name)
                    resource = NatureProtocolResources(original_path=uri, oss_bucket=bucket_name, oss_path=oss_path,
                                                       doi=original_data.doi, resource_type=type, original_name=name,
                                                       description=description)
                    flag = False

                    if ('.mp4' in name or '.MP4' in name or 'avi' in name or '.AVI' in name):
                        path = './app/static/video/' + name
                        os.makedirs(os.path.dirname('./app/static/video/'), exist_ok=True)
                        if path:
                            if download_video(uri, path, task_id=task_id, doi=original_data.doi):
                                flag = True
                                resource.oss_path = oss_path
                    else:
                        os.makedirs(os.path.dirname(path_file_folder), exist_ok=True)
                        if download_file(uri, path, task_id=task_id, doi=original_data.doi):
                            flag = True
                            resource.oss_path = oss_path

                    if path:
                        if flag:
                            # if ('.mp4' in name or '.MP4' in name or 'avi' in name or '.AVI' in name) or upload_file(oss_path, path):
                            if upload_file(oss_path, path):
                                md5 = get_file_md5(oss_path)
                                resource.md5 = md5
                                session.add(resource)
                                file_number = file_number + 1
                                session.commit()
                            os.remove(path)

            add_to_array(f'{success_list_key}{task_id}', original_data.id, 3600)
            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
            time.sleep(1)
        except Exception as e:
            # raise e
            logger.error(f'an error occurred ,which is {str(e)},doi is {data_doi},taskId is {task_id}')
            # raise e

            add_to_array(f'{fail_list_key}{task_id}', original_data.id, 3600)
            redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)

            # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
            # path = LOG_FILE + f'./resource/{task_id}.log'
            # os.makedirs(os.path.dirname(path), exist_ok=True)
            # update_and_save_map(path, get_data)

            # 处理所有类型的异常
            continue
    return {'code': 200,
            'msg': 'success'}


def get_nature_protocol_total_list(issue, task_id, time1, time2, volume):
    total_list = []
    if volume:
        list_uri = f'https://www.nature.com/nprot/volumes/{volume}/issues/{issue}'
        str_data = get_http_html(list_uri, task_id)
        soup = BeautifulSoup(str_data, 'html.parser')
        issue_pic = soup.find('img', attrs={'data-test': 'issue-cover-image'})
        img_uri = issue_pic.attrs['src']
        os.makedirs(os.path.dirname('./app/static/file/'), exist_ok=True)
        year = str(int(volume) + 2005)
        path = f'./app/static/file/{year}-{volume}-{issue}.png'
        oss_path = f'nprot_covers/{year}-{volume}-{issue}.png'
        if not file_exist(oss_path):
            if download_file(img_uri, path, task_id=task_id):
                upload_file(oss_path, path)

        data_list = get_page_all_data_list(soup)
        for data_html in data_list:
            data = get_data_from_html(str(data_html))
            data['issue'] = issue
            data['volume'] = volume

            total_list.append(data)
    else:
        list_uri = 'https://www.nature.com/nprot/articles?page='
        str_data = get_http_html(list_uri + str(1), task_id)
        soup = BeautifulSoup(str_data, 'html.parser')

        last_page = get_list_last_page(soup)
        i = 1
        total_list = []
        flag = True
        # 1.根据时间返回获取这次爬取的所有的protocol列表（多次调用https://www.nature.com/nprot/articles?page=）
        while i <= last_page and flag:
            str_data = get_http_html(list_uri + str(i), task_id)
            soup = BeautifulSoup(str_data, 'html.parser')
            data_list = get_page_all_data_list(soup)

            for data_html in data_list:
                data = get_data_from_html(str(data_html))
                published_on = data['published_on']
                if published_on > time2:
                    continue
                if published_on < time1:
                    flag = False
                    break
                total_list.append(data)
            time.sleep(1)
            i = i + 1
    return total_list


def get_filter_resource_list_name(resource_list_name):
    resource_filter_name_list = []
    for get_resource_original_uri in resource_list_name:
        if '?' in get_resource_original_uri:
            get_resource_original_uri = get_resource_original_uri.split('?')[0]
        else:
            get_resource_original_uri = get_resource_original_uri
        resource_filter_name_list.append(get_resource_original_uri)
    return resource_filter_name_list
