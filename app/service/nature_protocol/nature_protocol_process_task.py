import logging

from app.models.task import DatasetsTask
from app.service import task_service
from app.service.nature_protocol.process_task.nature_protocol_clean import clean_nature_protocol
from app.service.nature_protocol.process_task.nature_protocol_crawl import crawl_nature_protocol
from app.service.nature_protocol.process_task.nature_protocol_publish import publish_nature_protocol
from app.service.process_action import ProcessActionStrategy, ProcessActionContext
from app.service.protocol_io.process_task.protocol_io_clean import clean_protocol_io
from app.service.protocol_io.process_task.protocol_io_publish import publish_protocol_io
from app.service.common.parse_pdf import parse_pdf

logger = logging.getLogger(__name__)
# 具体策略类
class CleanNatureProtocol(ProcessActionStrategy):
    def execute(self, datasets_task):
        task_setup=datasets_task.task_setup
        task_id=task_setup['task_id']
        if task_id:
            crawl_task=DatasetsTask.query.filter_by(id=task_id).first()
            if crawl_task:
                id_list=crawl_task.result_detail['success_list']
                task_setup['id_list']=id_list
        clean_nature_protocol(datasets_task.id, task_setup)
        task_service.end_task(datasets_task.id)


class CrawlNatureProtocol(ProcessActionStrategy):
    def execute(self, datasets_task):
        data=crawl_nature_protocol(datasets_task.id, datasets_task.task_setup)
        code=data['code']
        logger.debug(f'crawl nature protocol task is over code is  {code}')
        if data['code'] == 200:
            task_service.end_task(datasets_task.id)
        else:
            task_service.fail_task(datasets_task.id, data['msg'])


class PublishNatureProtocol(ProcessActionStrategy):
    def execute(self, datasets_task):
        task_setup = datasets_task.task_setup
        task_id = task_setup['task_id']
        if task_id:
            clean_task = DatasetsTask.query.filter_by(id=task_id).first()
            if clean_task:
                id_list = clean_task.result_detail['success_list']
                task_setup['id_list'] = id_list
        publish_nature_protocol(datasets_task.id, task_setup)
        task_service.end_task(datasets_task.id)


class ParseNatureProtocolPdf(ProcessActionStrategy):
    def execute(self, datasets_task):
        parse_pdf(datasets_task.id, datasets_task.task_setup)
        task_service.end_task(datasets_task.id)


class NatureProtocolProcessor:

    @staticmethod
    def execute(datasets_task):
        STRATEGIES = {
            "clean": CleanNatureProtocol(),
            "crawl": CrawlNatureProtocol(),
            "publish": PublishNatureProtocol(),
            "parse_pdf": ParseNatureProtocolPdf()
        }
        context = ProcessActionContext()

        # 使用字典获取策略
        context.strategy = STRATEGIES.get(datasets_task.type)

        context.perform_action(datasets_task)