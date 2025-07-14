import json
import logging
import os
import time

from bs4 import BeautifulSoup
from flask import current_app
from datetime import datetime
from app.config.config import get_env
from app.service import count_key, success_count_key, fail_list_key, success_list_key, fail_count_key, total_count_key

from app.util.nature_protocol_crawl_util import get_list_last_page, get_page_all_data_list, get_data_from_html, \
    get_all_resource_from_html
from extensions.ext_database import db
from app.models.crawl_data import OriginalDataProtocolIO, ProtocolIoResources, OriginalDataNatureProtocol, \
    NatureProtocolResources

from app.util.download import get_http_data, download_file, download_video, get_http_html
from app.util.oss_util import upload_file, get_file_md5, file_exist
from app.util.protocol_io_util import get_pdf_attrs, get_documents_attrs, get_resource_attrs
from app.util.redis_util import add_to_array, \
    batch_hash_set
from app.util.text_deal import get_file_extension, compress_html_to_string
from app.util.time_deal import get_timestamp, split_time
import uuid

from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)

def vectoried_nature_protocol(task_id, task_setup):
    with current_app.app_context():
        conflict_strategy = task_setup['conflict_strategy']
        doi_list = task_setup['doi_list']
        batch_hash_set(f'{count_key}{task_id}', {success_count_key: 0, fail_count_key: 0, total_count_key: 0}, 3600)

        redis_client.hset(f'{count_key}{task_id}', 'total_count', len(doi_list))
        vectoried_data( conflict_strategy, doi_list, task_id)


    return 'ok'
def vectoried_data(conflict_strategy, doi_list, task_id):


    for doi in doi_list:


                try:
                    row = get_query_content(cur, doi)
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
                        delete_figure_list(cur, doi)
                        insert_figure_list(cur, doi, literature_id)
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

                        insert_figure_list(cur, doi, literature_id)

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
                        add_to_array(f'{success_list_key}{task_id}', literature_doi, 3600)
                        redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                        time.sleep(0.2)

                except Exception as e:
                    raise e
                    add_to_array(f'{fail_list_key}{task_id}', literature_doi, 3600)
                    redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                    time.sleep(0.2)
                    # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                    # path = LOG_FILE + f'./resource/{task_id}.log'
                    # os.makedirs(os.path.dirname(path), exist_ok=True)
                    logger.error(
                        f'an error occurred ,which is {str(e)},doi is {literature_doi},taskId is {task_id}')
                    # update_and_save_map(path, get_data)