import os
import time
from random import random

from bs4 import BeautifulSoup
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from undetected_chromedriver import ChromeOptions

from extensions.ext_database import db
from app.models.crawl_data import OriginalDataCurrentProtocol, CurrentProtocolResources
from app.util.oss_util import upload_file
from app.util.pic_back_deal import remove_black_border
from app.util.text_deal import content_split, get_file_extension

import undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

LOG_FILE=os.getenv('LOG_FILE')
def crewel_one_text_v2(list, category_name):
    meta_data_list = OriginalDataCurrentProtocol.query.filter_by().all()
    doi_list = [e.doi for e in meta_data_list]

    # 初始化 WebDriver
    session = db.session
    if list:
        for e in list:

            doi = str(e.get('DO')).split('doi.org/')[1]


            if doi in doi_list:
                continue

            driver = uc.Chrome()
            driver.set_script_timeout(100)
            meta_data = OriginalDataCurrentProtocol(doi=doi, uri=e.get('UR'), title=e.get('TI')
                                                    , volume=e.get('VL'), issue=e.get('IS'), keywords=e.get('KW'))
            driver.get(meta_data.uri)
            try:
                element = WebDriverWait(driver, 1000).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    '//*[@id="pane-pcw-relatedcon"]'))
                )

                # 滚动页面到底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                text = soup.find(class_='page-body pagefulltext')
                content = str(text)

                text1, text2, text3 = content_split(content)

                meta_data.category_name = category_name
                meta_data.content = text1
                meta_data.content1 = text2
                meta_data.content2 = text3
                figure_list = text.find_all('figure', class_='figure')
                i = 0
                resource_list = CurrentProtocolResources.query.filter_by(doi=doi).all()
                resource_original_name_list = [e.original_name for e in resource_list]

                print(f'总共有{len(figure_list)}张图')
                i = 0

                if len(figure_list) > 0:

                    # driver = uc.Chrome()
                    try:
                        for figure in figure_list:
                            figure_a_tag = figure.find('a', {'target': '_blank'})

                            if figure_a_tag:
                                tag = figure_a_tag.find('img')

                                if 'data-lg-src' in str(tag):

                                    if i % 8 == 0 and i != 0:
                                        print(f'这是第{i}张图')
                                        driver.quit()
                                        driver = uc.Chrome()
                                    # driver.set_window_size(1920,1080)
                                    # driver.set_script_timeout(100)  # 设置为 60 秒
                                    uri = 'https://currentprotocols.onlinelibrary.wiley.com' + tag.get('data-lg-src')

                                    name_list = tag.get('data-lg-src').split('/')
                                    name = name_list[len(name_list) - 1]

                                    if str(name) not in resource_original_name_list:
                                        screenshot_path = None
                                        try:
                                            i = i + 1
                                            driver.get(uri)

                                            element = WebDriverWait(driver, 1000).until(
                                                EC.presence_of_element_located((By.XPATH,
                                                                                '/html/body/img'))
                                            )
                                            screenshot_path = os.path.join(os.getcwd(), 'pic',
                                                                           'page_screenshot_undectedxx' + str(
                                                                               i) + '.jpg')
                                            # 确保截图目录存在
                                            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                                            driver.save_screenshot(screenshot_path)
                                            remove_black_border(screenshot_path, screenshot_path)
                                            path = 'literature_test/' + name
                                            resource = CurrentProtocolResources(original_name=name, oss_path=path, uri=uri, doi=doi,
                                                                 type='jpg', source='current_protocol')

                                            if upload_file(path, screenshot_path):
                                                db.session.add(resource)
                                                db.session.commit()
                                        finally:
                                            time.sleep(1)
                                            if screenshot_path:
                                                if os.path.exists(screenshot_path):
                                                    os.remove(screenshot_path)
                    finally:
                        if driver:
                            driver.quit()

                session.add(meta_data)

            finally:
                session.commit()
                driver.quit()
                time.sleep(15)


