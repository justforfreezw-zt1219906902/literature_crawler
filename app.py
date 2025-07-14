import json

import time

from flask import request



from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait



from app.config.config import Config, get_env

import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from app.models.crawl_data import ProtocolIoResources, OriginalDataProtocolIO, OriginalDataNatureProtocol
from app.models.task import DatasetsTask
from app.service import task_service

from app.util.current_protocol_crawl_util import crewel_one_text_v2, read_entries, crewel_one_text
from app.util.download import download_video, download_file, get_http_data
from app.util.oss_util import upload_file
from app.util.protocol_io_util import get_resource_attrs, get_pdf_attrs, get_uri_from_interface_steps, \
    get_all_uri_from_interface_steps
from app.util.text_deal import get_file_extension, content_split, read_strings_from_file, write_strings_to_file, \
    decompress_string_to_html

from app.routes.current_local_deal import *


from extensions.ext_database import db
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
from app import create_app

OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')



app = create_app()
logger = logging.getLogger(__name__)

if app.config['TESTING']:
    logger.info("App is running in TESTING mode")
initialized = False

env=os.getenv('ENV','dev')
@app.route('/ping')
def ping():
    return 'pong'

@app.route('/test/get_decode_html')
def get_decode_html():
    doi='10.1038/s41596-024-01062-3'
    get_originaldata = OriginalDataNatureProtocol.query.filter_by(doi=doi).first()
    html=decompress_string_to_html(get_originaldata.content)
    return html

# with app.app_context():
#     logger.info(f'current env is {env}')
#     datasets_task_list = DatasetsTask.query.filter(DatasetsTask.status=='progress').all()
#     for task in datasets_task_list:
#         task_service.start_task(task)


# @app.route('/test/get_current_protocol_html')
# def get_current_protocol_html():
#     try:
#         list = read_entries('./app/static/current_protocol/Bioinformatics_2.txt')
#         session = db.session
#         i = 0
#         category_name='Bioinformatics'
#         # crewel_one_text(list, 'Bioinformatics')
#         for data in list:
#             try:
#                 doi = str(data.get('DO')).split('doi.org/')[1]
#                 meta_data = OriginalDataCurrentProtocol(doi=doi, uri=data.get('UR'), title=data.get('TI')
#                                                         , volume=data.get('VL'), issue=data.get('IS'), keywords=data.get('KW'),category_name=category_name)
#                 logger.info(f'this is index {i} data')
#                 i = i + 1
#                 logger.info(f'start to crawl doi is {doi}')
#
#                 # 访问目标网址
#                 url = f'https://doi.org/{doi}'  # 替换为目标文件的 URL
#                 # driver = uc.Chrome();
#                 driver = get_driver('./', False)
#                 driver.get(url)
#                 element = WebDriverWait(driver, 1000).until(
#                     EC.presence_of_element_located((By.CLASS_NAME,
#                                                     'article__body '))
#                 )
#                 content = driver.page_source
#                 is_click_cited = True
#                 original_soup = BeautifulSoup(content, 'html.parser')
#
#                 equation = original_soup.find_all('span', class_='fallback__mathEquation')
#                 logger.info(f'doi {doi} has {len(equation)} equation')
#                 cited_literature = original_soup.find('section',
#                                                       class_='article-section article-section__citedBy cited-by')
#                 if not cited_literature:
#                     is_click_cited = False
#                 logger.info(f'is doi {doi} has cited:{cited_literature}')
#                 # 滚动页面到底部
#
#                 time.sleep(3)
#
#                 total_height = int(driver.execute_script("return document.body.scrollHeight"))
#                 total_height = total_height - 1200
#                 driver.execute_script(f"window.scrollTo(0, {total_height});")
#                 if is_click_cited:
#                     literature_cited_element = WebDriverWait(driver, 1000).until(
#                         EC.presence_of_element_located((By.XPATH,
#                                                         '//*[@id="cited-by"]'))
#                     )
#
#                     # 模拟点击元素
#                     # driver.execute_script("arguments[0].click();", literature_cited_element)
#                     # driver.execute_script("arguments[0].scrollIntoView();", literature_cited_element)
#                     literature_cited_element.click()
#                     time.sleep(3)
#                     element = WebDriverWait(driver, 1000).until(
#                         EC.presence_of_element_located((By.CLASS_NAME,
#                                                         'citedByEntry'))
#                     )
#                     driver.execute_script("return document.body.scrollHeight")
#                     logger.info(f'is doi {doi} finish cited js loaded')
#                 # literature_cited_element.click()
#                 if len(equation)!=0:
#                     load_annotations(driver, len(equation))
#                     new_count = len(driver.find_elements(By.TAG_NAME, 'annotation'))
#
#                     if new_count == 0:
#
#                         print(f'fail to crawl doi,doi not have equation,doi is {doi} continue to update')
#                 else:
#                     load_drivger(driver)
#                 logger.info(f'is doi {doi} finish load_source_html')
#
#                 soup = BeautifulSoup(driver.page_source, 'html.parser')
#
#                 text = soup.find(class_='page-body pagefulltext')
#                 meta_data.content = str(text)
#                 session.commit()
#                 driver.quit()
#
#             except Exception as e:
#                 logger.error(f'error is {e}')
#                 raise e
#
#                 continue
#
#
#     finally:
#
#         session.close()



if __name__ == '__main__':
    # before_request()
    with app.app_context():
        logger.info(f'current env is {env}')
        datasets_task_list = DatasetsTask.query.filter(DatasetsTask.status == 'progress').all()
        for task in datasets_task_list:
            task_service.start_task(task)
    app.run(host='0.0.0.0', port=9001)
