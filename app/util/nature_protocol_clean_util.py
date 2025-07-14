import json
import logging
from urllib.parse import urlparse, unquote

import html2text
import requests
from bs4 import BeautifulSoup


from app.util.text_deal import get_file_extension, get_replace_resource, MyHTML2Text, get_absoluted_url_html
from app.util.time_deal import get_timestamp2
from app.util.url_util import is_html_link, is_relative_path

logger=logging.getLogger(__name__)
def get_paper_info_by_html(soup):


    script = soup.find('script', {'type': 'application/ld+json'})

    data = json.loads(script.text)
    result = dict()
    # 提取信息
    isPartOf = data['mainEntity']['isPartOf']
    result['volume']=None
    if 'volumeNumber' in dict(isPartOf).keys():

        volume = isPartOf['volumeNumber']

        result['volume']=volume
    author_list=[]

    for author in data['mainEntity']['author']:
        author_object=dict()
        name=author['name']
        author_object['name'] = name
        if 'email' in dict(author).keys():
            email=author['email']
            author_object['email'] = email
        orc_list=[]
        if 'affiliation' in dict(author).keys():
            for orc in author['affiliation']:
                orc_list.append(orc['name'])
        else:
            if author['@type'] == 'Person':
                orc_list.append(author['name'])
        author_object['institution'] = orc_list

        author_list.append(author_object)


    result['author_list'] = author_list
    return result


def get_ref_txt_by_html(soup):


    ref_list = soup.find_all('li', class_='c-article-references__item js-c-reading-companion-references-item')
    # 解析HTML
    data=[]
    for e in ref_list:
        ref=dict()
        sub_soup = BeautifulSoup(str(e), 'html.parser')

        # 寻找包含DOI数据的'a'标签
        doi_a_tag = sub_soup.find('a', attrs={'data-doi': True})
        text_tag = sub_soup.find('p', class_='c-article-references__text')

        # 提取DOI值 uri doi authors volume issue pages title
        if doi_a_tag:
            ref['doi']=doi_a_tag['data-doi']
            uri=unquote (doi_a_tag['href'])
            ref['uri'] = [uri]
        if text_tag:
            ref['ref_text']=text_tag.text
        if ref:
            data.append(ref)

    return data


def get_relate_txt_by_html(soup):


    relate_list = soup.find_all('a', class_='c-article-recommendations-card__link')
    # 解析HTML
    data=[]
    for a_tag in relate_list:
        relate=dict()
        relate['title']=a_tag.text
        relate['uri']=a_tag.attrs['href']
        if 'data-track-label' in a_tag:
            relate['doi']=a_tag.attrs['data-track-label']

        data.append(relate)

    return data


def get_issue_by_html(soup):
    citation_issue = soup.find('meta', attrs={'name': 'citation_issue'})
    if citation_issue:
        return citation_issue['content'].strip()
    else:
        return None


def get_abstract_by_html(soup):
    abstract = soup.find('div', class_='c-article-section__content',id='Abs1-content')
    if abstract:
        return abstract.text
    else:
        return None

def get_key_points_by_html(soup):
    key_points = soup.find('div', class_='c-article-section__content',id='Abs2-content')
    key_points=BeautifulSoup(str(key_points),'html.parser')
    lis=key_points.find_all('li')
    key_points=[]
    for li in lis:
        key_points.append(li.text)

    return key_points

def get_clean_content_by_html(soup,resources):
    supplementary_div = soup.find('section', attrs={'data-title':'Supplementary information'})
    supporting_div = soup.find('section', attrs={'data-title':'Supporting information'})
    extend_data_div = soup.find('section', attrs={'data-title':'Extended data'})
    h = MyHTML2Text()
    h.body_width = 0  # 不进行换行
    h.ignore_links = False  # 不忽略链接
    h.ignore_images = False  # 不忽略图片
    data = dict()
    base_url='https://www.nature.com'
    if supplementary_div:
        supplementary_div=get_absoluted_url_html(str(supplementary_div),base_url)
        sub_soup = BeautifulSoup(str(supplementary_div), 'html.parser')
        h2 = sub_soup.find('h2')
        h2.replaceWith('')
        supplementary_markdown = h.handle(data=str(sub_soup))
        supplementary_markdown = get_replace_resource(resources, supplementary_markdown)


        data['supplementaryInformation'] = str(supplementary_markdown)

    if supporting_div:
        supporting_div = get_absoluted_url_html(str(supporting_div),base_url)
        sub_soup = BeautifulSoup(str(supporting_div), 'html.parser')
        h2 = sub_soup.find('h2')
        h2.replaceWith('')
        supporting_markdown = h.handle(data=str(sub_soup))
        supporting_markdown = get_replace_resource(resources, supporting_markdown)

        data['supportingInformation'] = str(supporting_markdown)

    if extend_data_div:
        extend_data_div = get_absoluted_url_html(str(extend_data_div),base_url)
        sub_soup = BeautifulSoup(str(extend_data_div), 'html.parser')
        h2 = sub_soup.find('h2')
        h2.replaceWith('')
        extend_data_markdown = h.handle(data=str(sub_soup))
        extend_data_markdown = get_replace_resource(resources, extend_data_markdown)
        data['extendedData'] = str(extend_data_markdown)


    return data








