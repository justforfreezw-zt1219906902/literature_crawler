
from extensions.ext_database import db
from app.models import StringUUID


class TaskRecord(db.Model):
    __tablename__ = 'task_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_type = db.Column(db.String(255))
    is_increment = db.Column(db.Boolean)
    data_source = db.Column(db.String(255))
    crawl_data_record = db.Column(db.JSON)
    task_status = db.Column(db.Integer)
    success_list = db.Column(db.ARRAY(db.String))
    fail_list = db.Column(db.ARRAY(db.String))
    skip_list = db.Column(db.ARRAY(db.String))
    retry_count = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    def __init__(self, task_type=None, is_increment=None, data_source=None,
                 crawl_data_record=None, task_status=None, success_list=None,
                 fail_list=None, skip_list=None, retry_count=None,
                 create_time=None, end_time=None):
        self.task_type = task_type
        self.is_increment = is_increment
        self.data_source = data_source
        self.crawl_data_record = crawl_data_record
        self.task_status = task_status
        self.success_list = success_list
        self.fail_list = fail_list
        self.skip_list = skip_list
        self.retry_count = retry_count
        self.create_time = create_time
        self.end_time = end_time



class CleanMission(db.Model):
    __tablename__ = 'clean_data_record_mission'

    id = db.Column(db.Integer, primary_key=True, index=True)
    status = db.Column(db.Integer, nullable=True)  # 引用列表


class DatasetsTask(db.Model):
    __tablename__ = 'datasets_task'

    id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
    type = db.Column(db.String(255))
    journal_name = db.Column(db.String(255))
    parent_task_id = db.Column(db.String(255))
    status = db.Column(db.String(255))
    failed_reason = db.Column(db.String(1024))

    task_setup = db.Column(db.JSON)
    result_detail = db.Column(db.JSON)
    success_count = db.Column(db.Integer)
    failed_count = db.Column(db.Integer)
    total_count = db.Column(db.Integer)

    create_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    def __init__(self, type=None, journal_name=None,parent_task_id=None,status=None,task_setup=None,
                 result_detail=None, success_count=None,
                 failed_count=None, total_count=None,
                 create_time=None, end_time=None,id=None):
       self.type = type
       self.journal_name = journal_name
       self.parent_task_id = parent_task_id
       self.status = status
       self.task_setup=task_setup
       self.result_detail = result_detail
       self.success_count = success_count
       self.failed_count = failed_count
       self.total_count = total_count
       self.create_time = create_time
       self.end_time = end_time
       self.id = id

    def to_dict(self):
        return {
            "id":self.id,
            "type": self.type,
            "journal_name": self.journal_name,
            "parent_task_id": self.parent_task_id,
            "status": self.status,
            "result_detail": self.result_detail,
            "failed_count": self.failed_count,
            "success_count": self.success_count,
            "total_count": self.total_count,
            "create_time": self.create_time,
            "end_time": self.end_time,
            "task_setup": self.task_setup,
            "failed_reason":self.failed_reason
        }