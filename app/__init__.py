
import logging


from flask import Flask
import os

from flask_migrate import Migrate

from app.routes.current_local_deal import current_deal
from extensions import ext_redis

from app.config.config import Config, get_env


from app.models.crawl_data import ProtocolIoResources, OriginalDataProtocolIO


from app.routes.task.task import task

from app.util.current_protocol_crawl_util import crewel_one_text_v2, read_entries, crewel_one_text
from app.util.download import download_video, download_file, get_http_data
from app.util.oss_util import upload_file
from app.util.protocol_io_util import get_resource_attrs, get_pdf_attrs, get_uri_from_interface_steps, \
    get_all_uri_from_interface_steps
from app.util.text_deal import get_file_extension, content_split, read_strings_from_file, write_strings_to_file
from app.config.logging_config import setup_logging

from extensions.ext_database import db


OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')


logger = logging.getLogger(__name__)

migrate = Migrate()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config())
    db.init_app(app)

    ext_redis.init_app(app)
    # 配置日志
    # configure_logging(app)
    migrate.init_app(app, db)
    setup_logging()
    app.register_blueprint(current_deal)
    app.register_blueprint(task)

    return app




