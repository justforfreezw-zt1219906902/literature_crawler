import logging
import os
import time

from bs4 import BeautifulSoup
from flask import current_app
from sqlalchemy import and_

from app.config.config import get_env
from app.service import count_key, success_count_key, fail_count_key, total_count_key, success_list_key, fail_list_key
from app.util.current_protocol_clean_util import get_tre_data
from app.util.nature_protocol_clean_util import get_paper_info_by_html, get_ref_txt_by_html, \
    get_relate_txt_by_html, get_issue_by_html, get_abstract_by_html, get_key_points_by_html, get_clean_content_by_html

from extensions.ext_database import db
from app.models.clean_data import IOData, CleanDataNatureProtocol, CurrentData
from app.models.crawl_data import OriginalDataProtocolIO, ProtocolIoResources, OriginalDataNatureProtocol, \
    NatureProtocolResources, OriginalDataCurrentProtocol

from app.util.protocol_io_util import clean_author_list, \
    clean_ref_list, clean_relate_list, get_content_from_steps, get_abstartct
from app.util.redis_util import add_to_array, batch_hash_set, get_array
from app.util.text_deal import read_strings_from_file, write_strings_to_file, decompress_string_to_html
from app.util.time_deal import get_timestamp, timestamp_format
from datetime import datetime

from extensions.ext_redis import redis_client
from app.util.migrate_util import connect, delete_figure_list

logger = logging.getLogger(__name__)


def clean_current_protocol(task_id, task_setup):
    with current_app.app_context():
        session = db.session
        conflict_strategy = task_setup['conflict_strategy']
        id_list = task_setup['id_list']

        total_records = len(id_list)
        #  初始化redis count总数
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}',
                           {success_count_key: 0, fail_count_key: 0, total_count_key: total_records}, 360000)

        #  初始化redis 任务执行总数

        logger.info(f'task_id is {task_id},the length of clean list is {total_records}')
        success_list = get_array(f'{success_list_key}{task_id}')
        fail_list = get_array(f'{fail_list_key}{task_id}')
        for original_data_id in id_list:
            if original_data_id in success_list or original_data_id in fail_list:
                continue
                # doi='10.1002/cpz1.419'
            original_data = OriginalDataCurrentProtocol.query.filter_by(id=original_data_id).first()
            if not original_data:
                add_to_array(f'{fail_list_key}{task_id}', original_data_id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                # path = LOG_FILE + f'./resource/{task_id}.log'
                logger.error(
                    f'an error occurred,this data not exist in  original_data table ,id is {original_data_id} , taskId is {task_id}')
                continue

            get_cleandata = CurrentData.query.filter_by(id=original_data_id).first()
            if get_cleandata and conflict_strategy == 'skip':

                # redis 执行完一篇文章
                add_to_array(f'{success_list_key}{task_id}', get_cleandata.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                continue


            try:

                logger.info(
                    f'strat to clean current protocol ,doi is {get_cleandata.doi} ,id is {get_cleandata.id} taskId is {task_id}')

                # 404

                # if meta_data.doi in ['10.1002/cpz1.950','10.1002/cpz1.972','10.1002/cpz1.1094','10.1002/cpz1.1109','10.1002/cpz1.1092']:
                #     continue

                true_data = get_tre_data(original_data)

                data = CurrentData(**true_data)
                data.id = original_data.id
                data.doi = original_data.doi
                conn = connect()
                with conn.cursor() as cur:
                    DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
                    cur.execute(f"SET search_path TO {DB_SCHEMA};")
                    figures = get_figure_list_to_clean_data(cur, get_cleandata.doi)

                conn.close()
                if conflict_strategy == 'update' and get_cleandata:
                    get_cleandata.update_time = datetime.utcnow()
                    get_cleandata.content = data.content
                    get_cleandata.content = data.content
                    get_cleandata.figures = figures
                else:
                    data.figures = figures
                    session.commit(data)

                session.commit()
                time.sleep(0.1)
                add_to_array(f'{success_list_key}{task_id}', get_cleandata.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)

            except Exception as e:
                # raise e
                add_to_array(f'{fail_list_key}{task_id}', get_cleandata.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                # path = LOG_FILE + f'./resource/{task_id}.log'
                logger.error(
                    f'an error occurred,which is {e},doi is {get_cleandata.doi} id is {get_cleandata.id} , taskId is {task_id}')
                continue


def get_figure_list_to_clean_data(cur, doi):
    doi_prefix = str(doi).split('/')[1]
    doi_prefix = doi_prefix.replace('.', '')
    cur.execute("""
                            SELECT id, oss_path, doi,original_path,description,resource_type
                            FROM original_resource_current_protocol where doi=%s
                            """, (doi,))
    rows = cur.fetchall()
    all_list = []
    for row in rows:
        all_list.append(row)
    all_data = []
    for row in all_list:
        data = dict()
        if doi_prefix not in row[1] or not row[4] or '-fig-' not in row[1]:
            continue
        if not row[5] == 'jpg':
            continue
        oss_path = row[1]
        # preview_oss_path = oss_path.replace('.jpg', '.png')
        if '?' in oss_path:
            preview_oss_path = oss_path.split('?')[0].rsplit('/')[-1].replace('.jpg', '.png')
        else:
            temp_path = oss_path.split('/')[-1]
            preview_oss_path = temp_path.replace('.jpg', '.png')
        cur.execute("""
                                            SELECT id,oss_path from original_resource_current_protocol where oss_path like %s    
                                                                               """, ('%' + preview_oss_path + '%',))
        preview_rows = cur.fetchall()
        if len(preview_rows) == 0:
            preview_oss_path = None
        else:
            preview_oss_path = preview_rows[0][1]

        data['description'] = row[4]
        data['doi'] = doi
        data['oss_path'] = oss_path
        data['preview_oss_path'] = preview_oss_path
        all_data.append(data)
    return all_data
