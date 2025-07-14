import os
import re
import time
from urllib.parse import unquote

import html2text
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import ChromeOptions

from app.util.text_deal import MyHTML2Text, get_url_from_text, escape_markdown, \
    process_tag_to_md_no_sort,process_tag_to_md_with_sort
from extensions.ext_database import db
from app.models.crawl_data import CurrentProtocolResources
from app.util.oss_util import upload_file
from app.util.pic_back_deal import remove_black_border

from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


def get_reference_from_html(li_texts):
    references = []
    # 打印列表内容
    for text in li_texts:
        singel_ref_soup = BeautifulSoup(str(text), 'html.parser')
        author_tags = singel_ref_soup.find_all(class_='author')

        if author_tags:
            author_list = [e.text for e in author_tags]
        else:
            author_list = None
        title_tag = singel_ref_soup.find(class_='articleTitle')
        if title_tag:
            title = title_tag.text
        else:
            title = None
        page_first_tag = singel_ref_soup.find(class_='pageFirst')
        if page_first_tag:
            page_first_text = page_first_tag.text
        else:
            page_first_text = None

        page_last_tag = singel_ref_soup.find(class_='pageLast')
        if page_last_tag:
            page_last_text = page_last_tag.text
            page_last_text = page_first_text + '-' + page_last_text
        else:
            page_last_text = None

        journal_tag = singel_ref_soup.find('i')
        if journal_tag:
            journal = journal_tag.text
        else:
            journal = None
        volume_tag = singel_ref_soup.find(class_='vol')
        if volume_tag:
            volume = volume_tag.text
        else:
            volume = None
        issue_tag = singel_ref_soup.find(class_='citedIssue')
        if issue_tag:
            issue = issue_tag.text
        else:
            issue = None

        uri_tag_list = singel_ref_soup.find_all('a')

        uri_list = []
        for uri_tag in uri_tag_list:
            if 'google' in str(uri_tag):
                uri = uri_tag.get('href')
                if 'doiOfLink' in uri:
                    doi = uri.split('doiOfLink=')[1].split('&')[0]
                else:
                    doi = singel_ref_soup.find(class_='hidden data-doi').text
                doi = unquote(doi)

            elif 'CAS' in str(uri_tag):
                uri = uri_tag.get('href')
                if 'refDoi' in uri:
                    doi = uri.split('refDoi=')[1].split('&')[0]
                else:
                    doi = singel_ref_soup.find(class_='hidden data-doi').text
                doi = unquote(doi)

            elif 'Web of Science' in str(uri_tag):
                uri = uri_tag.get('href')
                if 'doiForPubOfPage' in uri:
                    doi = uri.split('doiForPubOfPage=')[1].split('&')[0]
                else:
                    doi = singel_ref_soup.find(class_='hidden data-doi').text

                doi = unquote(doi)

            elif 'PubMed' in str(uri_tag):
                uri = uri_tag.get('href')
                if 'refOfDoi' in uri:
                    doi = uri.split('refOfDoi=')[1].split('&')[0]
                else:
                    doi = singel_ref_soup.find(class_='hidden data-doi').text
                doi = unquote(doi)


            else:
                uri = uri_tag.get('href')
                if 'doi.org' in uri:
                    doi = uri.split('doi.org/')[1]
                else:
                    doi = None
            if not str(uri).startswith('http'):
                uri = 'https://currentprotocols.onlinelibrary.wiley.com' + uri
            uri_list.append(uri)

        reference = {'authors': author_list, 'title': title, 'journal': journal, 'volume': volume, 'issue': issue,
                     'uri': uri_list, 'doi': doi, 'ref_text': singel_ref_soup.text, 'pages': page_last_text}
        references.append(reference)
    return references