def crewel_one_text(list, category_name):
    # 启动浏览器驱动器
    driver_path = '/Users/root1/PycharmProjects/practiceProjects/chromedriver'
    service = Service(executable_path=driver_path)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    ]

    meta_data_list = OriginalDataCurrentProtocol.query.filter_by().all()
    doi_list = [e.doi for e in meta_data_list]
    # 创建 ChromeOptions 对象
    options = Options()
    options.add_argument('--headless')
    options.add_experimental_option("detach", True)
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    # 初始化 WebDriver
    session = db.session
    if list:
        for e in list:

            doi = str(e.get('DO')).split('doi.org/')[1]
            print(e)

            if doi in doi_list:
                continue

            driver = webdriver.Chrome(service=service, options=options)
            driver.set_script_timeout(100)
            meta_data = OriginalDataCurrentProtocol(doi=doi, uri=e.get('UR'), title=e.get('TI')
                                                    , volume=e.get('VL'), issue=e.get('IS'), keywords=e.get('KW'))
            driver.get(meta_data.uri)
            try:
                element = WebDriverWait(driver, 1000).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    '//*[@id="pane-pcw-relatedcon"]'))
                )

                # 滚动页面到底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                text = soup.find(class_='page-body pagefulltext')
                img_tags = text.find_all('img')

                if doi in doi_list:
                    print(f'该文章{meta_data.title}有{len(img_tags)}个图片')

                    continue

                content = str(text)

                text1, text2, text3 = content_split(content)

                meta_data.category_name = category_name
                meta_data.content = text1
                meta_data.content1 = text2
                meta_data.content2 = text3

                session.add(meta_data)

            finally:
                session.commit()
                driver.quit()
                time.sleep(15)

def crewel_one_text_undetected_chromedriver(list, category_name):
    meta_data_list = MetaArtcle2.query.filter_by().all()
    doi_list = [e.doi for e in meta_data_list]
    # 创建 ChromeOptions 对象

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    ]
    # 初始化 WebDriver
    session = db.session
    options = uc.ChromeOptions()
    # options.add_argument('--headless')
    # options.add_experimental_option("detach", True)
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    # options.add_argument('User-Agent={0}'.format(ua.chrome))
    driver = uc.Chrome(options=options, headless=True)
    try:

        if list:
            for e in list:

                doi = str(e.get('DO')).split('doi.org/')[1]
                print(e)
                if doi in doi_list:
                    continue

                meta_data = MetaArtcle2(doi=doi, uri=e.get('UR'), title=e.get('TI')
                                        , volume=e.get('VL'), issue=e.get('IS'), key_words=e.get('KW'))
                print(meta_data.uri)

                try:

                    driver.get(meta_data.uri)
                    element = WebDriverWait(driver, 1000).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'page-body pagefulltext'))
                    )

                    # 滚动页面到底部
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    text = soup.find(class_='page-body pagefulltext')

                    content = str(text)

                    if content:
                        text1, text2, text3 = content_split(content)

                        meta_data.category_name = category_name
                        meta_data.content = text1
                        meta_data.content1 = text2
                        meta_data.content2 = text3

                        session.add(meta_data)
                    else:
                        raise ValueError("内容不能为空")

                except ValueError as e:
                    print(e)
                finally:
                    session.commit()
                    time.sleep(20)
    finally:

        driver.quit()
        session.close()


def parse_entry(entry):
    data = {}
    lines = entry.split('\n')
    length = len(lines)
    choose_au_line = []
    choose_kw_line = []
    i = 0
    while i < length:
        line = lines[i]
        if line.startswith(('AU', 'KW')):
            for j in range(i, length):
                line = lines[j]
                if line.startswith(('AU')):
                    choose_au_line.append(line)
                elif line.startswith(('KW')):
                    choose_kw_line.append(line)
                else:
                    i = j
                    break
        i = i + 1

    for line in lines:
        if line.startswith(('TY', 'C7', 'TI', 'JO', 'JA', 'VL', 'IS', 'UR', 'DO', 'SP', 'PY', 'AB')):
            parts = line.split('  - ', 1)
            if len(parts) == 2:
                key, value = parts
                data[key] = value
            else:
                # Handle cases where there is no ' - ' separator, such as the last line 'ER'
                data['ER'] = line

    data['AU'] = [line.split(' - ', 1)[1] for line in choose_au_line]
    data['KW'] = [line.split(' - ', 1)[1] for line in choose_kw_line]
    return data


def read_entries(filename):
    entries = []
    current_entry = ""
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip().startswith('ER'):
                # We've reached the end of an entry
                if current_entry:
                    parsed_entry = parse_entry(current_entry)
                    # Convert the dictionary back to a tuple

                    entries.append(parsed_entry)
                    current_entry = ""  # Reset for the next entry
            else:
                current_entry += line
        # Check if there's a final entry that wasn't caught by the loop
        if current_entry:
            parsed_entry = parse_entry(current_entry)
            entries.append(parsed_entry)
    return entries


