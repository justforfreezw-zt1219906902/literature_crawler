import logging
import os
import time

from bs4 import BeautifulSoup
from flask import current_app
from sqlalchemy import and_

from app.config.config import get_env
from app.service import count_key, success_count_key, fail_count_key, total_count_key, success_list_key, fail_list_key
from app.util.migrate_util import connect

from extensions.ext_database import db
from app.models.clean_data import IOData
from app.models.crawl_data import OriginalDataProtocolIO, ProtocolIoResources

from app.util.protocol_io_util import clean_author_list, \
    clean_ref_list, clean_relate_list, get_content_from_steps, get_abstartct
from app.util.redis_util import add_to_array, batch_hash_set, get_array
from app.util.text_deal import read_strings_from_file, write_strings_to_file
from app.util.time_deal import get_timestamp, timestamp_format, get_utc_timestamp
from datetime import datetime

from extensions.ext_redis import redis_client

global protocol_io_clean

logger = logging.getLogger(__name__)


def clean_protocol_io(task_id,task_setup):
    with current_app.app_context():

        session = db.session

        conflict_strategy = task_setup['conflict_strategy']
        start_time = task_setup['start_time']
        end_time = task_setup['end_time']
        id_list = task_setup['id_list']

        if start_time:
            if not end_time:
                time2 = int(datetime.utcnow().timestamp())
            else:
                time2 = get_timestamp(end_time)
            time1 = get_timestamp(start_time)
            # time1_utc = get_utc_timestamp(time1)
            # time2_utc = get_utc_timestamp(time2)
            data_list = db.session.query(OriginalDataProtocolIO.id).filter(and_(
                OriginalDataProtocolIO.published_on >= time1, OriginalDataProtocolIO.published_on < time2)).all()
            id_list = [data[0] for data in data_list ]
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}',{success_count_key:0,fail_count_key:0,total_count_key:0},3600)
        # list = db.session.query(OriginalDataProtocolIO).filter(and_(
        #     OriginalDataProtocolIO.published_on >= time1, OriginalDataProtocolIO.published_on <= time2)).all()

        # 获取总记录数
        page_size=100
        query=session.query(OriginalDataProtocolIO).filter(and_(
            OriginalDataProtocolIO.doi.in_(id_list)
        ))
        total_records = (
            query
            .count()
        )
        # 初始化redis
        redis_client.hset(f'{count_key}{task_id}', total_count_key, total_records)


        logger.info(f'task_id is {task_id},the length of clean list is {total_records}')
        # 计算总页数
        total_pages = (total_records + page_size - 1) // page_size
        index = 1
        skip_index = 0
        success_list = get_array(f'{success_list_key}{task_id}')
        fail_list = get_array(f'{fail_list_key}{task_id}')
        # 循环处理所有页数
        for page_number in range(1, total_pages + 1):
            offset = (page_number - 1) * page_size

            # 分页查询
            query = (
                query
                .offset(offset)
                .limit(page_size)
            )

            # 获取分页结果
            results = query.all()

            # 处理分页结果
            for original_data in results:
                if original_data.id in success_list or original_data.id in fail_list:
                    continue
                try:

                    get_cleandata = IOData.query.filter_by(id=original_data.id).first()
                    # 如果是更新的逻辑
                    if conflict_strategy == 'skip' and get_cleandata:

                        skip_index = skip_index + 1
                        add_to_array(f'{success_list_key}{task_id}', get_cleandata.id, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', success_count_key)

                        continue
                    else:

                        doi = original_data.doi

                        strat_info = f'taskid is {task_id} index is {index} :start to clean protocol_id is {original_data.protocol_id},doi is {original_data.doi}'
                        logger.info(strat_info)

                        publish_date = timestamp_format(original_data.published_on)
                        if original_data.keywords:
                            keywords = original_data.keywords
                            keywords = keywords.split(',')
                        else:
                            keywords = []
                        deal_keywords = []
                        for keyword in keywords:
                            deal_keywords.append(str(keyword).strip())

                        resources = ProtocolIoResources.query.filter_by(doi=original_data.doi).all()

                        # 这里需要使用正则表达式提取各种信息
                        ref_list = clean_ref_list(original_data)
                        # ref_list = [json.dumps(tmp, ensure_ascii=False) for tmp in ref_list]

                        author_list = clean_author_list(original_data)
                        # author_list = [json.dumps(tmp, ensure_ascii=False) for tmp in author_list]

                        relate_list = clean_relate_list(original_data)
                        # relate_list = [json.dumps(tmp, ensure_ascii=False) for tmp in relate_list]

                        units = original_data.units

                        steps = original_data.steps
                        if steps:
                            # 排序列表
                            try:
                                steps = [step for step in steps if step['number']]
                                steps = sorted(steps, key=lambda x: float(x["number"]))
                                for step in steps:
                                    if step['cases']:
                                        logger.error(
                                            f'this literature has cases,doi is {doi} , taskId is {task_id}')
                            except Exception as e:

                                add_to_array(f'{fail_list_key}{task_id}', original_data.id, 3600)
                                redis_client.incr(f'{count_key}{task_id}', fail_count_key)

                                # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                                # path = LOG_FILE + f'./resource/{task_id}.log'
                                # os.makedirs(os.path.dirname(path), exist_ok=True)
                                # update_and_save_map(path, get_data)
                                logger.error(
                                    f'an error occurred,which is no number error,doi is {doi} , taskId is {task_id}')
                                # 处理所有类型的异常

                                continue
                        content = get_content_from_steps(original_data, units, resources, doi)

                        abstract = get_abstartct(original_data, units, resources, doi)
                        io_data = IOData(
                            doi=original_data.doi,
                            title=original_data.title,
                            publish_date=publish_date,
                            keywords=deal_keywords,
                            content=content,
                            abstract_text=abstract,
                            reference=ref_list,
                            relates=relate_list,
                            author_list=author_list,
                            id=original_data.id
                        )
                        conn = connect()
                        with conn.cursor() as cur:
                            DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
                            cur.execute(f"SET search_path TO {DB_SCHEMA};")
                            figures = get_figure_list_to_clean_data(cur, get_cleandata.doi)

                        conn.close()
                        if conflict_strategy == 'update' and get_cleandata:
                            get_cleandata.figures=figures
                            get_cleandata.abstract_text = abstract
                            get_cleandata.content = content
                            get_cleandata.update_time = datetime.utcnow()
                        else:
                            io_data.figures = figures
                            db.session.add(io_data)

                        db.session.commit()
                        add_to_array(f'{success_list_key}{task_id}', original_data.id, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                        time.sleep(0.2)
                        index = index + 1

                except Exception as e:


                    add_to_array(f'{fail_list_key}{task_id}', original_data.id, 3600)
                    redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                    # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                    # path = LOG_FILE + f'./resource/{task_id}.log'
                    logger.error(f'an error occurred,which is {e},doi is {doi} , taskId is {task_id}')
                    # os.makedirs(os.path.dirname(path), exist_ok=True)
                    # update_and_save_map(path, get_data)
                    # raise e

                    continue



    return 'ok'

def get_figure_list_to_clean_data( doi, literature_id, content):
    data_list = [step['data'] for step in content['steps']]
    total_list = []
    for data in data_list:
        data_soup = BeautifulSoup(data, 'html.parser')
        img_list = data_soup.find_all('img')
        total_list.extend(img_list)
    logger.info(f'total list: {len(total_list)} literature_id: {literature_id} literature doi: {doi}')
    all_data = []
    for img_tag in total_list:
        oss_path = img_tag.get('src')
        oss_path = oss_path.replace('https://static.yanyin.tech/', '')
        if ';base64' in oss_path:
            continue

        description = img_tag.get('title')
        preview_oss_path = None
        data['description'] =description
        data['doi'] = doi
        data['oss_path'] = oss_path
        data['preview_oss_path'] = preview_oss_path
        all_data.append(data)
    return all_data