def get_related_from_html(li_texts):
    relateds = []
    # 打印列表内容
    for text in li_texts:
        singel_ref_soup = BeautifulSoup(str(text), 'html.parser')
        uri_p = singel_ref_soup.find('p', {'class': 'creative-work__title'})

        uri_tags = uri_p.find('a')
        uri = uri_tags.get('href')
        doi = uri.split('doi/full/')[1]
        uri = 'https://doi.org/' + doi
        title = uri_tags.text

        author_div = singel_ref_soup.find_all('a', {'class': 'publication_contrib_author'})
        author_list = []
        for e in author_div:
            author = {'name': e.text, 'uri': e.get('href')}
            author_list.append(author)

        journal_div = singel_ref_soup.find('div', {'class': 'parent-item'})
        journal_tag = journal_div.find('a')

        journal = {'name': journal_tag.text, 'uri': journal_tag.get('href')}

        related = {'authors': author_list, 'title': title, 'journal': journal,
                   'uri': uri, 'doi': doi, 'ref_text': singel_ref_soup.text}
        relateds.append(related)
    return relateds


def replace_pattern_in_text(text):
    # 正则表达式匹配"数字/. 空格"的模式
    pattern = r'\d+\\.\s'
    # 替换为"数字."
    replacement = r'\d+.'
    # 使用sub函数执行替换
    list = re.findall(pattern, text)
    print(list)
    for e in list:
        replacement = e.replace(' ', '').replace('\\', '')
        # replacement=e.replace('\\','')
        text = re.sub(e, replacement, text, count=1)
        # 查找 search_string 在 document 中第一次出现的位置
        position = text.find(e)

        # 如果找到了匹配项，则替换它
        if position != -1:
            # 替换第一个匹配项
            text = text[:position] + replacement + text[position + len(e):]
        else:
            # 没有找到匹配项
            text = text
    text = re.sub(r'^\d+\) ', lambda match: match.group(0).rstrip(), text, flags=re.MULTILINE)
    # text=text.replace('---  ','')

    lines = text.splitlines()
    new_text = ''
    # 输出每一行
    for line in lines:
        if line == '---  ':
            line = ''

        new_text = new_text + '\n' + line
    return new_text
    # return text


def replace_resources(result, doi_resources):
    for resource in doi_resources:
        original_path = resource.original_path
        #/action/downloadSupplement?doi=10.1002%2Fcpz1.535&amp;file=cpz1535-sup-0001-TableS1.docx
        replace_url = 'https://static.yanyin.tech/' + resource.oss_path
        original_path = original_path.replace('https://currentprotocols.onlinelibrary.wiley.com','')

        if '?download' in original_path:
            original_path = original_path.replace('?download', '')
        if original_path in result:
            result = result.replace(original_path, replace_url)
        else:
            if 'downloadSupplement?' in original_path:
                name = original_path.split('file=')[-1]
            else:
                name = str(original_path).split('？')[0].split('/')[-1]
            url = get_url_from_text(result, name)
            if url:
                result = result.replace(url, replace_url)
    return result