def get_all_resource_from_soup(soup):
    resources = []
    a_tags=soup.find_all("a")
    figure_tags=soup.find_all('figure')
    imgs_tags=soup.find_all('img')
    for a in a_tags:
        if 'href' not in str(a):
            continue
        src = a['href']
        permit_list = ['.pdf',  '.dmg', '.mov', '.mp4', '.zip', '.mpg', '.avi',
                       '.xlsx', '.xls', '.xlt', '.ppt','docx','doc']
        permit_flag = False
        for permit in permit_list:
            if permit in src:
                permit_flag = True
                break
        if not permit_flag:
            continue

        if src.startswith('/'):
            src='https://currentprotocols.onlinelibrary.wiley.com'+src
        resources.append(['',src,''])
    filter_img=[]
    for figure in figure_tags:
        img=figure.find('img')
        video=figure.find('a',class_='download-media linkBehavior')
        if img:
            filter_img.append(img.attrs.get('data-lg-src'))
        if video:
            src=video.attrs.get('href')
            if src.startswith('/'):
                src = 'https://currentprotocols.onlinelibrary.wiley.com' + src
            description_tag = figure.find('div', class_='figure__caption-text')
            description=None
            if description_tag:
                description = description_tag.get_text(strip=True)
            resources.append(['', src, description])
    for img in imgs_tags:
        src=img.attrs.get('src')
        if src in filter_img:
            continue
        if src.startswith('/'):
            src='https://currentprotocols.onlinelibrary.wiley.com'+src
        resources.append(['',src,''])

    for resource in resources:
        type = get_file_extension(resource[1])
        if type=='png' or type=='jpg'  :
            if not resource[1].endswith('?download'):
                resource[1]=resource[1]+'?download'
    return resources

def filter_resource_by_original_name(resource_all,name_list):
    filter_resource_list=[]
    for resource in resource_all:
        resource_flag = True
        for name in name_list:
            if name in resource[1]:
                resource_flag=False
                break
        if resource_flag:
            filter_resource_list.append(resource)
    return filter_resource_list



def get_driver(download_path,falg):
    # driver_url=os.getenv('driver_url')
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--disable-gpu')  # 禁用 GPU 加速
    chrome_options.add_argument('--no-sandbox')  # 禁用沙箱模式
    if falg:
        chrome_options.add_argument('--headless')  # 无头模式运行
    chrome_options.add_argument('--disable-dev-shm-usage')  # 解决 Linux 下的权限问题
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
    chrome_options.add_argument('--allow-running-insecure-content')  # 允许运行不安全内容
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 禁用自动化特征
    # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # chrome_options.add_experimental_option('useAutomationExtension', False)
    # chrome_options.add_argument(
    #     f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')  # 设置用户代理
    chrome_options.add_argument("--start-maximized")  # 最大化窗口
    chrome_options.add_argument("--disable-plugins")  # 禁用插件
    # chrome_options.add_argument("--incognito")  # 使用无痕模式
    # 设置 Chrome 的下载偏好
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,  # 不提示保存到桌面
        "download.directory_upgrade": True,

        "plugins.always_open_pdf_externally": True  # PDF 文件下载而不是打开
    }
    chrome_options.add_experimental_option('prefs', prefs)
    # 初始化 undetected_chromedriver
    driver = uc.Chrome(options=chrome_options)
    return driver

def get_selenium_driver(download_path,falg):
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--disable-gpu')  # 禁用 GPU 加速
    chrome_options.add_argument('--no-sandbox')  # 禁用沙箱模式
    if falg:
        chrome_options.add_argument('--headless')  # 无头模式运行
    chrome_options.add_argument('--disable-dev-shm-usage')  # 解决 Linux 下的权限问题
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
    chrome_options.add_argument('--allow-running-insecure-content')  # 允许运行不安全内容
    # 设置 Chrome 的下载偏好
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,  # 不提示保存到桌面
        "download.directory_upgrade": True,

        "plugins.always_open_pdf_externally": True  # PDF 文件下载而不是打开
    }
    chrome_options.add_experimental_option('prefs', prefs)
    # 初始化 undetected_chromedriver
    driver = uc.Chrome(options=chrome_options)
    return driver