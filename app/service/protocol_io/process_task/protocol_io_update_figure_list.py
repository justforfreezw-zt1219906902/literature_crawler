import logging
import os
import time
import uuid
from datetime import datetime

import psycopg2
from bs4 import BeautifulSoup
from flask import current_app
from psycopg2 import sql
from psycopg2._json import Json

from app.config.config import get_env
from app.service import count_key, success_count_key, fail_count_key, total_count_key, success_list_key, fail_list_key
from app.service.protocol_io.process_task.protocol_io_publish import insert_figure_list, get_query_content, \
    get_query_total_doi_list

from app.util.oss_util import get_file_md5
from app.util.redis_util import add_to_array, \
    batch_hash_set, get_array
from app.util.text_deal import read_strings_from_file
from app.util.time_deal import get_timestamp, get_utc_timestamp
from extensions.ext_redis import redis_client

from app.util.migrate_util import connect,insert_literature_authors,insert_into_literature_keywords,insert_literature_reference,insert_protocol\
,get_protocol_max_id,insert_literature,update_literature,get_literature_by_id,insert_or_select_id,delete_figure_list

logger = logging.getLogger(__name__)


def update_protocol_io_figure_list(task_id,task_setup):
    with current_app.app_context():

        conflict_strategy = task_setup['conflict_strategy']

        doi_list = task_setup['doi_list']
        # doi_list=['10.17504/protocols.io.eq2lyjmqrlx9/v1']
        conn = connect()

        # if start_time:
        #     time1 = get_timestamp(start_time)
        #
        #     time2 = get_timestamp(end_time)
        #     # time2_utc = get_utc_timestamp(time2)
        #     time2_utc = time2
        #     doi_list=get_query_total_doi_list(conn,time1,time2_utc)

        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}',{success_count_key:0,fail_count_key:0,total_count_key:len(doi_list)},3600)

        update_figure_list(conn, conflict_strategy, task_id,doi_list)
        conn.close()

    return 'ok'








def update_figure_list(conn, conflict_strategy, task_id,doi_list):

    page_size=10
    # logging.info(
    #     f"task_id is {task_id} ,Executing SQL query params:start_time is {time1}   end_time is {time2}")
    # total_number=get_query_total_number(conn, doi_list)
    redis_client.hset(f'{count_key}{task_id}', 'total_count', len(doi_list))
    total_pages = (len(doi_list) + page_size - 1) // page_size
    success_list = get_array(f'{success_list_key}{task_id}')
    fail_list = get_array(f'{fail_list_key}{task_id}')
    for page_number in range(1, total_pages + 1):
        offset = (page_number - 1) * page_size
        with conn:
            with conn.cursor() as cur:
                DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
                cur.execute(f"SET search_path TO {DB_SCHEMA};")
                rows =  get_query_content(cur,offset,page_size,doi_list)
                for row in rows:
                    try:
                        literature_id = row[0]
                        literature_doi = row[2]

                        if literature_doi in success_list or literature_doi in fail_list:
                            continue

                        content = row[8]
                        start_info = f'start to deal literature doi is {literature_doi} id is {literature_id}  task_id is {task_id}'
                        logger.info(start_info)
                        query_row = get_literature_by_id(cur, literature_id)
                        #如果是skip
                        if conflict_strategy == 'skip' and query_row:
                            add_to_array(f'{success_list_key}{task_id}', literature_doi,3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                            continue
                        elif conflict_strategy == 'update' and query_row:
                            add_to_array(f'{success_list_key}{task_id}', literature_doi,3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                            delete_figure_list(cur,literature_doi)

                            insert_figure_list(cur, literature_doi, literature_id,content)
                            continue
                        else:

                            insert_figure_list(cur, literature_doi, literature_id, content)
                            add_to_array(f'{success_list_key}{task_id}', literature_doi,3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                            time.sleep(0.2)

                    except Exception as e:

                        add_to_array(f'{fail_list_key}{task_id}', literature_doi,3600)
                        redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                        time.sleep(0.2)
                        # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                        # path = LOG_FILE + f'./resource/{task_id}.log'
                        # os.makedirs(os.path.dirname(path), exist_ok=True)
                        logger.error(
                                f'an error occurred ,which is {str(e)},doi is {literature_doi},taskId is {task_id}')
                        raise e
                            # update_and_save_map(path, get_data)

