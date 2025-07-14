import logging
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


from app.util.text_deal import get_file_extension
from app.util.time_deal import get_timestamp2
from app.util.url_util import is_html_link, is_relative_path

logger=logging.getLogger(__name__)
def get_list_last_page(soup):
    # 查找所有的 <li> 元素
    li_elements = soup.find_all('li', class_='c-pagination__item')
    # 过滤掉无效的 <li> 元素（如省略号）
    valid_li_elements = [li for li in li_elements if 'data-page' in li.attrs and li['data-page'].isdigit()]
    # 提取最后一个有效的 <li> 元素的页码
    last_page = int(valid_li_elements[-1]['data-page'])
    return last_page


def get_page_all_data_list(soup):
    # 查找所有的 <li> 元素
    li_elements = soup.find_all('li', class_='app-article-list-row__item')

    return li_elements



def get_data_from_html(html):
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 查找文章元素

    article = soup.find('article', class_='c-card c-card--flush')
    doi ='10.1038'+ soup.find('a', class_='c-card__link u-link-inherit').attrs['href'].split('/articles')
    print(doi)
    # 提取 title
    title = article.find('h3', class_='c-card__title').get_text(strip=True)

    # 提取 description
    description = article.find('div', {'data-test': 'article-description'}).get_text(strip=True)

    # 提取 c-meta__type
    meta_type = article.find('span', {'class': 'c-meta__type'}).get_text(strip=True)

    # 提取 datePublished
    date_published = article.find('time', itemprop='datePublished')['datetime']
    date_published=get_timestamp2(date_published)

    data={ 'doi':doi, 'title':title, 'article_description':description, 'type':meta_type, 'published_on':date_published}

    return data

def get_data_from_html(html):
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 查找文章元素

    # article = soup.find('article', class_='c-card c-card--flush')
    # article = soup.find('article', class_='u-full-height c-card c-card--flush')
    doi_a = soup.find('a', class_='c-card__link u-link-inherit')
    if not doi_a:
        doi_a=soup.find('a', class_='u-link-inherit')
    doi_postfix=doi_a['href'].split('/articles')[-1]
    doi ='10.1038'+ doi_postfix


    # 提取 title
    title = soup.find('h3', class_='c-card__title').get_text(strip=True)

    # 提取 description
    description_element=soup.find('div', {'data-test': 'article-description'})
    if not description_element:
        description_element=soup.find('div', class_='c-card__summary u-mb-16 u-hide-sm-max')
    description=None
    if description_element:
        description = description_element.get_text(strip=True)

    # 提取 c-meta__type
    meta_type = soup.find('span', {'class': 'c-meta__type'}).get_text(strip=True)

    # 提取 datePublished
    date_published = soup.find('time', itemprop='datePublished')['datetime']
    date_published=get_timestamp2(date_published)

    data={ 'doi':doi, 'title':title, 'article_description':description, 'type':meta_type, 'published_on':date_published}

    return data
