import json
import os
import re
import urllib
from urllib.parse import quote, unquote

import html2text
from bs4 import BeautifulSoup
import json
import os
import zlib
import base64


class MyHTML2Text(html2text.HTML2Text):
    def handle_div(self, attrs):
        # 检查div是否有class="code"属性
        if attrs.get('class_') == 'computerCode':
            return self.handle_pre(attrs)
        else:
            return super().handle_div(attrs)


def content_split(text):
    # 计算分割点
    third_length = len(text) // 3
    remainder = len(text) % 3
    # 分割文本
    part1 = text[:third_length + (1 if remainder > 0 else 0)]
    part2 = text[third_length + (1 if remainder > 0 else 0): 2 * third_length + (1 if remainder > 1 else 0)]
    part3 = text[2 * third_length + (1 if remainder > 1 else 0):]
    return part1, part2, part3


def get_file_extension(file_path):
    _, ext = os.path.splitext(file_path)
    extension = ext[1:]
    extension = unquote(extension)
    if '?' in extension:
        extension = str(extension).split('?')[0]
    return extension


def is_json_serializable(s):
    try:
        # 尝试将字符串解析为 JSON
        result = json.loads(s)
        # 如果解析成功，检查结果是否为字典
        if isinstance(result, dict):
            return True
        else:
            return False
    except json.JSONDecodeError:
        # 如果解析失败，返回 False
        return False


def content_deal(content):
    content = content.replace('\0', '')
    return content


def get_new_text(map, text):
    # 初始化新字符串
    new_s = ''
    # 保存所有需要替换的区间
    ranges = sorted(map.keys(), key=lambda x: x[0])  # 按照起始位置排序
    # 当前索引
    current_index = 0
    # 遍历所有区间
    for start, end in ranges:
        # 添加当前索引到下一个替换区间的前一部分
        new_s += text[current_index:start]
        # 插入替换文本
        new_s += map[(start, end)] if map[(start, end)] else ''
        # 更新当前索引
        current_index = end
    # 添加最后一个替换区间之后的剩余部分
    new_s += text[current_index:]
    return new_s


def get_abc_pattern_result(text):
    # 匹配至少8个空格开头、一个小写字母、一个点以及其他字符串
    pattern = r"(^ {8,})([a-z]\.)(.*)"

    # 使用正则表达式匹配并替换
    def replace_match(match):
        spaces, letter_period, rest = match.groups()
        # 将至少8个空格替换为4个空格
        spaces = "    "
        # 将字母替换为数字
        if letter_period == 'a.':
            letter_period = '1.'
        elif letter_period == 'b.':
            letter_period = '2.'
        elif letter_period == 'c.':
            letter_period = '3.'
        elif letter_period == 'd.':
            letter_period = '4.'
        elif letter_period == 'e.':
            letter_period = '5.'
        elif letter_period == 'f.':
            letter_period = '6.'
        elif letter_period == 'g.':
            letter_period = '7.'
        elif letter_period == 'h.':
            letter_period = '8.'
        elif letter_period == 'i.':
            letter_period = '9.'
        elif letter_period == 'j.':
            letter_period = '10.'
        # 返回替换后的字符串
        return f"{spaces}{letter_period}{rest}"

    # 使用正则表达式进行替换
    new_text = re.sub(pattern, replace_match, text)

    return new_text


def html_to_md(content):
    soup = BeautifulSoup(str(content).strip(), 'html.parser')

    # 处理段落
    replace_text = ''
    if str(soup).startswith('<b>'):
        string = soup.text
        replace_text = '**' + string.strip() + '**'
    else:
        replace_text = soup.text
    replace_text = replace_text.replace('\n', ' ')
    return replace_text


def escape_markdown(text):
    # 定义需要转义的 Markdown 特殊字符
    # special_chars = ['_', '*', '`', '~', '#']
    special_chars = ['#', '~', '$']
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, '\\' + char)
    return escaped_text


def write_strings_to_file(strings, filename):
    with open(filename, 'w') as file:
        for string in strings:
            file.write(str(string) + '\n')


def read_strings_from_file(filename='./app/static/resource_list/protocol_io_no_doi.txt'):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        # 去除每行末尾的换行符
        return [line.strip() for line in lines]
    except FileNotFoundError:
        return []


def read_map_from_file(filename):
    """从文件中读取映射"""
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {}


def write_map_to_file(filename, data):
    """将映射写入文件"""
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