def get_content_text_by_text(text, doi_resources):
    abstract_soup = BeautifulSoup(text, 'html.parser')

    article_table_contents = abstract_soup.find_all('div', class_='article-table-content')
    support_table_contents = abstract_soup.find_all('div', class_='support-info__table-wrapper article-table-content-wrapper')

    to_preserve = abstract_soup.find_all(['sub', 'sup'])
    ol_type_a_tags = abstract_soup.find_all('ol', {'type': 'a'})
    # all_ul_cp_plain_tags = abstract_soup.find_all('ul', class_='cp-list plain')
    # all_ul_noteList_tags = abstract_soup.find_all('ul', class_='custom-style-list noteList')
    all_ul_plain_list_tags = abstract_soup.find_all('ul', class_='plain-list')
    # all_ul_cp_list_tags = abstract_soup.find_all('ul', class_='cp-list')
    # all_ul_tags = abstract_soup.find_all('ul')

    plain_list_tags = abstract_soup.find_all('ul', class_='plain-list')


    annotation_change = abstract_soup.find_all('p', class_='annotation')
    # all_cp_list = abstract_soup.find_all(class_='cp-list plain')
    # open_figure_list = abstract_soup.find_all(class_='open-figure-link')
    # ppt_figure_list = abstract_soup.find_all(class_='ppt-figure-link')
    # open_search_section = abstract_soup.find_all(class_='article-section article-section__open-research')
    ref_section = abstract_soup.find(class_='article-section article-section__references')
    cited_section = abstract_soup.find(class_='article-section article-section__citedBy cited-by')
    figure_section = abstract_soup.find_all('section', class_='article-section__inline-figure')

    img_list = abstract_soup.find_all('img', alt='InlineGraphics')
    img_equation_inline_tags = abstract_soup.find_all('img', class_='section_image')

    dependent_equation = abstract_soup.find_all('div', class_='inline-equation')
    equation_mjx_container_tags = abstract_soup.find_all('mjx-container', class_='MathJax CtxtMenu_Attached_0')


    # code_tag = abstract_soup.find_all(class_='computerCode')
    table_list = []
    code_list = []
    deal_section(ref_section)
    deal_section(cited_section)
    a_tags = abstract_soup.find_all('a')

    for article_table_content in article_table_contents:
        article_table_content_sub = BeautifulSoup(str(article_table_content), 'html.parser')
        computer_code = article_table_content_sub.find('div', class_='computerCode')
        if computer_code:
            code_list.append(article_table_content)
        else:
            table_list.append(article_table_content)

    # 创建一个字典，用于存储和恢复占位符
    preserve_placeholders = {}
    img_equation_placeholders = {}
    dependent_equation_placeholders = {}
    inline_equation_placeholders = {}
    annotation_placeholders = {}
    img_placeholders = {}
    table_placeholders = {}
    figure_placeholders = {}
    inline_img_placeholders = {}
    code_placeholders = {}
    equation_mjx_container_placeholders = {}




    filter_img_list=[]
    for tag in to_preserve:
        placeholder = f'__PLACEHOLDER_{id(tag)}__'
        if 'sub' in str(tag):
            preserve_placeholders[placeholder] = f'<sub>{tag.text}</sub>'
        elif 'sup' in str(tag):
            preserve_placeholders[placeholder] = f'<sup>{tag.text}</sup>'
        tag.replaceWith(placeholder)
    mjx_container_filter_list=[]

    for equation in dependent_equation:
        placeholder = f'__PLACEHOLDER_{id(equation)}__'
        equation_soup = BeautifulSoup(str(equation), 'html.parser')
        equation_tag = equation_soup.find('annotation', attrs={'encoding': 'application/x-tex'})
        mjx_container_tag = equation_soup.find('mjx-container',  class_='MathJax CtxtMenu_Attached_0')
        mjx_container_filter_list.append(mjx_container_tag)
        if equation_tag:
            equation_text = equation_tag.text
            equation_text = f'\n{equation_text}\n'
            # equation_text=re.sub(r'\\begin{equation\*?}','',equation_text)
            # equation_text=re.sub(r'\\end{equation\*?}','',equation_text)
            # equation_text=equation_text.replace('$$','\n$$\n')
            # dependent_equation_placeholders[placeholder]=equation_text
            equation_text=equation_text.replace('&gt;', '<').replace('&lt;', '>')
            equation.replace_with(equation_text)
        else:
            img_equation = equation_soup.find('img')
            if img_equation:
                filter_img_list.append(img_equation)
                img_equation_placeholders[placeholder] = str(img_equation)
                equation.replaceWith(placeholder)
    for mjx_equation in equation_mjx_container_tags:
        if mjx_equation in mjx_container_filter_list:
            continue
        equation_soup = BeautifulSoup(str(mjx_equation), 'html.parser')
        equation_tag = equation_soup.find('annotation', attrs={'encoding': 'application/x-tex'})
        if equation_tag:
            equation_text = equation_tag.text.replace('&gt;', '<').replace('&lt;', '>')
            mjx_equation.replace_with(equation_text)



    for a_tag in a_tags:
        if not a_tag:
            continue
        if not a_tag.has_attr('href'):
            continue
        if a_tag.attrs['href'].startswith('#'):
            a_tag.replaceWith(a_tag.text)
    # 处理为video和img标签
    for figure in figure_section:
        placeholder = f'__PLACEHOLDER_{id(figure)}__'
        img = figure.find('img')
        video = figure.find('a', class_='download-media linkBehavior')
        if img:
            url = img.attrs.get('data-lg-src')
            alt = img.attrs.get('alt')
            title = figure.find('div', class_='figure__caption figure__caption-text').text.strip()
            img_text = f'\n<img src="{url}" alt="{title}"  loading="lazy" title="{alt}"/>\n'
            figure_placeholders[placeholder] = img_text
        if video:
            src = video.attrs.get('href')

            description_tag = figure.find('div', class_='figure__caption-text')
            if description_tag:
                description = description_tag.get_text(strip=True)
                video_text = f'\n<video src="{src}" controls muted title="{description}"/>\n'
            else:
                video_text = f'\n<video src="{src}" controls muted title=""/>\n'
            figure_placeholders[placeholder] = video_text
        figure.replaceWith(placeholder)

    for code_tag_section in code_list:
        placeholder = f'__PLACEHOLDER_{id(code_tag_section)}__'
        code_tag_section_soup = BeautifulSoup(str(code_tag_section), 'html.parser')
        ul_tags = code_tag_section_soup.find('ul', class_='custom rlist')
        ul_tags_soup = BeautifulSoup(str(ul_tags), 'html.parser')
        li_tags = ul_tags_soup.find_all('li')
        result = ''
        for li_tag in li_tags:
            result = result + '\n' + li_tag.get_text(strip=True)
        code = f'\n\n```\n{result}\n```\n\n'
        code_placeholders[placeholder] = str(code)
        code_tag_section.replaceWith(placeholder)

    for img_tag in img_list:

        placeholder = f'__PLACEHOLDER_{id(img_tag)}__'
        url = img_tag.attrs.get('src')
        alt = img_tag.attrs.get('alt')
        title = img_tag.attrs.get('title')
        filter_img_list.append(img_tag)

        img_text = f'\n\n<img src="{url}" alt="{alt}"  loading="lazy" title="{title}"/>\n\n'

        inline_img_placeholders[placeholder] = img_text
        img_tag.replaceWith(placeholder)
    for img_tag in img_equation_inline_tags:
        if img_tag in filter_img_list:
            continue
        placeholder = f'__PLACEHOLDER_{id(img_tag)}__'
        url = img_tag.attrs.get('src')
        alt = img_tag.attrs.get('alt')
        title = img_tag.attrs.get('title')
        class_ = img_tag.attrs.get('class')
        filter_img_list.append(img_tag)

        img_text = f'\n\n<img src="{url}" alt="{alt}"  loading="lazy" title="{title}" class="{class_}"/>\n\n'

        inline_img_placeholders[placeholder] = img_text
        img_tag.replaceWith(placeholder)

    for tag in table_list:
        placeholder = f'__PLACEHOLDER_{id(tag)}__'
        table_placeholders[placeholder] = str(tag)
        tag.replaceWith(placeholder)
    for tag in support_table_contents:
        placeholder = f'__PLACEHOLDER_{id(tag)}__'
        table_placeholders[placeholder] = str(tag)
        tag.replaceWith(placeholder)
    ul_tags_placeholders = {}
    ol_tags_placeholders = {}
    plain_list_tags_placeholders={}
    for tag in plain_list_tags:
        placeholder = f'__PLACEHOLDER_{id(tag)}'
        result = process_tag_to_md_no_sort(tag, 1, '')
        result = escape_markdown(result)
        plain_list_tags_placeholders[placeholder] = result
        tag.replaceWith(placeholder)
    # for tag in all_ul_tags:
    #     placeholder = f'__PLACEHOLDER_{id(tag)}'
    #     result = process_tag_to_md_no_sort(tag, 1, '')
    #     result = escape_markdown(result)
    #     ul_tags_placeholders[placeholder] = result
    #     tag.replaceWith(placeholder)
    # for tag in all_ul_plain_list_tags:
    #     placeholder = f'__PLACEHOLDER_{id(tag)}'
    #     result = process_tag_to_md_no_sort(tag, 1, '')
    #     result = escape_markdown(result)
    #     all_ul_plain_list_tags_placeholders[placeholder] = result
    #     tag.replaceWith(placeholder)
    # for tag in all_ul_noteList_tags:
    #     placeholder = f'__PLACEHOLDER_{id(tag)}'
    #     result = process_tag_to_md_no_sort(tag, 1, '')
    #     result=escape_markdown(result)
    #     all_ul_noteList_tags_placeholders[placeholder]=result
    #     tag.replaceWith(placeholder)
    # for tag in all_ul_cp_plain_tags:
    #     result=process_tag_to_md_no_sort(tag,1,'')
    #     placeholder = f'__PLACEHOLDER_{hash(tag)}__'
    #     result = escape_markdown(result)
    #     all_ul_cp_plain_tags_placeholders[placeholder] = result
    #     tag.replaceWith(placeholder)
    # for tag in all_ul_cp_list_tags:
    #     result=process_tag_to_md_no_sort(tag,1,'')
    #     placeholder = f'__PLACEHOLDER_{hash(tag)}__'
    #     result = escape_markdown(result)
    #     all_ul_cp_list_tags_placeholders[placeholder] = result
    #     tag.replaceWith(placeholder)

    for tag in ol_type_a_tags:
        result=process_tag_to_md_with_sort(tag,1,'')
        placeholder = f'__PLACEHOLDER_{hash(tag)}__'
        result = escape_markdown(result)
        ol_tags_placeholders[placeholder] = result
        tag.replaceWith(placeholder)

    # 去掉id注解
    annotation_pattern = r'id\s*=\s*"[^"]*"'
    # 使用空字符串替换id属性

    for tag in annotation_change:
        contents = tag.contents
        result = ''
        for content in contents:
            if isinstance(content, str):
                content_text = content
            elif content.name:
                content_text = content.text

            result = result + content_text

        placeholder = f'__PLACEHOLDER_{id(tag)}__'
        result = result.strip()
        type_tag_text = f'\n<Note title="Note" type="info">{result}</Note>\n'

        # annotation_placeholders[placeholder] = re.sub(annotation_pattern, '', str(tag))
        annotation_placeholders[placeholder] = type_tag_text
        tag.replaceWith(placeholder)

    # 去掉图片的data-lg-src属性
    img__pattern = r'data-lg-src\s*=\s*"[^"]*"'

    i = 0

    # for tag in open_figure_list + ppt_figure_list + open_search_section + ref_section:
    #     tag.replaceWith('')

    li_pattern = r"^[a-zA-Z]\."

    # 使用正则表达式检查字符串是否匹配模式

    li_placeholders = {}
    # for cp in all_cp_list:
    #     cp_soup = BeautifulSoup(str(cp), 'html.parser')
    #     all_li = cp_soup.find_all('li')
    #     for li in all_li:
    #         if re.match(li_pattern, li.text):
    #             placeholder = li.text
    #             li_placeholders[placeholder] = f'<abc>' + li.text + '</abc>'
    #             li.replaceWith(placeholder)

    # 将处理后的HTML转换为Markdown
    h = MyHTML2Text()
    h.body_width = 0  # 不进行换行
    h.ignore_links = False  # 不忽略链接
    h.ignore_images = False  # 不忽略图片
    # h.code_sniffer.code_tags.add('div.computerCode')
    markdown = h.handle(str(abstract_soup))
    # 恢复占位符
    markdown = replace_pattern_in_text(markdown)
    for placeholder, original_tag in annotation_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)
    for placeholder, original_tag in ol_tags_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)

    for placeholder, original_tag in plain_list_tags_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)

    for placeholder, original_tag in table_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)
    for placeholder, original_tag in img_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)
    for placeholder, original_tag in code_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)



    for placeholder, original_tag in figure_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)

    for placeholder, original_tag in inline_img_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)


    for placeholder, original_tag in img_equation_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)
    for placeholder, original_tag in inline_equation_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)
    for placeholder, original_tag in dependent_equation_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)
    for placeholder, original_tag in equation_mjx_container_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)
    for placeholder, original_tag in preserve_placeholders.items():
        markdown = markdown.replace(placeholder, original_tag)



    filter_result = replace_resources(markdown, doi_resources)
    return filter_result


