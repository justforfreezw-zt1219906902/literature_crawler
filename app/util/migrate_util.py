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
    batch_hash_set
from app.util.text_deal import read_strings_from_file
from app.util.time_deal import get_timestamp, get_utc_timestamp
from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)

def connect():
    # Replace with your database connection details
    conn = psycopg2.connect(
        dbname=get_env('DB_DATABASE'),
        user=get_env('DB_USERNAME'),
        password=get_env('DB_PASSWORD'),
        host=get_env('DB_HOST'),
        port=get_env('DB_PORT')
    )
    return conn

def insert_literature_authors(author_id, cur, literature_id):
    cur.execute(
        "INSERT INTO literature_authors (id,create_time, update_time, is_deleted, create_by, update_by,"
        "literature_id, author_id) VALUES (%(id)s,now(), now(), 0, 1, 1,"
        "%(literature_id)s, %(author_id)s);",
        {'id': str(uuid.uuid4()), 'literature_id': literature_id, 'author_id': author_id}
    )


def insert_into_literature_keywords(cur, keyword_id, literature_id):
    cur.execute(
        "INSERT INTO literature_keywords (id,create_time, update_time, is_deleted, create_by, update_by,"
        "literature_id, keywords_id,create_from) VALUES (%(id)s,now(), now(), 0, 1, 1,"
        "%(literature_id)s, %(keywords_id)s, %(create_from)s);",
        {'id': str(uuid.uuid4()), 'literature_id': literature_id, 'keywords_id': keyword_id,
         'create_from': 'crawl'}
    )
def insert_literature_reference(cur, literature_id, ref_id):
    cur.execute(
        "INSERT INTO literature_reference (id,create_time, update_time, is_deleted, create_by, update_by,"
        "literature_id, reference_id) VALUES (%(id)s,now(), now(), 0, 1, 1,"
        "%(literature_id)s, %(reference_id)s);",
        {'id': str(uuid.uuid4()), 'literature_id': literature_id, 'reference_id': ref_id}
    )

def insert_protocol(author_name_list, cur, literature_id, number, publish_date, doi,name,keywords):
    cur.execute(sql.SQL(
        "INSERT INTO protocol (create_time, update_time, is_deleted, create_by, update_by,"
        "id, authors, doi, name, publish_date,keywords,content,type) "
        "VALUES (now(), now(), 0, 1, 1,"
        "%(id)s, %(authors)s, %(doi)s, %(name)s, %(publish_date)s, %(keywords)s,%(content)s,%(type)s);"
    ), {
        'id': number,
        'authors': Json(author_name_list),
        'doi': doi,
        'name': name,
        'publish_date': publish_date,
        'keywords': Json(keywords),
        'content': Json({'literatureId': literature_id}),
        'type': 'md'
    })


def get_protocol_max_id(cur):
    cur.execute("""
                                                            SELECT * FROM protocol WHERE id = (SELECT MAX(id) FROM protocol);
                                                        """)
    inserted_row = cur.fetchone()
    return inserted_row


def insert_literature(cur, literature_id, literature_type, publish_date, abstract_text,doi,title,content,file_info,issue,volume,journal_name):
    cur.execute(sql.SQL(
        "INSERT INTO literature (create_time, update_time, is_deleted, create_by, update_by,"
        "id, abstract_text, doi, title, journal_name, publish_date,content,file_info,literature_type,issue,volume) "
        "VALUES (now(), now(), 0, 1, 1,"
        "%(id)s, %(abstract_text)s, %(doi)s, %(title)s, %(journal_name)s, %(publish_date)s, %(content)s, %(file_info)s,%(literature_type)s"
        ",%(issue)s,%(volume)s);"
    ), {
        'id': literature_id,
        'abstract_text': abstract_text,
        'doi': doi,
        'title':title,
        'journal_name': journal_name,
        'publish_date': publish_date,
        'content': Json(content),
        'file_info': Json(file_info),
        'literature_type': literature_type,
        'issue': issue,
        'volume': volume
    })


def update_literature(cur, literature_id, abstract_text,content):
    cur.execute(sql.SQL(
        "UPDATE literature set update_time=now(),update_by=1,content=%(content)s  , abstract_text=%(abstract_text)s  "
        " where id =%(id)s;"
    ), {
        'abstract_text': abstract_text,
        'content': Json(content),
        'id': literature_id
    })


def get_literature_by_id(cur, literature_id):
    cur.execute("""
                        SELECT id FROM literature where id=%s
                                                                    """, (literature_id,))
    query_row = cur.fetchone()
    return query_row

def insert_or_select_id(cur, table_name, columns, values, name_value, type):
    """
    Inserts or selects an ID from the given table based on the provided values.
    If the record exists, it returns the existing ID; otherwise, it inserts the record and returns the new ID.
    """
    placeholders = ', '.join(['%s'] * len(values))

    query = f"""
                INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                            RETURNING id;
            """

    cur.execute(query, values)
    result = cur.fetchone()

    if not result:
        if '\'' in name_value:
            name_value = name_value.replace('\'', '\'\'')
        query = f"""

                        SELECT id FROM {table_name} WHERE name = '{name_value}'

                    """
        cur.execute(query, values)
        result = cur.fetchone()

    return result[0] if result else None


def delete_figure_list(cur, doi):

    cur.execute("""
                        delete 
                        FROM literature_figures where doi=%s
                        """, (doi,))