def update_and_save_map(filename, new_data):
    """读取文件中的映射，更新映射，并保存回文件"""
    # 读取现有映射
    existing_map = read_map_from_file(filename)

    # 更新映射
    existing_map.update(new_data)

    # 保存更新后的映射
    write_map_to_file(filename, existing_map)

    return existing_map


def get_url_from_text(text, target_string):
    # 正则表达式模式，用于匹配包含特定字符串的 URL
    pattern = r'https?://[\w.-]+(?:/[\w.-]*)*(?:\?[\w.-]+(?:=[\w%.-]*)?(?:&[\w.-]+=[\w%.-]*)*)?'
    pattern2 = '\/[^?#<>"]+(?:\?[^#<>"]*)?'
    # 查找所有匹配项
    urls = re.findall(pattern, text)

    urls.extend(re.findall(pattern2, text))

    # 输出匹配到的 URL

    for url in urls:
        if target_string in url:
            return str(url)
    return None


def get_url_from_html(html, target_string, prefix):
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html, 'html.parser')
    target_id = target_string.split('-m.')[0]
    if not target_id:
        target_id = target_string.split('.')[0]
    aim_figure_tag = None
    figure_tag_list = soup.find_all('figure')
    for figure_tag in figure_tag_list:
        if target_string in str(figure_tag):
            aim_figure_tag = figure_tag
            break
    if not aim_figure_tag:
        return False
    # 查找包含图片链接的标签
    href = prefix + aim_figure_tag.a['href']
    return href


def get_description_from_html(soup, target_string):
    # 使用BeautifulSoup解析HTML

    target_id = target_string.split('-m.')[0]
    if not target_id:
        target_id = target_string.split('.')[0]
    # 查找包含图片链接的标签
    figure_tag_list = soup.find_all('figure')

    aim_figure_tag = None
    for figure_tag in figure_tag_list:
        if target_string in str(figure_tag):
            aim_figure_tag = figure_tag
            break
    if not aim_figure_tag:
        return False

    sub_soup = BeautifulSoup(str(aim_figure_tag), 'html.parser')

    description = sub_soup.find('div', class_='figure__caption figure__caption-text')

    return description.encode_contents().decode()


text = '''
<section class="article-section__inline-figure">
<figure class="figure" id="cpz1697-fig-0001">
<a href="/cms/asset/bb3df2fb-a85e-4ea2-91d3-5b5f7d02b503/cpz1697-fig-0001-m.jpg" target="_blank">
<picture>
<source media="(min-width: 1650px)" srcset="/cms/asset/bb3df2fb-a85e-4ea2-91d3-5b5f7d02b503/cpz1697-fig-0001-m.jpg"/>
<img alt="Details are in the caption following the image" class="figure__image" data-lg-src="/cms/asset/bb3df2fb-a85e-4ea2-91d3-5b5f7d02b503/cpz1697-fig-0001-m.jpg" loading="lazy" src="/cms/asset/ce1043db-8fd3-4507-8ad8-b26fd271009c/cpz1697-fig-0001-m.png" title="Details are in the caption following the image"/>
</picture>
</a>
<figcaption class="figure__caption">
<div class="figure__caption__header"><strong class="figure__title">Figure 1<span style="font-weight:normal"></span></strong><div class="figure-extra"><a class="open-figure-link" href="#">Open in figure viewer</a><a class="ppt-figure-link" href="/action/downloadFigures?id=cpz1697-fig-0001&amp;partId=&amp;doi=10.1002%2Fcpz1.697"><i aria-hidden="true" class="icon-Icon_Download"></i><span>PowerPoint</span></a></div>
</div>
</figcaption>
</figure>
</section>
'''


# print(get_url_from_html(text, 'cpz1697-fig-0001-m.jpg'))


def natural_sort_key(s):
    def tryint(s):
        try:
            return int(s)
        except ValueError:
            return s

    return [tryint(c) for c in re.split('([0-9]+)', s)]


