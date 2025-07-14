import json
import logging
import time
import uuid

from bs4 import BeautifulSoup
from flask import current_app
from selenium.webdriver.support.wait import WebDriverWait

from app.routes.current_local_deal import load_annotations, load_drivger
from app.service import count_key, success_count_key, fail_count_key, total_count_key, success_list_key, fail_list_key, \
    crawl_list

from app.util.current_protocol_crawl_util import get_driver, read_entries

from extensions.ext_database import db

from app.models.crawl_data import OriginalDataProtocolIO, ProtocolIoResources, OriginalDataNatureProtocol, \
    NatureProtocolResources, OriginalDataCurrentProtocol

from app.util.redis_util import add_to_array, batch_hash_set, get_array

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from datetime import datetime

from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)


def crawl_current_protocol(task_id, task_setup):
    with current_app.app_context():
        session = db.session
        conflict_strategy = task_setup['conflict_strategy']
        # doi_list = task_setup['doi_list']
        path = './app/static/current_protocol/Bioinformatics_2.txt'
        if not redis_client.exists(f'{crawl_list}{task_id}'):
            list = read_entries(path)
            for item in list:
                add_to_array(f'{crawl_list}{task_id}', json.dumps(item))
        else:
            list =  [json.loads(item.decode()) for item in redis_client.lrange(f'{crawl_list}{task_id}', 0, -1)]
        category_name = path.split('/')[-1].split('_')[0]

        total_records = len(list)
        #  初始化redis count总数
        if not redis_client.exists(f'{count_key}{task_id}'):
            batch_hash_set(f'{count_key}{task_id}',
                           {success_count_key: 0, fail_count_key: 0, total_count_key: total_records}, 360000)
        #  初始化redis 任务执行总数
        logger.info(f'task_id is {task_id},the length of clean list is {total_records}')
        success_list = get_array(f'{success_list_key}{task_id}')
        fail_list = get_array(f'{fail_list_key}{task_id}')

        for data in list:
            data_doi = str(data.get('DO')).split('doi.org/')[1]
            original_data = OriginalDataCurrentProtocol.query.filter_by(doi=data_doi).first()
            if original_data:
                if original_data.id in success_list or original_data.id in fail_list:
                    continue
                if conflict_strategy == 'skip':
                    # redis 执行完一篇文章
                    add_to_array(f'{success_list_key}{task_id}', original_data.id, 3600)
                    redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                    continue
            else:
                original_data = OriginalDataCurrentProtocol(uri=data.get('UR'), title=data.get('TI')
                                                            , volume=data.get('VL'), issue=data.get('IS'),
                                                            keywords=data.get('KW'), category_name=category_name)
                original_data.id=str(uuid.uuid4())
                session.add(original_data)
                session.commit()

            try:

                logger.info(f'start to crawl doi is {data_doi} id is {original_data.id} task_id is {task_id}')

                # 访问目标网址
                url = f'https://doi.org/{data_doi}'  # 替换为目标文件的 URL
                driver = get_driver('./', False)
                driver.get(url)
                element = WebDriverWait(driver, 1000).until(
                    EC.presence_of_element_located((By.CLASS_NAME,
                                                    'article__body '))
                )
                content = driver.page_source
                is_click_cited = True
                original_soup = BeautifulSoup(content, 'html.parser')

                equation = original_soup.find_all('span', class_='fallback__mathEquation')
                logger.info(f'doi {data_doi} has {len(equation)} equation')
                cited_literature = original_soup.find('section',
                                                      class_='article-section article-section__citedBy cited-by')
                if not cited_literature:
                    is_click_cited = False
                logger.info(f'is doi {data_doi} has cited:{is_click_cited}')
                # 滚动页面到底部

                time.sleep(3)

                total_height = int(driver.execute_script("return document.body.scrollHeight"))
                total_height = total_height - 1200
                driver.execute_script(f"window.scrollTo(0, {total_height});")
                if is_click_cited:
                    literature_cited_element = WebDriverWait(driver, 1000).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//*[@id="cited-by"]'))
                    )

                    # 模拟点击元素
                    # driver.execute_script("arguments[0].click();", literature_cited_element)
                    # driver.execute_script("arguments[0].scrollIntoView();", literature_cited_element)
                    literature_cited_element.click()
                    time.sleep(3)
                    element = WebDriverWait(driver, 1000).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'citedByEntry'))
                    )
                    driver.execute_script("return document.body.scrollHeight")
                    logger.info(f'is doi {data_doi} finish cited js loaded')
                # literature_cited_element.click()
                if len(equation) != 0:
                    load_annotations(driver, len(equation))
                    new_count = len(driver.find_elements(By.TAG_NAME, 'annotation'))
                    if new_count == 0:
                        logger.error(f'fail to crawl doi,doi not have equation,doi is {data_doi} continue to update')
                else:
                    load_drivger(driver)
                logger.info(f'doi {data_doi} finish load_source_html')

                soup = BeautifulSoup(driver.page_source, 'html.parser')

                text = soup.find(class_='page-body pagefulltext')
                original_data = OriginalDataCurrentProtocol.query.filter_by(doi=data_doi).first()
                original_data.content = str(text)
                if conflict_strategy == 'update':
                    original_data.update_time = datetime.utcnow()

                session.commit()
                add_to_array(f'{success_list_key}{task_id}', original_data.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                driver.quit()

            except Exception as e:
                logger.error(
                    f'an error occurred,which is {e},doi is {data_doi} , id is {original_data.id},taskId is {task_id}')
                add_to_array(f'{fail_list_key}{task_id}', original_data.id, 3600)
                redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
                # raise e

                continue
        return {'code': 200,
                'msg': 'success'}
