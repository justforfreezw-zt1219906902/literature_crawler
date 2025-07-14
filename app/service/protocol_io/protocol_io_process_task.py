from app.models.task import DatasetsTask
from app.service import task_service
from app.service.process_action import ProcessActionStrategy, ProcessActionContext
from app.service.protocol_io.process_task.protocol_io_clean import clean_protocol_io
from app.service.protocol_io.process_task.protocol_io_crawl import crawl_protocol_io
from app.service.protocol_io.process_task.protocol_io_publish import publish_protocol_io
from app.service.protocol_io.process_task.protocol_io_update_figure_list import update_protocol_io_figure_list


# 具体策略类
class CleanProtocolIo(ProcessActionStrategy):

    def execute(self, datasets_task):
        task_setup = datasets_task.task_setup
        task_id = task_setup['task_id']
        if task_id:
            crawl_task = DatasetsTask.query.filter_by(id=task_id).first()
            if crawl_task:
                id_list = crawl_task.result_detail['success_list']
                task_setup['id_list'] = id_list
        clean_protocol_io(datasets_task.id, datasets_task.task_setup)
        task_service.end_task(datasets_task.id)


class CrawlProtocolIo(ProcessActionStrategy):
    def execute(self, datasets_task):
        crawl_protocol_io(datasets_task.id, datasets_task.task_setup)
        task_service.end_task(datasets_task.id)


class MigrateProtocolIo(ProcessActionStrategy):
    def execute(self, datasets_task):
        task_setup = datasets_task.task_setup
        task_id = task_setup['task_id']
        if task_id:
            clean_task = DatasetsTask.query.filter_by(id=task_id).first()
            if clean_task:
                doi_list = clean_task.result_detail['success_list']
                task_setup['doi_list'] = doi_list
        publish_protocol_io(datasets_task.id, datasets_task.task_setup)
        task_service.end_task(datasets_task.id)


class MigrateFigureProtocolIo(ProcessActionStrategy):
    def execute(self, datasets_task):
        task_setup = datasets_task.task_setup
        task_id = task_setup['task_id']
        if task_id:
            clean_task = DatasetsTask.query.filter_by(id=task_id).first()
            if clean_task:
                doi_list = clean_task.result_detail['success_list']
                task_setup['doi_list'] = doi_list
        update_protocol_io_figure_list(datasets_task.id, datasets_task.task_setup)
        task_service.end_task(datasets_task.id)


class ProtocolIoProcessor:
    @staticmethod
    def execute(datasets_task):
        STRATEGIES = {
            "clean": CleanProtocolIo(),
            "crawl": CrawlProtocolIo(),
            "migrate": MigrateProtocolIo(),
            "migrate_pic": MigrateFigureProtocolIo(),
        }
        context = ProcessActionContext()

        # 使用字典获取策略
        context.strategy = STRATEGIES.get(datasets_task.type)

        context.perform_action(datasets_task)