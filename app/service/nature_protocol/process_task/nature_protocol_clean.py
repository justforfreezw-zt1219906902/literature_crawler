import logging
import os
import tempfile
import time

from bs4 import BeautifulSoup
from flask import current_app
from pytz import reference
from sqlalchemy import and_

from app.config.config import get_env
from app.service import count_key, success_count_key, fail_count_key, total_count_key, success_list_key, fail_list_key
from app.service.common.parse_pdf import get_file_info
from app.util.migrate_util import connect
from app.util.nature_protocol_clean_util import get_paper_info_by_html, get_ref_txt_by_html, \
    get_relate_txt_by_html, get_issue_by_html, get_abstract_by_html, get_key_points_by_html, get_clean_content_by_html
from app.util.oss_util import get_default_bucket

from extensions.ext_database import db
from app.models.clean_data import IOData, CleanDataNatureProtocol
from app.models.crawl_data import OriginalDataProtocolIO, ProtocolIoResources, OriginalDataNatureProtocol, \
    NatureProtocolResources

from app.util.protocol_io_util import clean_author_list, \
    clean_ref_list, clean_relate_list, get_content_from_steps, get_abstartct
from app.util.redis_util import add_to_array, batch_hash_set, get_array
from app.util.text_deal import read_strings_from_file, write_strings_to_file, decompress_string_to_html
from app.util.time_deal import get_timestamp, timestamp_format
from datetime import datetime

from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)


def clean_nature_protocol(task_id, task_setup):
    with current_app.app_context():

        session = db.session

        conflict_strategy = task_setup['conflict_strategy']
        id_list = task_setup['id_list']
        total_records = len(id_list)
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}',
                           {success_count_key: 0, fail_count_key: 0, total_count_key: total_records}, 360000)
        logger.info(f'task_id is {task_id},the length of clean list is {total_records}')

        index = 1
        success_list = get_array(f'{success_list_key}{task_id}')
        fail_list = get_array(f'{fail_list_key}{task_id}')
        bucket = get_default_bucket()
        # 循环处理所有页数
        for original_data_id in id_list:
            if original_data_id in success_list or original_data_id in fail_list:
                continue
            original_data = OriginalDataNatureProtocol.query.filter_by(id=original_data_id).first()
            get_cleandata = CleanDataNatureProtocol.query.filter_by(id=original_data_id).first()
            # 如果是更新的逻辑
            if conflict_strategy == 'skip' and get_cleandata:
                # redis 执行完一篇文章
                add_to_array(f'{success_list_key}{task_id}', get_cleandata.doi, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)

                continue
            doi=original_data.doi

            try:

                issue = original_data.issue
                volume = original_data.volume

                content = original_data.content

                strat_info = f'taskid is {task_id} index is {index} :start to clean nature protocol ,doi is {original_data.doi}'
                logger.info(strat_info)

                publish_date = timestamp_format(original_data.published_on)

                resources = NatureProtocolResources.query.filter_by(doi=original_data.doi).all()
                soup = BeautifulSoup(content, 'html.parser')
                paper_info = get_paper_info_by_html(soup)

                # 这里需要使用正则表达式提取各种信息

                ref_list = get_ref_txt_by_html(soup)

                # doi title uri
                relate_list = get_relate_txt_by_html(soup)
                if not issue:
                    issue = get_issue_by_html(soup)
                if not volume:
                    volume = paper_info['volume']

                abstract_text = get_abstract_by_html(soup)

                content = get_clean_content_by_html(soup, resources)

                key_points = get_key_points_by_html(soup)
                io_data = CleanDataNatureProtocol(
                    doi=original_data.doi,
                    title=original_data.title,
                    publish_date=publish_date,
                    relates=relate_list,
                    content=content,
                    abstract_text=abstract_text,
                    reference=ref_list,
                    author_list=paper_info['author_list'],
                    paper_type=original_data.type,
                    id=original_data.id,
                    issue=issue,
                    key_points=key_points,
                    volume=volume

                )

                conn = connect()
                with conn.cursor() as cur:
                    DB_SCHEMA = os.getenv('DB_SCHEMA', 'datasets')
                    cur.execute(f"SET search_path TO {DB_SCHEMA};")
                    figures = get_figure_list_to_clean_data(cur, get_cleandata.doi)

                conn.close()
                pdf_key = f'literature/original_nature_protocol/{doi}/original_pdf/'
                try:
                    pdf_file = bucket.get_object(pdf_key)

                    if pdf_file:
                        with tempfile.NamedTemporaryFile(dir='/tmp', suffix='.pdf') as temp_file:
                            file_info=get_file_info(temp_file,pdf_file,pdf_key,conflict_strategy,bucket)
                        temp_file.close()
                except Exception as e:
                    logger.error(f'an error occurred,which is {e},doi is {doi} , taskId is {task_id}')
                    file_info = None
                if conflict_strategy == 'update' and get_cleandata:

                    get_cleandata.abstract_text = abstract_text
                    get_cleandata.content = content
                    get_cleandata.figures = figures
                    get_cleandata.file_info=file_info
                    get_cleandata.update_time = datetime.utcnow()
                else:
                    io_data.figures=figures
                    io_data.file_info = file_info
                    session.add(io_data)

                session.commit()


                add_to_array(f'{success_list_key}{task_id}',original_data_id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                time.sleep(0.1)
                index = index + 1

            except Exception as e:
                # raise e
                #  redis 执行一篇文章的子任务失败
                add_to_array(f'{fail_list_key}{task_id}', original_data_id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
                # path = LOG_FILE + f'./resource/{task_id}.log'
                logger.error(f'an error occurred,which is {e},doi is {doi} , taskId is {task_id}')
                # os.makedirs(os.path.dirname(path), exist_ok=True)
                # update_and_save_map(path, get_data)

                continue


    return 'ok'

def get_figure_list_to_clean_data(cur, doi):
    doi_prefix = str(doi).split('/')[1]
    cur.execute("""
                        SELECT id, oss_path, doi,original_path,description,resource_type
                        FROM original_resource_nature_protocol where doi=%s
                        """, (doi,))
    rows = cur.fetchall()
    all_list=[]
    for row in rows:
        all_list.append(row)
    all_data = []
    #literature/nature_protocol/10.1038/s41596-022-00750-2/full/41596_2022_750_Fig1_HTML1.png
    for row in all_list:
        data = dict()
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

        data['description'] = row[4]
        data['doi'] = doi
        data['oss_path'] = oss_path
        data['preview_oss_path'] = preview_oss_path
        all_data.append(data)
    return all_data