def deal_section(ref_section):
    if ref_section:
        ref_li_tags = ref_section.find_all('li')

        for li in ref_li_tags:
            del_div = li.find('div', class_='extra-links getFTR')
            if del_div:
                del_div.decompose()


def is_key_section(tag, name_list):
    node_name = tag.get('class', [])
    for node_class in node_name:
        if node_class in name_list:
            return True
    return False


def get_content_map_by_text(text, doi_resources, abstract_tag):
    # 创建一个有序列表来存储结果
    soup = BeautifulSoup(text, 'html.parser')
    ordered_list = []

    section_all = soup.find('section', class_='article-section article-section__full')

    children = section_all.contents

    len_children = len(children)
    index = 0
    start_index = None
    filter_list = ['article-section__inline-figure']
    while index < len_children:
        node = children[index]
        if start_index:
            if index < start_index - 1:
                index = index + 1
                continue

        if node.name:
            # 如果节点是标签节点
            if node.name == 'section' and not is_key_section(node, filter_list):
                # 将<section>标签字符串化并加入有序列表

                ordered_list.append(str(node))
            elif node.name == 'h2':
                # 收集<h2>标签及其后续内容直到下一个<section>或<h2>标签
                collected_content = []
                start_index = index
                collected_content.append(str(node))
                if start_index + 1 < len_children:
                    next_element = children[start_index + 1]

                    while isinstance(next_element, str):
                        start_index = start_index + 1
                        collected_content.append(next_element)
                        next_element = children[start_index]

                    while (next_element.name not in ['section', 'h2'] or
                           (next_element.name == 'section' and
                            is_key_section(next_element, filter_list))) and start_index < len_children:
                        start_index = start_index + 1
                        collected_content.append(str(next_element))
                        next_element = children[start_index]

                # 将收集的内容字符串化并加入有序列表
                ordered_list.append(''.join(collected_content))

        else:
            # 如果节点是其他类型（如注释）
            print(f"Other Node {index}: {node}")
        index = index + 1
    cited_soup = soup.find('section', class_='article-section article-section__citedBy cited-by')
    if cited_soup:
        ordered_list.append(str(cited_soup))
    print(f"step 1")
    time.sleep(0.1)

    data = dict()

    # 初始化一个空列表来存储最终的结果
    final_list = []

    # 用于记录最后一个包含 <h2> 标签的索引
    last_h2_index = None

    for index, html_text in enumerate(ordered_list):
        # 解析当前的HTML文本
        soup = BeautifulSoup(html_text, 'html.parser')
        key = soup.find('h2')
        # 检查当前文本是否包含 <h2> 标签
        if key:
            # 如果包含 <h2> 标签，则添加到 final_list 中
            final_list.append(html_text)
            last_h2_index = len(final_list) - 1
        else:
            # 如果不包含 <h2> 标签，则合并到最后一个包含 <h2> 标签的元素中
            if last_h2_index is not None:
                final_list[last_h2_index] += html_text

    print(f"step 2")
    data['0_Abstract'] = abstract_tag
    i = 1
    for html_text in final_list:
        sub_soup = BeautifulSoup(html_text, 'html.parser')
        key = sub_soup.find('h2').text
        key = str(i) + '_' + key.strip()
        h2 = sub_soup.find('h2')
        h2.replaceWith('')

        sub_text = get_content_text_by_text(str(sub_soup), doi_resources)

        data[key] = str(sub_text)
        i = i + 1
    print(f"step 3")

    return data


