import logging

import json


from flask import Blueprint, request

from app.service import task_service
from app.models.task import (DatasetsTask)


logger = logging.getLogger(__name__)

journal_name_source = ['protocol_io', 'current_protocol', 'bio_protocol', 'nature_protocol']
data_operate_type = ['clean', 'crawl', 'migrate', 'parse_pdf','migrate_pic','publish']

task = Blueprint('task', __name__)


@task.route('/task', methods=['POST'])
def create_task():
    data = request.data.decode('utf-8')
    data = json.loads(data)
    journal_name = data.get('journal_name')
    operate_type = data.get('type')
    datasets_task = DatasetsTask.query.filter_by(journal_name=journal_name, status='progress').first()
    if datasets_task:
        task_id = str(datasets_task.id)
        data = {'code': 400, 'data': task_id, 'msg': 'task already exists'}
        return data
    if not (journal_name in journal_name_source and operate_type in data_operate_type):
        logger.error(f"No strategy found for journal_name={journal_name} and action_type={operate_type}")

        data = {'code': 400,
                'msg': f"No strategy found for journal_name={journal_name} and action_type={operate_type}"}
        return data

    return task_service.create_task(data)


@task.route('/task', methods=['GET'])
def get_task():
    task_id = request.args.get('id', False)
    datasets_task = DatasetsTask.query.filter_by(id=task_id).first()
    if not datasets_task:
        data = {'code': 400,
                'msg': f"task not exist"}
        return data
    return task_service.get_task(datasets_task)
