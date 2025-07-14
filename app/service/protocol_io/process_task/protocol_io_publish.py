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

from app.util.oss_util import get_file_md5
from app.util.redis_util import add_to_array, \
    batch_hash_set, get_array
from app.util.text_deal import read_strings_from_file
from app.util.time_deal import get_timestamp, get_utc_timestamp
from extensions.ext_redis import redis_client

from app.util.migrate_util import connect, insert_literature_authors, insert_into_literature_keywords, \
    insert_literature_reference, insert_protocol \
    , get_protocol_max_id, insert_literature, update_literature, get_literature_by_id, insert_or_select_id, \
    delete_figure_list

logger = logging.getLogger(__name__)


def publish_protocol_io(task_id, task_setup):
    with current_app.app_context():

        conflict_strategy = task_setup['conflict_strategy']

        doi_list = task_setup['doi_list']
        conn = connect()
        # if start_time:
        #     if not end_time:
        #         time2 = int(datetime.utcnow().timestamp())
        #     else:
        #         time2 = get_timestamp(end_time)
        #     time1 = get_timestamp(start_time)
        #
        #     # time2 = get_timestamp(end_time)
        #     # time2_utc = get_utc_timestamp(time2)
        #     time2_utc = time2
        #     doi_list = get_query_total_doi_list(conn, time1, time2_utc)
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}',
                           {success_count_key: 0, fail_count_key: 0, total_count_key: len(doi_list)}, 3600)
        # conn = connect()
        # create_tables(conn)
        # time2_utc = time2_utc - 24 * 3600
        migrate_data(conn, conflict_strategy, task_id, doi_list)
        conn.close()

    return 'ok'


