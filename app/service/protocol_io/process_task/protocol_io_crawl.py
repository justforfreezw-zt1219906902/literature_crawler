import json
import logging
import os
import time

from flask import current_app
from datetime import datetime
from app.config.config import get_env
from app.service import success_count_key, count_key, fail_count_key, total_count_key, success_list_key, fail_list_key, \
    crawl_list

from extensions.ext_database import db
from app.models.crawl_data import OriginalDataProtocolIO, ProtocolIoResources

from app.util.download import get_http_data, download_file, download_video
from app.util.oss_util import upload_file
from app.util.protocol_io_util import get_pdf_attrs, get_documents_attrs, get_resource_attrs
from app.util.redis_util import add_to_array, \
    batch_hash_set, get_array
from app.util.text_deal import get_file_extension
from app.util.time_deal import get_timestamp, split_time
import uuid

from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)


def crawl_protocol_io(task_id, task_setup):
    with current_app.app_context():

        # 2021_01_01 ->2024_08_14
        session = db.session

        start_time = task_setup['start_time']
        end_time = task_setup['end_time']
        conflict_strategy = task_setup['conflict_strategy']
        time1 = get_timestamp(start_time)
        # time1_utc = get_utc_timestamp(time1)
        time2 = get_timestamp(end_time)
        # time2_utc = get_utc_timestamp(time2)
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}', {success_count_key: 0, fail_count_key: 0, total_count_key: 0}, 3600)
        if time2 > time1:
            protocol_io_basic_crawl(session, time1, time2, conflict_strategy, task_id)

    return 'ok'


