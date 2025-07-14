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
from app.util.current_protocol_migrate_util import migrate_data

from app.util.oss_util import get_file_md5
from app.util.redis_util import add_to_array, \
    batch_hash_set
from app.util.text_deal import read_strings_from_file
from app.util.time_deal import get_timestamp, get_utc_timestamp
from extensions.ext_redis import redis_client

from app.util.migrate_util import connect,insert_literature_authors,insert_into_literature_keywords,insert_literature_reference,insert_protocol\
,get_protocol_max_id,insert_literature,update_literature,get_literature_by_id,insert_or_select_id,delete_figure_list


logger = logging.getLogger(__name__)


def publish_current_protocol(task_id, task_setup):
    with current_app.app_context():
        conflict_strategy = task_setup['conflict_strategy']
        id_list = task_setup['id_list']
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}', {success_count_key: 0, fail_count_key: 0, total_count_key: len(doi_list)}, 3600)

        conn = connect()

        migrate_data(conn, conflict_strategy, id_list, task_id)

    return 'ok'