def migrate_data(conn, conflict_strategy, task_id, doi_list):

    page_size = 10
    # logging.info(
    #     f"task_id is {task_id} ,Executing SQL query params:start_time is {time1}   end_time is {time2}")
    # total_number=get_query_total_number(conn, doi_list)
    redis_client.hset(f'{count_key}{task_id}', 'total_count', len(doi_list))
    total_pages = (len(doi_list) + page_size - 1) // page_size
    success_list = get_array(f'{success_list_key}{task_id}')
    fail_list = get_array(f'{fail_list_key}{task_id}')
    for page_number in range(1, total_pages + 1):
        cur = conn.cursor()
        DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
        cur.execute(f"SET search_path TO {DB_SCHEMA};")
        offset = (page_number - 1) * page_size
        rows = get_query_content(cur, offset, page_size, doi_list)
        time.sleep(4)
        logger.info(f'start to deal page {page_number}  ')
        for row in rows:
            with conn:
                with conn.cursor() as cur:
                    try:
                        literature_id = row[0]
                        literature_doi = row[2]

                        if literature_doi in success_list or literature_doi in fail_list:
                            continue

                        content = row[8]

                        start_info = f'start to deal literature doi is {literature_doi} id is {literature_id}  task_id is {task_id}'

                        logger.info(start_info)
                        query_row = get_literature_by_id(cur, literature_id)

                        # 如果是skip

                        if conflict_strategy == 'skip' and query_row:

                            add_to_array(f'{success_list_key}{task_id}', literature_doi, 3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                            continue
                        elif conflict_strategy == 'update' and query_row:

                            update_literature(cur, literature_id, row[1], row[8])

                            delete_figure_list(cur, literature_doi)

                            insert_figure_list(cur, literature_doi, literature_id, content)
                            add_to_array(f'{success_list_key}{task_id}', literature_doi, 3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                            continue
                        else:
                            publish_date = row[4]
                            insert_figure_list(cur, literature_doi, literature_id, content)
                            if publish_date:
                                try:
                                    publish_date = datetime.strptime(publish_date, '%d %B %Y').date()
                                except ValueError:
                                    publish_date = None
                            # Insert literature

                            doi_list = str(literature_doi).split('/')

                            doi_path = doi_list[1]
                            # clean_fail_list_string = read_strings_from_file(
                            #     './app/static/resource/file_not_exist_list_bakup.txt')
                            if len(doi_list) > 2 :
                                file_name = doi_list[1] + '_' + doi_list[2] + '.pdf'
                            else:
                                file_name = doi_list[1] + '.pdf'

                            oss_path = 'https://static.yanyin.tech/literature_test/protocol_io_true/' + doi_path + '/' + file_name

                            object_path = 'literature_test/protocol_io_true/' + doi_path + '/' + file_name
                            md5=get_file_md5(object_path)
                            if md5:
                                file_info = {'ossPath': oss_path, "md5": str()}
                            else:
                                file_info = None

                            literature_type = 'protocol'

                            current_time = datetime.now()
                            insert_literature(cur, literature_id, literature_type, publish_date, row[1], row[2], row[3],
                                              row[8], file_info, None, None, 'protocol_io')
                            inserted_row = get_protocol_max_id(cur)
                            if inserted_row:
                                if inserted_row[0] > 19999:
                                    number = inserted_row[0] + 1
                                else:
                                    number = 20000
                            else:
                                number = 20000
                            author_name_list = []
                            for author in row[7]:
                                if 'name' not in dict(author).keys() or not author['name']:
                                    continue
                                author_name_list.append(author['name'])

                            insert_protocol(author_name_list, cur, literature_id, number, publish_date, row[2], row[3],
                                            row[5])

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
                                                                     'create_by', 'update_by', 'id', 'name', 'type',
                                                                     'org'],
                                                                    (current_time, current_time, 0, 1, 1,
                                                                     str(uuid.uuid4()),
                                                                     author['name'], author.get('type', ''),
                                                                     author.get('institution', '')), author['name'],
                                                                    'yes')
                                    if not author_id:
                                        raise Exception('author_id is null')
                                    insert_literature_authors(author_id, cur, literature_id)

                            if row[9]:  # references
                                for ref in row[9]:
                                    if not ref['ref_text']:
                                        continue
                                    ref_id = insert_or_select_id(cur, 'reference',
                                                                 ['create_time', 'update_time', 'is_deleted',
                                                                  'create_by',
                                                                  'update_by', 'id', 'literature_info', 'status'],
                                                                 (
                                                                 current_time, current_time, 0, 1, 1, str(uuid.uuid4()),
                                                                 Json(ref), 'need.check'), None, 'no')
                                    if not ref_id:
                                        raise Exception('ref_id is null')
                                    insert_literature_reference(cur, literature_id, ref_id)
                            add_to_array(f'{success_list_key}{task_id}', literature_doi, 3600)
                            redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                            time.sleep(0.2)

                    except Exception as e:
                        add_to_array(f'{fail_list_key}{task_id}', literature_doi, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                        time.sleep(0.2)
                        # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                        # path = LOG_FILE + f'./resource/{task_id}.log'
                        # os.makedirs(os.path.dirname(path), exist_ok=True)
                        logger.error(
                            f'an error occurred ,which is {str(e)},doi is {literature_doi},taskId is {task_id}')
                        # update_and_save_map(path, get_data)
                        raise e
                        # continue


def insert_figure_list(cur, doi, literature_id, content):
    data_list = [step['data'] for step in content['steps']]
    total_list = []
    for data in data_list:
        data_soup = BeautifulSoup(data, 'html.parser')
        img_list = data_soup.find_all('img')
        total_list.extend(img_list)
    logger.info(f'total list: {len(total_list)} literature_id: {literature_id} literature doi: {doi}')
    for img_tag in total_list:
        oss_path = img_tag.get('src')
        oss_path = oss_path.replace('https://static.yanyin.tech/', '')
        if ';base64' in oss_path:
            continue

        description = img_tag.get('title')
        preview_oss_path = None
        cur.execute(
            "INSERT INTO literature_figures (id,create_time, update_time, is_deleted, create_by, update_by,"
            "literature_id, description,doi,oss_path,preview_oss_path) VALUES (%(id)s,now(), now(), 0, 1, 1,"
            "%(literature_id)s, %(description)s,%(doi)s,%(oss_path)s,%(preview_oss_path)s);",
            {'id': str(uuid.uuid4()), 'literature_id': literature_id, 'description': description, 'doi': doi,
             'oss_path': oss_path, 'preview_oss_path': preview_oss_path}
        )


def get_query_content(cur, offset, page_size, doi_list):
    placeholders = ', '.join(['%s'] * len(doi_list))

    cur.execute(f"""
                    SELECT id, abstract_text, doi, title, publish_date, keywords, author_list, relates, content,reference 
                    FROM clean_data_protocol_io where 
                    doi in ({placeholders}) LIMIT %s offset %s; 
                """, (*doi_list, page_size, offset))
    rows = cur.fetchall()


    return rows


def get_query_total_number(conn, time1, time2):
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                    SELECT count(*)
                    FROM clean_data_protocol_io where 
                    to_date(publish_date, 'DD Month yyyy') >= to_timestamp(%s) AND to_date(publish_date, 'DD Month yyyy') < to_timestamp(%s); 
                """, (time1, time2))
            row = cur.fetchall()
            return row[0][0]


def get_query_total_doi_list(conn, time1, time2):
    with conn:
        with conn.cursor() as cur:
            DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
            cur.execute(f"SET search_path TO {DB_SCHEMA};")
            cur.execute("""
                    SELECT doi
                    FROM clean_data_protocol_io where 
                    to_date(publish_date, 'DD Month yyyy') >= to_timestamp(%s) AND to_date(publish_date, 'DD Month yyyy') <to_timestamp(%s); 
                """, (time1, time2))
            rows = cur.fetchall()
            doi_list = []
            for row in rows:
                doi_list.append(row[0])
            return doi_list