def protocol_io_basic_crawl(session, time1, time2, conflict_strategy, task_id):
    headers = {
        'Authorization': 'Bearer c19e9ae63e04417bb6c5525d74ce59c59b0e6afc5cb32ccc10f3f58a358e8bc98938122d0edb5679d2f17867482653c9ccd6051fc3c2c6fae4ab0361703205c0'}
    if not redis_client.exists(f'{crawl_list}{task_id}'):
        time_list = split_time(time1, time2)
        api_times = len(time_list)

        i = 0
        list = []
        total_list = []
        # 1.根据时间返回获取这次爬取的所有的protocol列表（多次调用https://www.protocols.io/api/v3/publications?from=1571097600&to=1571961600）

        while i < api_times - 1:
            url = f'https://www.protocols.io/api/v3/publications?from={time_list[i]}&to={time_list[i + 1]}'
            str_data = get_http_data(url, headers)
            result = []
            # 将字符串解析为 dict
            dict_data = json.loads(str_data)

            id_list = [dict(e)['id'] for e in dict_data['items']]
            list.__iadd__(id_list)
            # 遍历每个字典
            for item in dict_data['items']:
                # 检查 alias 是否为空
                if item.get('doi'):  # 如果 alias 不为空或 None
                    result.append(item['doi'])
                else:  # 如果 alias 为空或 None
                    result.append(item['id'])
            total_list.__iadd__(result)
            # total_doi_list.__iadd__(all_doi_list)
            time.sleep(3)
            i = i + 1

        list.reverse()
        for e in list:
            add_to_array(f'{crawl_list}{task_id}', str(e),3600)

    else:
        list = get_array(f'{crawl_list}{task_id}')

    # 初始化redis

    redis_client.hset(f'{count_key}{task_id}', total_count_key, len(list))

    success_list = get_array(f'{success_list_key}{task_id}')
    fail_list = get_array(f'{fail_list_key}{task_id}')

    for e in list:
        protocol_id = str(e)

        original_data = OriginalDataProtocolIO.query.filter_by(protocol_id=protocol_id).first()
        if original_data:
            if original_data.id in success_list or original_data.id in fail_list:
                continue
            if conflict_strategy == 'skip':
                # redis 执行完一篇文章
                add_to_array(f'{success_list_key}{task_id}', original_data.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                continue
        else:
            original_data = OriginalDataProtocolIO(
                protocol_id=protocol_id
            )
            original_data.id = str(uuid.uuid4())
            db.session.add(original_data)
            db.session.commit()
            time.sleep(0.1)
        try:

            original_data = OriginalDataProtocolIO.query.filter_by(protocol_id=protocol_id).first()

            url = f'https://www.protocols.io/api/v4/protocols/{protocol_id}'
            str_data = get_http_data(url, headers)
            # 将字符串解析为 dict
            dict_data = json.loads(str_data)

            # materials = json.loads(dict_data['payload']['materials_text'])
            get_data = dict_data['payload']
            doi = get_data['doi']
            # del get_data['funders']

            # 暂时处理doi为空就不入库
            if not doi:
                add_to_array(f'{fail_list_key}{task_id}', original_data.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)

                logger.error(
                    f'an error occurred ,which is doi not exist,protocol_id is {protocol_id},taskId is {task_id}')
                continue

            get_doi = str(doi).split('doi.org/')[1]
            logger.info(f'start crawl data , taskId is {task_id},  protocol_id is {protocol_id},doi is {get_doi}  id is {original_data.id} ')
            resource_list = ProtocolIoResources.query.filter_by(doi=get_doi).all()

            resource_list_name = [e.original_path for e in resource_list]

            resource_filter_name_list = get_filter_resource_list_name(resource_list_name)

            steps = get_data['steps']
            documents = get_data['documents']

            get_data['doi'] = get_doi
            # 如果为空 则是插入 否则就是更新
            for key, value in get_data.items():
                if key == 'id':
                    continue
                setattr(original_data, key, value)
            original_data.protocol_id = protocol_id

            if conflict_strategy == 'update':
                original_data.update_time = datetime.utcnow()

            db.session.commit()
            doi_split_list = str(original_data.doi).split('/')
            doi_split = doi_split_list[1]

            downlaod_list = []

            if documents:
                for documents in documents:
                    data = get_documents_attrs(documents)
                    downlaod_list.append(data)
            if len(doi_split_list) > 2:
                pdf_data = get_pdf_attrs(e, doi_split + '_' + doi_split_list[2])
            else:
                pdf_data = get_pdf_attrs(e, doi_split)
            downlaod_list.append(pdf_data)
            if steps:
                for step in steps:
                    if step['step']:
                        step_json = json.loads(step['step'])
                        step_json_dict = dict(step_json)
                        map_dict = dict(step_json_dict['entityMap'])
                        map_values = map_dict.values()
                        for map_value in map_values:
                            map_entity = dict(map_value)
                            if map_entity['mutability'] == 'IMMUTABLE' and map_entity['type'] != 'image' and \
                                    map_entity[
                                        'type'] != 'video':
                                # 还有获取下一级别的资源 如果是iamge video类型则没有下一级别资源
                                map_data = map_entity['data']
                                step_json_dict = dict(map_data)
                                if 'entityMap' in step_json_dict.keys():
                                    step_json_dict = step_json_dict.get('entityMap', {})
                                    if step_json_dict:
                                        map_dict = dict(step_json_dict)
                                        map_values = map_dict.values()
                                        for map_value in map_values:
                                            next_map_value = dict(map_value)
                                            data = get_resource_attrs(next_map_value, doi)
                                            if data[1]:
                                                downlaod_list.append(data)

                            else:
                                data = get_resource_attrs(map_entity, doi)
                                if data[1]:
                                    downlaod_list.append(data)

            bucket_name = get_env('BUCKET_NAME')
            file_number = 0
            for e in downlaod_list:
                name = e[0]
                uri = e[1]
                if uri is None:
                    continue
                if name is None:
                    continue
                if '?' in uri:
                    compare_uri = uri.split('?')[0]
                else:
                    compare_uri = uri
                if compare_uri not in resource_filter_name_list:
                    if name.split('.')[0] not in doi:
                        normal_uri = str(uri).split('?')[0]
                        name = normal_uri.split('/')[-1].split('.')[0] + str(
                            file_number) + '.' + normal_uri.split('.')[-1]
                    path = './app/static/file/' + name
                    oss_path = f'literature_test/protocol_io_true/{doi_split}/' + name
                    type = get_file_extension(name)
                    resource = ProtocolIoResources(original_path=uri, oss_bucket=bucket_name, oss_path=oss_path,
                                                   doi=original_data.doi, resource_type=type)
                    flag = False

                    if ('.mp4' in name or '.MP4' in name or 'avi' in name or '.AVI' in name):
                        path = './app/static/video/' + name
                        os.makedirs(os.path.dirname('./app/static/video/'), exist_ok=True)
                        if path:
                            if download_video(uri, path, task_id=task_id, doi=original_data.doi,
                                              protocol_id=protocol_id):
                                flag = True
                                resource.oss_path = oss_path
                    else:
                        os.makedirs(os.path.dirname('./app/static/file/'), exist_ok=True)
                        if download_file(uri, path, task_id=task_id, doi=original_data.doi, protocol_id=protocol_id):
                            flag = True
                            resource.oss_path = oss_path

                    if path:
                        if flag:
                            # if ('.mp4' in name or '.MP4' in name or 'avi' in name or '.AVI' in name) or upload_file(oss_path, path):
                            if upload_file(oss_path, path):
                                session.add(resource)
                                file_number = file_number + 1
                                session.commit()
                            os.remove(path)

            add_to_array(f'{success_list_key}{task_id}', original_data.id, 3600)
            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)


        except Exception as e:

            add_to_array(f'{fail_list_key}{task_id}',  original_data.id, 3600)
            redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)

            # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
            # path = LOG_FILE + f'./resource/{task_id}.log'
            # os.makedirs(os.path.dirname(path), exist_ok=True)
            # update_and_save_map(path, get_data)
            logger.error(f'an error occurred ,which is {str(e)},protocol_id is {protocol_id},taskId is {task_id}')
            # 处理所有类型的异常
            continue


def get_filter_resource_list_name(resource_list_name):
    resource_filter_name_list = []
    for get_resource_original_uri in resource_list_name:
        if '?' in get_resource_original_uri:
            get_resource_original_uri = get_resource_original_uri.split('?')[0]
        else:
            get_resource_original_uri = get_resource_original_uri
        resource_filter_name_list.append(get_resource_original_uri)
    return resource_filter_name_list
