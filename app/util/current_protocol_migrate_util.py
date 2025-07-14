import logging
import os
import time
import uuid
from datetime import datetime

import psycopg2
from flask import current_app
from psycopg2 import sql
from psycopg2._json import Json

from app.config.config import get_env
from app.service import count_key, success_count_key, fail_count_key, total_count_key, success_list_key, fail_list_key

from app.util.oss_util import get_file_md5
from app.util.redis_util import add_to_array, \
    batch_hash_set, get_array
from app.util.text_deal import read_strings_from_file
from app.util.time_deal import get_timestamp, get_utc_timestamp
from extensions.ext_redis import redis_client

from app.util.migrate_util import insert_literature_authors, insert_into_literature_keywords, \
    insert_literature_reference, insert_protocol \
    , get_protocol_max_id, insert_literature, update_literature, get_literature_by_id, insert_or_select_id, \
    delete_figure_list

logger = logging.getLogger(__name__)


def migrate_data(conn, conflict_strategy, id_list, task_id):
    cur = conn.cursor()
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
    cur.execute(f"SET search_path TO {DB_SCHEMA};")
    logging.info(
        f"task_id is {task_id} ,Start to migrate data")
    success_list = get_array(f'{success_list_key}{task_id}')
    fail_list = get_array(f'{fail_list_key}{task_id}')
    for clean_data_id in id_list:
        if clean_data_id in success_list or clean_data_id in fail_list:
            continue
        with conn:
            with conn.cursor() as cur:
                try:
                    row = get_query_content(cur, clean_data_id)
                    literature_id = row[0]
                    literature_doi = row[2]

                    start_info = f'start to deal literature doi is {literature_doi} id is {literature_id}  task_id is {task_id}'

                    logger.info(start_info)
                    query_row = get_literature_by_id(cur, literature_id)

                    # 如果是skip
                    if conflict_strategy == 'skip' and query_row:
                        if task_id:
                            add_to_array(f'{success_list_key}{task_id}', clean_data_id, 3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                        continue
                    elif conflict_strategy == 'update' and query_row:
                        if task_id:
                            add_to_array(f'{success_list_key}{task_id}', clean_data_id, 3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)

                        update_literature(cur, literature_id, row[1], row[8])

                        delete_figure_list(cur, literature_doi)
                        insert_figure_list(cur, literature_doi, literature_id)
                        continue
                    else:
                        publish_date = row[4]

                        if publish_date:
                            try:
                                publish_date = datetime.strptime(publish_date, '%d %B %Y').date()
                            except ValueError:
                                publish_date = None
                        # Insert literature
                        literature_type='protocol'

                        current_time = datetime.now()

                        insert_figure_list(cur, literature_doi, literature_id)

                        # abstract_text,doi,title,content,file_info,issue,volume,journal_name
                        insert_literature(cur, literature_id, literature_type, publish_date, row[1], row[2], row[3],
                                          row[8], row[12], row[10], row[11], 'current_protocol')

                        inserted_row = get_protocol_max_id(cur)
                        if inserted_row:
                            if inserted_row[0] > 19999:
                                number = inserted_row[0] + 1
                            else:
                                number = 20000
                        else:
                            number = 20000
                        author_name_list = []
                        for author in row[6]:
                            if 'name' not in dict(author).keys() or not author['name']:
                                continue
                            author_name_list.append(author['name'])

                        insert_protocol(author_name_list, cur, literature_id, number, publish_date, literature_doi,
                                        row[3], row[5])

                        if row[5]:  # keywords
                            for kw in row[5]:
                                if not kw:
                                    continue
                                keyword_id = insert_or_select_id(cur, 'keywords',
                                                                 ['create_time', 'update_time', 'is_deleted',
                                                                  'create_by', 'update_by', 'id', 'name'],
                                                                 (
                                                                     current_time, current_time, 0, 1, 1,
                                                                     str(uuid.uuid4()),
                                                                     kw), kw, 'yes')
                                if not keyword_id:
                                    raise Exception('keyword_id is null')
                                insert_into_literature_keywords(cur, keyword_id, literature_id)

                        if row[6]:  # authors
                            for author in row[6]:
                                author_id = insert_or_select_id(cur, 'author',
                                                                ['create_time', 'update_time', 'is_deleted',
                                                                 'create_by', 'update_by', 'id', 'name', 'type', 'org'],
                                                                (current_time, current_time, 0, 1, 1, str(uuid.uuid4()),
                                                                 author['name'], author.get('type', ''),
                                                                 author.get('institution', '')), author['name'], 'yes')
                                if not author_id:
                                    raise Exception('author_id is null')
                                insert_literature_authors(author_id, cur, literature_id)

                        if row[9]:  # references
                            for ref in row[9]:
                                if not ref['ref_text']:
                                    continue
                                ref_id = insert_or_select_id(cur, 'reference',
                                                             ['create_time', 'update_time', 'is_deleted', 'create_by',
                                                              'update_by', 'id', 'literature_info', 'status'],
                                                             (current_time, current_time, 0, 1, 1, str(uuid.uuid4()),
                                                              Json(ref), 'need.check'), None, 'no')
                                if not ref_id:
                                    raise Exception('ref_id is null')
                                insert_literature_reference(cur, literature_id, ref_id)

                        time.sleep(0.2)
                        if task_id:
                            add_to_array(f'{success_list_key}{task_id}', clean_data_id, 3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)

                except Exception as e:
                    logger.error(
                        f'an error occurred ,which is {str(e)},doi is {literature_doi},taskId is {task_id}')
                    # raise e
                    if task_id:
                        add_to_array(f'{fail_list_key}{task_id}', clean_data_id, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                    time.sleep(0.2)
                    # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                    # path = LOG_FILE + f'./resource/{task_id}.log'
                    # os.makedirs(os.path.dirname(path), exist_ok=True)

                    # update_and_save_map(path, get_data)


def insert_figure_list(cur, doi, literature_id):
    doi_prefix = str(doi).split('/')[1]
    doi_prefix=doi_prefix.replace('.','')
    cur.execute("""
                        SELECT id, oss_path, doi,original_path,description,resource_type
                        FROM original_resource_current_protocol where doi=%s
                        """, (doi,))
    rows = cur.fetchall()
    all_list=[]
    for row in rows:
        all_list.append(row)
    for row in all_list:
        if doi_prefix not in row[1] or  not  row[4] or '-fig-' not in row[1] :
            continue
        if not row[5] == 'jpg':
            continue
        oss_path = row[1]
        # preview_oss_path = oss_path.replace('.jpg', '.png')
        if '?' in oss_path:
            preview_oss_path=oss_path.split('?')[0].rsplit('/')[-1].replace('.jpg', '.png')
        else:
            temp_path=oss_path.split('/')[-1]
            preview_oss_path=temp_path.replace('.jpg', '.png')
        cur.execute("""
                                        SELECT id,oss_path from original_resource_current_protocol where oss_path like %s    
                                                                           """, ('%'+preview_oss_path+'%',))
        preview_rows = cur.fetchall()
        if len(preview_rows) == 0:
            preview_oss_path = None
        else:
            preview_oss_path=preview_rows[0][1]
        cur.execute(
            "INSERT INTO literature_figures (id,create_time, update_time, is_deleted, create_by, update_by,"
            "literature_id, description,doi,oss_path,preview_oss_path) VALUES (%(id)s,now(), now(), 0, 1, 1,"
            "%(literature_id)s, %(description)s,%(doi)s,%(oss_path)s,%(preview_oss_path)s);",
            {'id': str(uuid.uuid4()), 'literature_id': literature_id, 'description': row[4], 'doi': doi,
             'oss_path': oss_path, 'preview_oss_path': preview_oss_path}
        )


def get_query_content(cur, clean_data_id):
    cur.execute("""
                    SELECT id, abstract_text, doi, title, publish_date, keywords, author_list, relates, content,reference
                     ,issue,volume,file_info
                    FROM clean_data_current_protocol where id=%s
                    """, (clean_data_id,))
    row = cur.fetchone()
    return row
