import logging
from logging.handlers import TimedRotatingFileHandler
import os

# 从环境变量读取全局的 `service` 和 `env`
SERVICE = os.getenv('SERVICE_NAME', 'default_service')
ENV = os.getenv('ENV', 'dev')

# 定义日志文件路径
log_directory = f'/opt/log/stash/{SERVICE}'
log_file_path = os.path.join(log_directory, f'{SERVICE}.log')


def setup_logging():
    """设置日志配置"""

    # 如果日志目录不存在，创建它
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # 定义日志格式
    log_format = (f'{{"@timestamp": "%(asctime)s", "@version": "1", '
                  f'"message": "%(message)s", "logger_name": "%(name)s", '
                  f'"thread_name": "%(threadName)s", "level": "%(levelname)s", '
                  f'"level_value": "%(levelno)s", "service": "{SERVICE}", "env": "{ENV}"}}')

    # 创建一个文件处理器（按小时滚动）
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when='H', interval=1, backupCount=7, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"))

    # 创建一个控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"))

    # 配置根日志记录器
    logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])