def get_author_by_soup(soup):
    author_list = []
    author_tag = soup.find_all('div', class_='author-info accordion-tabbed__content')
    for e in author_tag:
        author_soup = BeautifulSoup(str(e), 'html.parser')
        name_tag = author_soup.find('p', class_='author-name')
        if name_tag:
            name = name_tag.text
        else:
            name = None
        email_and_orc_tag = author_soup.find_all('a', class_='sm-account__link')
        email = None
        orcid = None

        for h in email_and_orc_tag:
            if 'Link to email address' in str(h):
                if h:
                    email = h.find('span').text
                else:
                    email = None
            elif 'icon-orcid' in str(h):
                if h:
                    orcid = h.find('span').text
                else:
                    orcid = None

        extra = e.text

        author = {'name': name, 'email': email if email else None, 'orcid': orcid if orcid else None, 'extra': extra}
        author_list.append(author)
    return author_list


def get_tre_data(meta_data):
    true_data = dict()

    content = meta_data.content
    soup = BeautifulSoup(content, 'html.parser')
    author_list = get_author_by_soup(soup)
    true_data['author_list'] = author_list
    #
    # text = soup.find(id='pane-pcw-references')
    # print(str(text))
    rlist = soup.find(class_='rlist separator')
    ref_soup = BeautifulSoup(str(rlist), 'html.parser')
    li_tags = ref_soup.find_all('li')
    # 提取 <li> 标签的文本内容，并存储到列表中
    li_texts = [str(li) for li in li_tags]
    references = get_reference_from_html(li_texts)
    true_data['reference'] = references
    rlist = soup.find(class_='show-recommended__content')
    ref_soup = BeautifulSoup(str(rlist), 'html.parser')
    li_tags = ref_soup.find_all('li')
    # 提取 <li> 标签的文本内容，并存储到列表中
    li_texts = [str(li) for li in li_tags]
    relateds = get_related_from_html(li_texts)
    true_data['relates'] = relateds
    abstract_tag = soup.find(class_='article-section article-section__abstract')
    # abstract_tag = html2markdown.convert(str(abstract_tag))
    # 使用BeautifulSoup提取要保留的标签
    doi_resources = CurrentProtocolResources.query.filter_by().filter_by(doi=meta_data.doi)
    original_pdf = next((resource for resource in doi_resources if '/original_pdf/' in resource.oss_path), None)
    h2 = abstract_tag.find('h2')
    h2.replaceWith('')
    abstract_tag = get_content_text_by_text(str(abstract_tag), doi_resources)
    # true_data.abstract_tag = abstract_tag
    true_data['abstract_text'] = abstract_tag
    # content_tag = soup.find(class_='article-section article-section__full')

    content_tag = get_content_map_by_text(str(soup), doi_resources, abstract_tag)
    true_data['content'] = content_tag
    true_data['doi'] = meta_data.doi
    true_data['keywords'] = meta_data.keywords
    true_data['title'] = meta_data.title
    true_data['issue'] = meta_data.issue
    true_data['title'] = meta_data.title
    true_data['volume'] = meta_data.volume
    true_data['publish_date'] = soup.find(class_='epub-date').text
    true_data['file_info'] = {'ossPath': 'https://static.yanyin.tech/' + original_pdf.oss_path, 'md5': original_pdf.md5,
                              'bucket': original_pdf.oss_bucket}
    return true_data
