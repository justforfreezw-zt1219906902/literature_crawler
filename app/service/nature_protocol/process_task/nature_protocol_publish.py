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

from app.util.migrate_util import connect,insert_literature_authors,insert_into_literature_keywords,insert_literature_reference,insert_protocol\
,get_protocol_max_id,insert_literature,update_literature,get_literature_by_id,insert_or_select_id,delete_figure_list


logger = logging.getLogger(__name__)


def publish_nature_protocol(task_id, task_setup):
    with current_app.app_context():
        conflict_strategy = task_setup['conflict_strategy']
        id_list = task_setup['id_list']
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}', {success_count_key: 0, fail_count_key: 0, total_count_key: len(id_list)}, 3600)
        conn = connect()
        migrate_data(conn, conflict_strategy, id_list, task_id)
        conn.close()

    return 'ok'



def get_literature_type(param):
    if param == 'Addendum' or param == 'Corrigendum' or param == 'Erratum':
        return 'erratum', True
    elif param == 'Author Correction' or param == 'Publisher Correction' or param == 'Retracion':
        return 'correction', True
    elif param == 'Consensus Statement' or param == 'Consensus':
        return 'consensus', False
    elif param == 'Correspondence':
        return 'correspondence', False
    elif param == 'Editorial':
        return 'editorial', False
    elif param == 'Matters Arising':
        return 'matters', False
    elif param == 'News & Views':
        return 'views', False
    elif param == 'Perspective':
        return 'perspective', False
    elif param == 'Poster':
        return 'poster', True
    elif param == 'Protocol' or param == 'Protocol Extension' or param == 'Protocol Update':
        return 'protocol', True
    elif param == 'Review Article':
        return 'review', True


def migrate_data(conn, conflict_strategy, doi_list, task_id):
    cur = conn.cursor()
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
    cur.execute(f"SET search_path TO {DB_SCHEMA};")
    logging.info(
        f"task_id is {task_id} ,Start to migrate data")
    success_list = get_array(f'{success_list_key}{task_id}')
    fail_list = get_array(f'{fail_list_key}{task_id}')
    # doi_list=['10.1038/s41596-024-01009-8']
    for clean_data_id in doi_list:
        if clean_data_id in success_list or clean_data_id in fail_list :
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

                        add_to_array(f'{success_list_key}{task_id}', literature_doi, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                        continue
                    elif conflict_strategy == 'update' and query_row:

                        update_literature(cur, literature_id, row[1],row[8])
                        add_to_array(f'{success_list_key}{task_id}', literature_doi, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
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
                        literature_type, flag = get_literature_type(row[10])

                        current_time = datetime.now()

                        insert_figure_list(cur, literature_doi, literature_id)

                        #abstract_text,doi,title,content,file_info,issue,volume,journal_name
                        insert_literature(cur, literature_id, literature_type, publish_date, row[1],row[2],row[3], row[8], row[13], row[11],row[12],'nature_protocol')
                        if flag:
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

                            insert_protocol(author_name_list, cur, literature_id, number, publish_date, literature_doi,row[3],row[5])

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
                                literature_info = ref
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
                        add_to_array(f'{success_list_key}{task_id}', clean_data_id, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                        time.sleep(0.2)

                except Exception as e:
                    logger.error(
                        f'an error occurred ,which is {str(e)},doi is {literature_doi},taskId is {task_id}')
                    # raise e
                    add_to_array(f'{fail_list_key}{task_id}', clean_data_id, 3600)
                    redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                    time.sleep(0.2)
                    # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                    # path = LOG_FILE + f'./resource/{task_id}.log'
                    # os.makedirs(os.path.dirname(path), exist_ok=True)

                    # update_and_save_map(path, get_data)


def insert_figure_list(cur, doi, literature_id):
    doi_prefix = str(doi).split('/')[1]
    cur.execute("""
                        SELECT id, oss_path, doi,original_path,description,resource_type
                        FROM original_resource_nature_protocol where doi=%s
                        """, (doi,))
    rows = cur.fetchall()
    all_list=[]
    for row in rows:
        all_list.append(row)
    #literature/nature_protocol/10.1038/s41596-022-00750-2/full/41596_2022_750_Fig1_HTML1.png
    for row in all_list:
        if doi_prefix not in row[3] or 'Fig' not in row[4] or 'full' not in row[3]:
            continue
        if not row[5] == 'png':
            continue
        oss_path=row[1]
        preview_oss_query=str(oss_path).split('/')[-1].split('_HTML')[0]
        cur.execute("""
                                SELECT oss_path from original_resource_nature_protocol where oss_path like %s and oss_path not like %s
                                """, ('%'+preview_oss_query+'%','%full%',))
        preview_rows = cur.fetchone()
        if not preview_rows:
            preview_oss_path =None
        else:
            preview_oss_path = preview_rows[0]

        cur.execute(
                "INSERT INTO literature_figures (id,create_time, update_time, is_deleted, create_by, update_by,"
                "literature_id, description,doi,oss_path,preview_oss_path) VALUES (%(id)s,now(), now(), 0, 1, 1,"
                "%(literature_id)s, %(description)s,%(doi)s,%(oss_path)s,%(preview_oss_path)s);",
                {'id': str(uuid.uuid4()), 'literature_id': literature_id, 'description': row[4], 'doi': doi,
                 'oss_path': oss_path,'preview_oss_path':preview_oss_path}
        )



def get_query_content(cur, clean_data_id):
    cur.execute("""
                    SELECT id, abstract_text, doi, title, publish_date, keywords, author_list, relates, content,reference
                     ,paper_type,issue,volume,file_info
                    FROM clean_data_nature_protocol where id=%s
                    """, (clean_data_id,))
    row = cur.fetchone()
    return row


def get_query_total_number(conn, time1, time2):
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT count(*)
                    FROM clean_data_protocol_io where 
                    to_date(publish_date, 'DD Month yyyy') >= to_timestamp(%s) AND to_date(publish_date, 'DD Month yyyy') <= to_timestamp(%s); 
                """, (time1, time2))
            row = cur.fetchall()
            return row[0][0]