def get_all_resource_from_html(html):
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 查找img
    li_elements = soup.find_all('div', class_='c-article-section__figure js-c-reading-companion-figures-item')
    img_elements = soup.find_all('img')
    resource_list=[]
    img_list=[]
    for img_element in li_elements:
        img_resource=get_img_resource_from_element(img_element)
        full_url=replace_substring_between_markers(img_resource[1],"https://media.springernature.com/","/springer-static",'full')
        full_img_resource=[img_resource[0],full_url,img_resource[2],img_resource[3]]
        resource_list.append(img_resource)
        resource_list.append(full_img_resource)
        img_list.append(img_resource)
        img_list.append(full_img_resource)
    #figures里面的图片和全文的图片都要进行爬取
    for img_tag in img_elements:
        data=get_resource_from_img_tag(img_tag,img_list)
        if data:
            resource_list.append(data)
    a_elements = soup.find_all('a')
    for a_element in a_elements:
        src = a_element['href']

        time.sleep(0.01)
        if 'data-track-label' in str(a_element):
            data_track_label = a_element['data-track-label']
            if data_track_label=='link' or data_track_label=='button':
                continue
        permit_list=['.pdf','.png','.jpg','.jpeg','.svg','.dmg','.mov','.mp4','.zip','.gif','.mpg','.avi','.xlsx','.xls','.xlt','.ppt','docx','doc']
        permit_flag=False
        for permit in permit_list:
            if permit  in src:
                permit_flag=True
                break
        if not permit_flag:
            continue

        post_prefix=get_file_extension(src)
        if not post_prefix.strip() or post_prefix == 'com' or '/' in post_prefix or post_prefix == 'plex' or post_prefix == 'html' or post_prefix == 'rss':
            continue
        if is_relative_path(src):
            continue
        a_resource=get_resource_from_a_element(a_element)
        if is_html_link(a_resource[1]):
            continue
        resource_list.append(a_resource)

    return resource_list

def get_img_resource_from_element(img_element):


    # 查找 figure 元素
    figure = img_element.find('figure')

    # 提取 figcaption 中的标题
    description = figure.find('figcaption').text.strip()

    # 提取 img 标签中的 src 属性
    img_src = figure.find('img')['src']

    # 提取 img 标签中的 alt 属性
    img_alt = figure.find('img')['alt']
    if img_src.startswith('//'):
        img_src = 'https:' + img_src

    name=img_src.split('?')[0].split('/')[-1]

    return name, img_src, description,img_alt

def get_resource_from_a_element(a_element):

    # 提取 figcaption 中的标题
    description = a_element.text.strip()

    # 提取 img 标签中的 src 属性
    alt=None
    if 'data-track-label' in str(a_element):
        alt = a_element['data-track-label']

    # 提取 img 标签中的 alt 属性
    src = a_element['href']

    if src.startswith('//'):
        src = 'https:' + src





    name=src.split('?')[0].split('/')[-1]

    return name, src, description,alt

def get_resource_from_img_tag(img_tag,img_list):
    uri = img_tag.get('src')
    alt = img_tag.get('alt')
    class_ = img_tag.get('class')
    if class_ == 'u-visually-hidden':
        return None
    if 'pubads.g.doubleclick.net/gampad/ad' in uri:
        return None
    if '.svg' in uri:
        return None
    if ' data:image/svg+xml;base64' in uri:
        return None
    if is_relative_path(uri):
        return None

    if uri.startswith('//'):
        uri = 'https:' + uri
    for img in img_list:
        if img[1] == uri:
            return None
    name = uri.split('?')[0].split('/')[-1]
    data = [name, uri, None, alt]
    return data


    # try:
    #     response = requests.head(url)
    #     content_type = response.headers.get('Content-Type', '')
    #     if 'text/html' in content_type:
    #         return True
    #     else:
    #         return False
    # except requests.RequestException as e:
    #     return False


def replace_substring_between_markers(original_url, marker_start, marker_end, new_substring):
    """
    替换URL中两个标记之间的子字符串。

    :param original_url: 原始URL字符串
    :param marker_start: 开始标记字符串
    :param marker_end: 结束标记字符串
    :param new_substring: 新的子字符串
    :return: 替换后的URL字符串
    """
    # 找到开始标记的位置
    start_index = original_url.find(marker_start)
    if start_index == -1:
        raise ValueError(f"Marker '{marker_start}' not found in the URL.")

    # 计算开始标记之后的位置
    start_index += len(marker_start)

    # 找到结束标记的位置
    end_index = original_url.find(marker_end, start_index)
    if end_index == -1:
        raise ValueError(f"Marker '{marker_end}' not found in the URL after '{marker_start}'.")

    # 替换标记之间的子字符串
    modified_url = (
            original_url[:start_index] +
            new_substring +
            original_url[end_index:]
    )

    return modified_url





