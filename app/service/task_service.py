import logging
import threading
from datetime import datetime

from flask import current_app

from app.models.task import DatasetsTask
from app.service import count_key, success_count_key, fail_count_key, total_count_key,success_list_key, fail_list_key
from app.service.journal_processor_factory import JournalProcessorFactory

from app.util.redis_util import get_array, get_hash_map
from extensions.ext_database import db
from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)


def create_task(data):
    session = db.session
    datasets_task = DatasetsTask(**data)
    datasets_task.status = 'progress'
    datasets_task.create_time = datetime.utcnow()
    session.add(datasets_task)
    session.commit()
    return start_task(datasets_task)





def start_task(datasets_task):
    task_id = datasets_task.id

    logger.info(f'start taskId is {task_id}, task_setup is {datasets_task.task_setup}')
    thread = threading.Thread(target=process_task, args=(task_id, current_app.app_context(),))
    # 启动线程
    thread.start()
    return {'code': 200, 'data': datasets_task.to_dict()}




def process_task(task_id, app_context):
    with app_context:
        datasets_task = DatasetsTask.query.filter_by(id=task_id).first()
        # task_setup = datasets_task.task_setup
        # head_task_id = task_setup['task_id']
        # if task_id:
        #     clean_task = DatasetsTask.query.filter_by(id=head_task_id).first()
        #     if clean_task:
        #         id_list = clean_task.result_detail['success_list']
        #         task_setup['id_list'] = id_list
        #         datasets_task.task_setup = task_setup
        processor = JournalProcessorFactory.produce(datasets_task.journal_name)
        processor.execute(datasets_task)


def get_task(datasets_task):
    if datasets_task.status == 'progress':
        get_progress_from_redis(datasets_task)

    datasets_task_map = datasets_task.to_dict()
    return datasets_task_map


def get_progress_from_redis(datasets_task):

    map_key = f'{count_key}{datasets_task.id}'

    count_map = get_hash_map(map_key)
    success_list = get_array(f'{success_list_key}{datasets_task.id}')
    fail_list = get_array(f'{fail_list_key}{datasets_task.id}')
    detail = {'success_list': success_list, 'fail_list': fail_list}
    datasets_task.success_count = count_map[success_count_key]
    datasets_task.failed_count = count_map[fail_count_key]
    datasets_task.total_count = count_map[total_count_key]
    datasets_task.result_detail = detail


def end_task(task_id):
    session = db.session
    datasets_task = DatasetsTask.query.filter_by(id=task_id).first()
    get_progress_from_redis(datasets_task)
    datasets_task.end_time = datetime.utcnow()
    datasets_task.status = 'finish'
    session.commit()
    redis_client.delete(f'{count_key}{datasets_task.id}')
    redis_client.delete(f'{success_list_key}{datasets_task.id}')
    redis_client.delete(f'{fail_list_key}{datasets_task.id}')


def fail_task(task_id, msg):
    session = db.session
    datasets_task = DatasetsTask.query.filter_by(id=task_id).first()
    get_progress_from_redis(datasets_task)
    datasets_task.end_time = datetime.utcnow()
    datasets_task.status = 'failed'
    datasets_task.failed_reason = msg
    session.commit()
    redis_client.delete(f'{count_key}{datasets_task.id}')
    redis_client.delete(f'{success_list_key}{datasets_task.id}')
    redis_client.delete(f'{fail_list_key}{datasets_task.id}')