import logging
import time

from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC

from app.routes.current_local_deal import load_annotations, load_drivger
from app.util.current_protocol_crawl_util import get_driver
from selenium.webdriver.common.by import By
logger = logging.getLogger(__name__)
try:
    doi='10.1002/cpz1.217'

    logger.info(f'start to crawl doi is {doi}')

    # 访问目标网址
    url = f'https://doi.org/{doi}'  # 替换为目标文件的 URL
    # driver = uc.Chrome();
    driver = get_driver('', True)
    driver.get(url)
    element = WebDriverWait(driver, 1000).until(
        EC.presence_of_element_located((By.CLASS_NAME,
                                        'article__body '))
    )
    content = driver.page_source
    is_click_cited = True
    original_soup = BeautifulSoup(content, 'html.parser')

    equation = original_soup.find_all('span', class_='fallback__mathEquation')
    logger.info(f'doi {doi} has {len(equation)} equation')
    cited_literature = original_soup.find('section',
                                          class_='article-section article-section__citedBy cited-by')
    if not cited_literature:
        is_click_cited = False
    logger.info(f'is doi {doi} has cited:{cited_literature}')
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
        logger.info(f'is doi {doi} finish cited js loaded')
    # literature_cited_element.click()
    if len(equation) != 0:
        load_annotations(driver, len(equation))
        new_count = len(driver.find_elements(By.TAG_NAME, 'annotation'))

        if new_count == 0:
            logger.error(f'fail to crawl doi,doi not have equation,doi is {doi} continue to update')
    else:
        load_drivger(driver)
    logger.info(f'is doi {doi} finish load_source_html')

    soup = BeautifulSoup(driver.page_source, 'html.parser')


finally:
    logger.error(f'doi is {doi} finish')