def compare_natural(a, b):
    return (natural_sort_key(a) > natural_sort_key(b)) - (natural_sort_key(a) < natural_sort_key(b))


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """

    def atoi(text):
        return int(text) if text.isdigit() else text

    return [atoi(c) for c in re.split(r'(\d+)', text)]


def get_replace_resource(resources, section_result):
    if resources:
        seen_names = set()
        resources = list(resource for resource in resources if
                         resource.original_path not in seen_names and not seen_names.add(resource.original_path))
        for resource in resources:
            if resource.oss_path:
                if str(resource.original_path) in str(section_result):
                    section_result = section_result.replace(resource.original_path,
                                                            quote(f'https://static.yanyin.tech/{resource.oss_path}',
                                                                  safe=':/?='))
                else:

                    get_url = get_url_from_text(section_result, resource.original_path.split('?')[0])
                    if not get_url:
                        get_url = resource.original_path
                    section_result = section_result.replace(get_url,
                                                            quote(f'https://static.yanyin.tech/{resource.oss_path}',
                                                                  safe=':/?='))
    return section_result


def compress_html_to_string(html):
    """
    使用 zlib 压缩 HTML 数据，并将其转换为 base64 编码的字符串。

    参数:
    html (str): 需要压缩的 HTML 数据。

    返回:
    str: 压缩后的 HTML 数据，以 base64 编码的字符串形式。
    """
    byte_data = html.encode('utf-8')
    compressed_data = zlib.compress(byte_data)
    compressed_string = base64.b64encode(compressed_data).decode('utf-8')
    return compressed_string


def decompress_string_to_html(compressed_string):
    """
    将 base64 编码的字符串解压为原始的 HTML 数据。

    参数:
    compressed_string (str): 压缩后的 HTML 数据，以 base64 编码的字符串形式。

    返回:
    str: 解压后的 HTML 数据。
    """
    compressed_data = base64.b64decode(compressed_string)
    decompressed_data = zlib.decompress(compressed_data)
    html = decompressed_data.decode('utf-8')
    return html


def get_absoluted_url_html(html_content, base_url):
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 遍历所有的<a>标签
    for a in soup.find_all('a', href=True):
        # 如果href是相对路径，则进行转换
        if not urllib.parse.urlparse(a['href']).netloc:
            a['href'] = urllib.parse.urljoin(base_url, a['href'])

    # 输出修改后的HTML
    return soup.prettify()


def process_tag_to_md(tag, depth=1, text_accumulator=''):
    """
    递归处理 HTML 标签及其子标签，并根据深度添加空格。

    :param tag: 当前处理的 BeautifulSoup Tag 对象
    :param depth: 当前标签的深度，默认为 0
    :param text_accumulator: 用于累积文本的字符串，默认为空字符串
    :return: 返回累积的文本字符串
    """
    # 生成当前深度的缩进
    indent = '&nbsp;' * 4 * depth

    # 如果当前标签内还有子标签，则递归处理子标签
    len_children = 0
    p_len = 0
    children = tag.children
    for child in children:
        # if len_children == 0 and depth=1:
        #     text_accumulator += indent
        if isinstance(child, str):
            # 如果子元素是文本，则直接处理
            stripped_text = child.strip()
            if stripped_text:
                text_accumulator += f"{stripped_text}"
        elif hasattr(child, 'name'):
            # 如果子元素是标签，则递归处理
            if depth == 1:
                text_accumulator += indent
            if child.name == 'p' or depth == 1:
                if child.name == 'p':
                    text_accumulator += indent
                text_accumulator += process_tag_to_md(child, depth + 1, '') + '\n\n'
                p_len = p_len + 1
            else:
                text_accumulator += process_tag_to_md(child, depth + 1, '')
        len_children += 1

    return text_accumulator


def process_tag_to_md_no_sort(tag, depth=1, text_accumulator='', ):
    """
    递归处理 HTML 标签及其子标签，并根据深度添加空格。

    :param tag: 当前处理的 BeautifulSoup Tag 对象
    :param depth: 当前标签的深度，默认为 0
    :param text_accumulator: 用于累积文本的字符串，默认为空字符串
    :return: 返回累积的文本字符串
    """
    # 生成当前深度的缩进
    indent = '&nbsp;' * 4 * depth
    text_accumulator += '\n\n'
    # 如果当前标签内还有子标签，则递归处理子标签
    len_children = 0
    p_len = 0
    children = tag.children
    for child in children:
        # if len_children == 0 and depth=1:
        #     text_accumulator += indent
        if isinstance(child, str):
            # 如果子元素是文本，则直接处理
            stripped_text = child.strip()
            if stripped_text:
                text_accumulator += indent
                text_accumulator += f"{stripped_text}"
        elif hasattr(child, 'name'):
            text_accumulator += indent
            # 如果子元素是标签，则递归处理
            if child.name == 'p' :
                text_accumulator += indent*2
                text_accumulator += f'\n\n{child.text}\n\n'
                p_len = p_len + 1
            elif child.name in  ['span','b','i']  :
                text_accumulator += f'{child.text}'
            elif child.name =='ul' :
                text_accumulator += process_tag_to_md_no_sort(child, depth + 1, '')
            else:
                text_accumulator += f'{child.text}'
        len_children += 1

    return text_accumulator


def process_tag_to_md_with_sort(tag, depth=1, text_accumulator=''):
    """
    递归处理 HTML 标签及其子标签，并根据深度添加空格。

    :param tag: 当前处理的 BeautifulSoup Tag 对象
    :param depth: 当前标签的深度，默认为 0
    :param text_accumulator: 用于累积文本的字符串，默认为空字符串
    :return: 返回累积的文本字符串
    """
    # 生成当前深度的缩进
    indent = '&nbsp;' * 4 * depth

    # 如果当前标签内还有子标签，则递归处理子标签
    len_children = 0
    p_len = 0
    children = tag.children
    for child in children:
        if isinstance(child, str):
            # 如果子元素是文本，则直接处理
            stripped_text = child.strip()
            if not stripped_text:
                continue
        if depth == 1:
            text_accumulator += str(len_children) + '. '
        if isinstance(child, str):
            # 如果子元素是文本，则直接处理
            stripped_text = child.strip()
            if stripped_text:
                text_accumulator += f"{stripped_text}"
        elif hasattr(child, 'name'):
            # 如果子元素是标签，则递归处理

            if child.name == 'p' or depth == 1:
                if child.name == 'p':
                    text_accumulator += indent
                text_accumulator += process_tag_to_md(child, depth + 1, '') + '\n\n'
                p_len = p_len + 1
            else:
                text_accumulator += process_tag_to_md(child, depth + 1, '')
        len_children += 1

    return text_accumulator


# 示例文本
text = """
<ul class="custom-style-list noteList">
            <li><span class="number" style="left:-20px">a.</span>During DNA repair (step 21), use 2 μl PreCR lacking T4 PDG in place of DNA Damage Repair Mix v2.</li>
            <li><span class="number" style="left:-20px">b.</span><p>During DNA ligation (step 24), use 5 μl PacBio Barcoded Adapter instead of Overhang Adapter v3.0.</p>
               
               <p>In this way, each sample (i.e., DNA from each UV exposure level) gets a unique SMRTbell barcoded adapter that allows for sample pooling during PacBio sequencing.</p>
               </li>
         </ul>
"""

text2 = """
<ul class="cp-list plain1">
            <li>Hplacehoder3O, deionized</li>
            <li>Algae COMBO stock solutions (see Table <a class="tableLink scrollableLink" title="Link to table" href="#cpz11064-tbl-0002">2</a> for instructions on making stock solutions) made with:

               <ul class="cp-list plain">
                  <li>CaClplacehoder>·2Hplacehoder>O (Sigma-Aldrich, cat. no. C7902)</li>
                  <li>MgSOplacehoder3·7Hplacehoder>O (Westlab, cat. no. 225-0546)</li>
                  <li>NaHCOplacehoder3 (Sigma Aldrich, cat. no. S6014)</li>
                  <li>Naplacehoder>SiOplacehoder3·5 Hplacehoder>O (Sigma-Aldrich, cat. no. 71746)</li>
                  <li>Hplacehoder3BOplacehoder3 (Fisher Scientific, cat. no. A74-500)</li>
                  <li>Naplacehoder>HPOplacehoder3·Hplacehoder>O (Caldedon, cat. no. 8120-1)</li>
                  <li>(NHplacehoder3)placehoder>SOplacehoder3 (Omnipur, cat. no. 2150)</li>
                  <li>Naplacehoder>EDTA (Sigma-Aldrich, cat. no. E5134)</li>
                  <li>FeClplacehoder3·6Hplacehoder>O (ThermoFisher, cat. no. 217091000)</li>
                  <li>MnSOplacehoder3·Hplacehoder>O (ThermoFisher, cat. no. A17615.36)</li>
                  <li>ZnSOplacehoder3·7Hplacehoder>O (Sigma-Aldrich, cat. no. Z4750)</li>
                  <li>Naplacehoder>MoOplacehoder3·2Hplacehoder>O (ACROS, cat. no. 206375000)</li>
                  <li>CoClplacehoder>·6Hplacehoder>O (Sigma Aldrich, cat. no. 255599)</li>
                  <li>CuSOplacehoder3·5Hplacehoder>O (ThermoFisher, cat. no. 197730010)</li>
                  <li>Vitamin B<sub>12</sub> (Sigma Aldrich, cat. no. V6629)</li>
                  <li>Biotin (Sigma Aldrich, cat. no. B4639)</li>
                  <li>Thiamine (Sigma Aldrich, cat. no. T1270)</li>
               </ul>
            </li>
            <li>0.1 M HCl (Current Protocols, <span><a href="#cpz11064-bib-0005" id="#cpz11064-bib-0005_R_d210113245e980" class="bibLink tab-link" data-tab="pane-pcw-references">2006</a></span>)</li>
            <li>0.1 M NaOH (Current Protocols, <span><a href="#cpz11064-bib-0005" id="#cpz11064-bib-0005_R_d210113245e986" class="bibLink tab-link" data-tab="pane-pcw-references">2006</a></span>)</li>
            <li>
               
               <p>Algal culture of <i>Tetradesmus obliquus</i>.</p>
               
               <p>Pure cultures can be purchased from phycological culture centers, e.g., Canadian Phycological Culture Centre (<a href="https://uwaterloo.ca/canadian-phycological-culture-centre/" class="linkBehavior">https://uwaterloo.ca/canadian-phycological-culture-centre/</a>).</p>
               </li>
            <li>20-L plastic carboys (Fisher Scientific, cat. no. 02-963BB or equivalent)</li>
            <li>Micropipettes (Fisher Scientific, cat. no. 14-559-433)</li>
            <li>pH meter</li>
            <li>125-ml Erlenmeyer flasks for subcultures (Fisher Scientific, cat. no. 10-040D)</li>
            <li>Aluminum foil</li>
            <li>Autoclave</li>
            <li>Fume hood</li>
            <li>Broad spectrum growth lamps (e.g., Sansi PAR30 24W LED Grow Light Bulb)</li>
            <li>2- to 4-L Erlenmeyer flasks (Fisher Scientific, cat. nos. 10-040M and 10-040P)</li>
            <li>Rubber stoppers (Fisher Scientific, cat. no. 14-130P)</li>
            <li>GAquarium air pump (e.g., Tetra Whisper 10)</li>
            <li>Centrifuge</li>
            <li>50-ml plastic graduated cylinder (Fisher Scientific, cat. no. 8-550D)</li>
            <li>1-L plastic bottles (Fisher Scientific, cat. no. 02-896F)</li>
         </ul>
"""
text3 = """
<ol type="a">
            <li>Mix all components necessary to prepare an 8% acrylamide gel (see <a href="#cpz1535-rec-0003">recipe</a>) in a clean 15-ml Falcon tube.</li>
            <li>Transfer the mixture to the corresponding polyacrylamide gel tray and let it solidify at room temperature for 30 min.</li>
            <li>During the waiting time, prepare the DNA ladder and mix all the samples with 6× DNA loading dye.</li>
            <li>Load all the samples and a 50-bp DNA ladder on the gel and run at 180 V for 15–20 min.</li>
            <li>After running, transfer the gel to 1× TBE buffer containing SYBR gold (1:10,000) and stain the gel in the dark for 20 min.</li>
            <li>After staining, check the gel under a gel documentation system and cut each gel lane from 220–1000 bp, using the 50-bp DNA ladder as reference.</li>
            <li>
               
               <p>Make a hole in the center of a 0.5-ml tube with a 21G needle and transfer each cut gel slice into a 0.5-ml punched tube. Place the 0.5-ml punched tube (containing the cut gel slice) inside a 2-ml Eppendorf tube. Then, centrifuge at 16,000 × <i>g</i> for 5 min and discard the 0.5-ml punched tube, leaving the small gel pieces collected in the 2-ml Eppendorf tube.</p>
               
               <p>The aim of this step is to reduce the entire gel slice into small pieces.</p>
               </li>
            <li>
               
               <p>Into each 2-ml tube containing the gel pieces, add 300 μl of crush soak buffer and incubate the mixture at 55°C for 8 hr with 1400 rpm shaking, to dissolve DNA fragments in the buffer.</p>
               
               <p>The aim of this step is to dissolve DNA fragments in the buffer.</p>
               </li>
            <li>After incubation, transfer the gel mixture to Costar spin-X centrifuge tubes and centrifuge for 5 min at 16,000 <i>× g</i>.</li>
            <li>
               
               <p>Collect the solution passing through the filter and use Zymo ChIP DNA Clean and concentrator kit to purify it. Then, elute in 15 μl of elution buffer.</p>
               
               <p>We follow the manufacturer's standard protocol to perform DNA purification. Please refer to the standard protocol from this kit for a detailed procedure.</p>
               </li>
         </ol>
"""
# soup = BeautifulSoup(text2, 'html.parser')
# ul_list = soup.find_all("ul")
# i=0
# for tag in ul_list:
#     if i == 0:
#         text=process_tag_to_md_no_sort(tag, 1, '')
#         print(text)
#     i+=1

# 要匹配的字符串
