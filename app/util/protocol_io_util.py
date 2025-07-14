import json
import logging
import re

import bs4

from collections import OrderedDict

from app.util.text_deal import is_json_serializable, content_split, get_new_text, get_abc_pattern_result, html_to_md, \
    escape_markdown, write_strings_to_file, read_strings_from_file, update_and_save_map, content_deal, \
    get_url_from_text, natural_keys, get_replace_resource
from app.util.time_deal import timestamp_year
from urllib.parse import quote

logger=logging.getLogger(__name__)
def get_uri_from_interface_steps(steps,uri,doi):
    downlaod_list=[]
    if steps:
        for step in steps:
            if step['step']:
                step_json = json.loads(step['step'])
                step_json_dict = dict(step_json)
                map_dict = dict(step_json_dict['entityMap'])
                map_values = map_dict.values()
                for map_value in map_values:
                    map_entity = dict(map_value)
                    if map_entity['mutability'] == 'IMMUTABLE' and map_entity['type'] != 'image' and \
                            map_entity[
                                'type'] != 'video':
                        # 还有获取下一级别的资源 如果是iamge video类型则没有下一级别资源
                        map_data = map_entity['data']
                        step_json_dict = dict(map_data)
                        if 'entityMap' in step_json_dict.keys():
                            step_json_dict = step_json_dict.get('entityMap', {})
                            if step_json_dict:
                                map_dict = dict(step_json_dict)
                                map_values = map_dict.values()
                                for map_value in map_values:
                                    next_map_value = dict(map_value)
                                    data = get_resource_attrs(next_map_value,doi)
                                    if data[1]:
                                        downlaod_list.append(data)

                    else:
                        data = get_resource_attrs(map_entity,doi)
                        if data[1]:
                            downlaod_list.append(data)
    normal_uri=str(uri).split('?')[0]
    for downlaod in downlaod_list:
        normal_get_uri=downlaod[1].split('?')[0]
        if normal_uri == normal_get_uri:
            return downlaod[1]
    return ''


def get_all_uri_from_interface_steps(steps,doi):
    downlaod_list=[]
    if steps:
        for step in steps:
            if step['step']:
                step_json = json.loads(step['step'])
                step_json_dict = dict(step_json)
                map_dict = dict(step_json_dict['entityMap'])
                map_values = map_dict.values()
                for map_value in map_values:
                    map_entity = dict(map_value)
                    if map_entity['mutability'] == 'IMMUTABLE' and map_entity['type'] != 'image' and \
                            map_entity[
                                'type'] != 'video':
                        # 还有获取下一级别的资源 如果是iamge video类型则没有下一级别资源
                        map_data = map_entity['data']
                        step_json_dict = dict(map_data)
                        if 'entityMap' in step_json_dict.keys():
                            step_json_dict = step_json_dict.get('entityMap', {})
                            if step_json_dict:
                                map_dict = dict(step_json_dict)
                                map_values = map_dict.values()
                                for map_value in map_values:
                                    next_map_value = dict(map_value)
                                    data = get_resource_attrs(next_map_value,doi)
                                    if data[1]:
                                        downlaod_list.append(data)

                    else:
                        data = get_resource_attrs(map_entity,doi)
                        if data[1]:
                            downlaod_list.append(data)
    url_list=[]
    if downlaod_list:
       for downlaod in downlaod_list:
           url_list.append(downlaod[1])

    return url_list
def get_resource_attrs(map_entity,doi):
    original_name = None
    uri = None
    type = None
    map_data = map_entity['data']
    map_type = map_entity['type']
    if isinstance(map_data, dict):
        data = dict(map_data)
        if map_type == 'image':
            original_name = data['original_name']
            uri = data['source']
            type = data['mime']
        elif map_type == 'video':

            original_name = data['original_name']
            uri = data['source']
            type = data['mime']
        elif map_type == 'file':

            original_name = data['original_name']
            uri = data['source']
            type = ''
        elif map_type == 'imageblock':

            original_name = ''
            uri = data['source']
            type = ''
        elif map_type == 'spectral':

            original_name = ''
            uri = data['source']
            type = ''
        elif map_type == 'link':

            # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
            read_strings = read_strings_from_file('./app/static/resource_list/protocol_link_extra_type.txt')
            read_strings.extend([data])

            # 再次写入文件
            write_strings_to_file(read_strings, './app/static/resource_list/protocol_link_extra_type.txt')

        elif map_type in ['duration', 'amount', 'notes', 'safety', 'temperature', 'centrifuge',
                          'shaker', 'equipment', 'protocols', 'tables', 'reagents', 'citation',
                          'concentration','dataset','software','code_insert','gotostep','thickness','tex_formula','result',
                          'imageblock','centrifugation','ph','command','geographic','cost','pressure','embed','humidity','smart_component','sample'
                        'spectral','emoji']:
            print('skip map type')
        else:
            data['doi']=doi
            get_data={map_type:data}
            # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
            update_and_save_map('./app/static/resource_list/protocol_link_extra_type_map.txt',get_data)
            print(f'extra skip map type is {map_type}')


    return original_name, uri, type


def get_documents_attrs(document):
    if document['ofn']:
        name = document['ofn']
    else:
        name = document['filename']
    uri = document['url']
    return name, uri, ''


def get_pdf_attrs(e, doi):
    uri = f'https://www.protocols.io/view/{e}.pdf'

    return doi + '.pdf', uri, ''


def clean_relate_list(original_data):
    relate_list = []
    if original_data.documents:
        for document in original_data.documents:
            url = document['url']
            relate_json = {'uri': url}
            relate_list.append(relate_json)
    return relate_list


def clean_author_list(original_data):
    author_list = []
    creator = original_data.creator
    if original_data.authors:
        for author in original_data.authors:
            name = author['name']
            institution = author['affiliation']
            # avatar = author['image']['source']
            # author_json = {'name': name, 'institution': institution, 'avatar': avatar,'type':'author'}
            author_json = {'name': name, 'institution': institution, 'type': 'author'}
            author_list.append(author_json)
    author = next((author for author in author_list if author['name'] == creator['name']), None)
    if author:
        author['type'] = 'creator'

    return author_list


def clean_ref_list(original_data):
    ref_list = []

    if original_data.protocol_references:
        if is_json_serializable(original_data.protocol_references):
            reference = json.loads(original_data.protocol_references)
            reference = dict(reference)
            blocks = reference['blocks']
            for block in blocks:
                ref = {'ref_text': block['text']}
                if ref and block['text']:
                    ref_list.append(ref)
    return ref_list


# def get_clean_equipment_text(data):
#     equipment_name = data['name']
#     equipment_type = data['type']
#     equipment_brand = data['brand']
#     equipment_sku = data['sku']
#     equipment_link = data['vendor']['link']
#     equipment_specifications = data['specifications']
#     array = [{'label': 'NAME', 'value': equipment_name}, {'label': 'TYPE', 'value': equipment_type},
#              {'label': 'BRAND', 'value': equipment_brand},
#              {'label': 'SKU', 'value': equipment_sku}, {'label': 'SPECIFICATIONS', 'value': equipment_specifications},
#              {'label': 'LINK', 'link': equipment_link, 'value': equipment_link}]
#     replace_text = f'<Entity type="Equipment"  datasource="{array}" />'
#     return replace_text


# def get_clean_protocol_text(data):
#     protocol_name = data['title']
#     protocol_uri = 'https://www.protocols.io/view/' + data['uri']
#     protocol_image_uri = data['image']['source']
#     author_name = data['creator']['name']
#     author_uri = data['creator']['link']
#     author_image_uri = data['creator']['user_image_file']['url']
#     array = [{'label': 'create by', 'link': author_uri, 'image': author_image_uri, 'value': author_name},
#              {'label': 'title', 'link': protocol_uri, 'image': protocol_image_uri, 'value': protocol_name}]
#     replace_text = f'<Entity type="Protocol"  datasource="{array}" />'
#     return replace_text


def get_clean_tempature_text(data, units):
    amount = data['temperature']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'`{amount}{unit_name}`'
    else:
        replace_text = f'`{amount}`'
    return replace_text


def get_clean_amount_text(data, units):
    amount = data['amount']
    unit_key = data['unit']

    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'`{amount}{unit_name}`'
    else:
        replace_text = f'`{amount}`'
    return replace_text


def get_clean_image_text(data):
    test=''
    if 'legend' in dict(data).keys():
        legend = data['legend']
        if legend:
            legend = json.loads(legend)
            legend = dict(legend)
            test = ''
            if legend['blocks']:
                for block in legend['blocks']:
                    test = test + block['text']

    data_source = data['source']
    if data_source:
        regulate = '尊敬的用户，由于网络监管政策的限制，部分内容暂时无法在本网站直接浏览。我们已经为您准备了相关原始数据和链接，感谢您的理解与支持。'
        if 'googleusercontent' in data_source:
            result = f'\n```\n#{regulate}\n{data_source}\n```\n'
            return  '\n' + result
        elif 'blob:' in data_source:
            return ''

    replace_text = f'<img src="{data_source}" alt="{test}" loading="lazy" title="{test}"/>\n\n'
    return replace_text



def get_clean_spectral_text(data):


    data_source = data['source']
    replace_text = f'<img src="{data_source}" alt="" loading="lazy" title=""/>\n'
    return replace_text

def get_clean_concentration_text(data, units):
    concentration = data['concentration']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)

    if unit:
        unit_name = unit['name']
        replace_text = f'`{concentration}{unit_name}`'
    else:
        replace_text = f'`{concentration}`'
    return replace_text


def get_clean_reagents_text(data):
    data_name = data['name']
    if not data_name:
        return ''
    data_vendor_name = data['vendor']['name']
    replace_text = f'<reagents  text="{data_name}" label="{data_vendor_name}"/>'
    return replace_text


def get_clean_shaker_text(data, units):
    shaker = data['shaker']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'`{shaker}{unit_name}`'
    else:
        replace_text = f'`{shaker}`'

    return replace_text


def get_spell_by_number(number):
    number = number + 1
    return chr(number + 64)


def get_clean_table_text(entity):
    test = ''
    if 'legend' in dict(entity).keys():
        legend = entity['legend']
        if legend:
            for block in legend['blocks']:
                test = test + block['text']
    data = entity['data']
    markdown_table=''
    if data:
        table_length = len(data[0])
        column_data = []
        for i in range(0, table_length):
            column_data.append(get_spell_by_number(i))

        data = [['' if x is None else x for x in sublist] for sublist in data]
        data = [[html_to_md(str(x)) for x in sublist] for sublist in data]
        data.insert(0, column_data)
        # 构建 Markdown 表格
        markdown_table = "| " + " | ".join(data[0]) + " |\n"
        markdown_table += "| " + " | ".join(["---"] * len(data[0])) + " |\n"
        number = 0
        for row in data:
            if number != 0:
                markdown_table += "| " + " | ".join(row) + " |\n"
            number = number + 1
        markdown_table = markdown_table + '\n' + test + '\n'
    return markdown_table


def get_clean_video_text(data):
    data_source = data['source']
    data_name = data['original_name']

    if data_source:
        regulate = '尊敬的用户，由于网络监管政策的限制，部分内容暂时无法在本网站直接浏览。我们已经为您准备了相关原始数据和链接，感谢您的理解与支持。'
        if 'googleusercontent' in data_source:
            result = f'\n```\n#{regulate}\n{data_source}\n```\n'
            return result
        elif 'blob:' in data_source:
            return ''
    replace_text = f'<video  src="{data_source}" text="{data_name}"  controls muted/>'
    return replace_text

def get_new_inlineranges(json_data):
    # 使用map来优化查找
    item_map = {}

    # 遍历列表，按(offset, length)存入字典
    for item in json_data:
        key = (item['offset'], item['length'])
        if key not in item_map:
            item_map[key] = []
        item_map[key].append(item['style'])

    # 构建新的结果列表
    new_items = []

    for key, styles in item_map.items():
        if "bold" in styles and "italic" in styles:
            # 如果同时包含bold和italic，将其转为bold_italic
            new_items.append({"style": "bold_italic", "offset": key[0], "length": key[1]})
        else:
            # 否则保留原始的样式
            for style in styles:
                new_items.append({"style": style, "offset": key[0], "length": key[1]})

    return new_items


def get_md_result_from_blocks(content, result, units, content_type,doi):
    try:
        content = json.loads(content)
    except Exception as e:
        return content
    description = dict(content)
    blocks = description['blocks']
    if description['entityMap']:
        entityMap = dict(description['entityMap'])
    else:
        entityMap = {}
    blocks_length = 0

    for e in blocks:
        text = e['text']
        block_type = e['type']
        map = dict()
        inlineStyleRanges = e['inlineStyleRanges']
        entityRanges = e['entityRanges']
        if inlineStyleRanges:
            inlineStyleRanges=get_new_inlineranges(inlineStyleRanges)
            for inlineStyleRange in inlineStyleRanges:
                stype = inlineStyleRange['style']
                offset = inlineStyleRange['offset']
                length = inlineStyleRange['length']
                string = None
                replace_text = None
                if stype == 'italic':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = ' _' + string.strip() + '_ '
                    else:
                        replace_text =string

                elif stype == 'sup':
                    string = str(text)[offset:offset + length]

                    if string.strip():
                        replace_text = '<sup>' + string.strip() + '</sup>'
                    else:
                        replace_text = string

                elif stype == 'sub':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = '<sub>' + string.strip() + '</sub>'
                    else:
                        replace_text = string
                elif stype == 'bold':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = ' **' + string.strip() + '** '
                    else:
                        replace_text = string
                elif stype == 'UNDERLINE':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = ' _' + string.strip() + '_ '
                    else:
                        replace_text = string
                elif stype == 'bold_italic':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = ' ***' + string.strip() + '*** '
                    else:
                        replace_text = string
                else:
                    print(f'extra style is {stype}')
                if string:
                    map[(offset, offset + length)] = replace_text
        flag = True
        if entityRanges:
            for entityRange in entityRanges:
                key = entityRange['key']
                outsidemap = entityMap.get(str(key), {})
                offset = entityRange['offset']
                length = entityRange['length']
                type = outsidemap['type']
                mutability = outsidemap['mutability']
                data = outsidemap['data']

                if type == 'link':

                    replace_text = get_clean_link_text(data, length, offset, text)
                    map[(offset, offset + length)] = replace_text
                elif type == 'amount':

                    replace_text = get_clean_amount_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'temperature':

                    replace_text = get_clean_tempature_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'duration':

                    replace_text = get_clean_duration_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'protocols':
                    flag = False
                    replace_text = get_clean_protocol_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'equipment':
                    flag = False
                    replace_text = get_clean_equipment_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'software':
                    flag = False
                    replace_text = get_clean_software_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'image':
                    flag = False
                    replace_text = get_clean_image_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'concentration':
                    replace_text = get_clean_concentration_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'reagents':
                    replace_text = get_clean_reagents_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'gotostep':
                    replace_text = get_clean_gotostep_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'video':
                    flag = False
                    replace_text = get_clean_video_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'tables':
                    flag = False
                    replace_text = get_clean_table_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'shaker':
                    replace_text = get_clean_shaker_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'centrifuge':
                    replace_text = get_clean_centrifuge_text(data, units)
                    map[(offset, offset + length)] = replace_text

                elif type == 'safety':
                    flag = False
                    if isinstance(data, str):
                        try:
                            data=json.loads(data)
                            data = dict(data)
                            sub_result = get_safety_content(data, length, offset, text, type, units)

                            map[(
                                offset,
                                offset + length)] = sub_result
                        except Exception as e:
                            sub_result = f'<Note title="Safety" type="warning" >{data}</Note>'
                            map[(offset, offset + length)] = sub_result
                    else:
                        sub_result = get_safety_content(data, length, offset, text, type, units)

                        map[(
                            offset,
                            offset + length)] = sub_result
                elif type == 'notes':
                    flag = False
                    if isinstance(data, str):
                        try:
                            data=json.loads(data)
                            data = dict(data)
                            sub_result = get_note_content(data, length, offset, text, type, units)
                            map[(offset, offset + length)] = sub_result
                        except Exception as e:
                            sub_result = f'<Note title="Note" type="warning" >{data}</Note>'
                            map[(offset, offset + length)] = sub_result
                    else:
                        sub_result = get_note_content(data, length, offset, text, type, units)
                        map[(offset, offset + length)] = sub_result
                elif type == 'result':
                    flag = False
                    if isinstance(data, str):
                        try:
                            data=json.loads(data)
                            data = dict(data)
                            sub_result = get_result_content(data, length, offset, text, type, units)
                            map[(offset, offset + length)] = sub_result
                        except Exception as e:
                            sub_result = f'<Note title="Result" type="warning"  >{data}</Note>'
                            map[(offset, offset + length)] = sub_result
                    else:
                        sub_result = get_result_content(data, length, offset, text, type, units)
                        map[(offset, offset + length)] = sub_result
                elif type == 'citation':
                    flag = False
                    replace_text = get_clean_citation_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'dataset':
                    flag = False
                    replace_text = get_clean_dataset_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'file':
                    flag = False
                    replace_text = get_clean_file_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'geographic':
                    replace_text = get_clean_geographic_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'thickness':
                    replace_text = get_clean_thickness_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'code_insert':
                    flag = False
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_code_text(data, '')
                    map[(offset, offset + length)] = replace_text
                elif type == 'emoji':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_emoji_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'command':
                    flag = False
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_command_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'tex_formula':
                    flag = False
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_tex_formula_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'imageblock':
                    flag = False
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_imageblock_text(data,doi)
                    map[(offset, offset + length)] = replace_text

                elif type == 'centrifugation':
                    replace_text = get_clean_centrifugation_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'ph':
                    replace_text = get_clean_ph_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'cost':
                    replace_text = get_clean_cost_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'pressure':
                    replace_text = get_clean_pressure_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'humidity':
                    replace_text = get_clean_humidity_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'sample':
                    replace_text = get_clean_sample_text(data, units)
                    map[(offset, offset + length)] = replace_text
                elif type == 'spectral':
                    replace_text = get_clean_spectral_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'embed':
                    flag = False
                    replace_text = get_clean_embed_text(data)
                    map[(offset, offset + length)] = replace_text
                elif type == 'well_plate_map':
                    flag = False
                    replace_text = get_clean_well_plate_map_text(data)
                    map[(offset, offset + length)] = replace_text
                else:
                    print(f'extra type is {type}')
        if block_type == 'unstyled' or block_type == 'align-justify':
            text = text.replace('\n', '\n\n')
            text= text+'\n\n'




        # 替换字符串
        if map:
            if (0, len(text)) in map:
                new_s = map[(0, len(text))]
            else:
                # 替换字符串
                new_s = get_new_text(map, text)

                if block_type == 'unstyled' or block_type == 'align-justify':
                    # new_s = text.replace('\n', '\n\n')
                    new_s = new_s + '\n\n'
        else:
            new_s = text
        new_s = new_s if new_s else ''


        new_s = get_abc_pattern_result(new_s)

        order_index = 1
        if blocks_length != 0:
            if flag:
                if new_s:
                    new_s = escape_markdown(new_s)
                    # new_s=new_s+'\\'
                    # new_s = new_s.replace('\n', '\\\n')
            if block_type == 'unordered-list-item':
                new_s = '* ' + new_s.strip()+'\n'
                order_index = 1
            if block_type == 'ordered-list-item':
                new_s = f'{order_index}. ' + new_s.strip()+'\n'
            result = result  + new_s
        else:

            result = result + new_s
        blocks_length = blocks_length + 1
        # if block_type == 'unordered-list-item':
        #     new_s = '\n* ' + new_s
        # else:
        #     new_s = '\n' + new_s
        # result = result + '\n' + new_s
    # result_last = len(result) - 1
    # result = result[:result_last]

    return result


def get_safety_content(data, length, offset, text, type, units):
    sub_blocks = data['blocks']
    if 'entityMap' in data.keys() and data['entityMap']:
        if isinstance(data['entityMap'], list):
            len_map = len(data['entityMap'])
            keys = [str(index) for index in (0, len_map)]
            sub_entityMap = OrderedDict(zip(keys, data['entityMap']))
        else:
            sub_entityMap = dict(data['entityMap'])
    else:
        sub_entityMap = {}
    sub_result = ''
    sub_flag = False
    if sub_entityMap:
        for sub_value in dict(sub_entityMap).values():
            if sub_value['type'] in ['safety', 'citation', 'command']:
                sub_flag = True
                break
    if sub_flag:
        sub_result = get_sub_result(length, offset, sub_blocks, sub_entityMap, sub_result, text, type,
                                    units)
        sub_result = sub_result.replace('\n', '')
        sub_result = f'<Note title="Safety information" type="error" >{sub_result}</Note>'

    else:
        sub_result = get_simple_clean_safety_text(data, units)
    return sub_result


def get_note_content(data, length, offset, text, type, units):
    sub_blocks = data['blocks']
    if 'entityMap' in data.keys() and data['entityMap']:
        if isinstance(data['entityMap'], list):
            len_map = len(data['entityMap'])
            keys = [str(index) for index in (0, len_map)]
            sub_entityMap = OrderedDict(zip(keys, data['entityMap']))
        else:
            sub_entityMap = dict(data['entityMap'])
    else:
        sub_entityMap = {}
    sub_result = ''
    sub_flag = False
    if sub_entityMap:
        for sub_value in dict(sub_entityMap).values():
            if sub_value['type'] in ['safety', 'citation', 'command']:
                sub_flag = True
                break
    if sub_flag:
        sub_result = get_sub_result(length, offset, sub_blocks, sub_entityMap, sub_result, text, type,
                                    units)
        sub_result = sub_result.replace('\n', '')
        sub_result = f'<Note title="Note" type="warning" >{sub_result}</Note>'

    else:
        sub_result = get_simple_clean_notes_text(data, units)
    return sub_result


def get_result_content(data, length, offset, text, type, units):
    sub_blocks = data['blocks']
    if 'entityMap' in data.keys() and data['entityMap']:
        if isinstance(data['entityMap'], list):
            len_map = len(data['entityMap'])
            keys = [str(index) for index in (0, len_map)]
            sub_entityMap = OrderedDict(zip(keys, data['entityMap']))
        else:
            sub_entityMap = dict(data['entityMap'])
    else:
        sub_entityMap = {}
    sub_result = ''
    sub_flag = False
    if sub_entityMap:
        for sub_value in dict(sub_entityMap).values():
            if sub_value['type'] in ['safety', 'citation', 'command']:
                sub_flag = True
                break
    if sub_flag:
        sub_result = get_sub_result(length, offset, sub_blocks, sub_entityMap, sub_result, text, type,
                                    units)
        sub_result = sub_result.replace('\n', '')
        sub_result = f'<Note title="Expected result" type="success" >{sub_result}</Note>'

    else:
        sub_result = get_simple_clean_expected_result_text(data, units)
    return sub_result


def get_sub_result(length, offset, sub_blocks, sub_entityMap, sub_result, text, type, units):

    for f in sub_blocks:
        sub_text = f['text']
        sub_map = dict()
        command_list = []
        embed_list = []
        # sub_entityRanges = f['entityRanges']

        sub_entityRanges = f.get('entityRanges', [])

        sub_inlineStyleRanges = f.get('inlineStyleRanges', [])

        if sub_inlineStyleRanges:
            sub_inlineStyleRanges = get_new_inlineranges(sub_inlineStyleRanges)
            for sub_inlineStyleRange in sub_inlineStyleRanges:
                stype = sub_inlineStyleRange['style']
                offset = sub_inlineStyleRange['offset']
                length = sub_inlineStyleRange['length']
                string = None
                replace_text = None
                if stype == 'italic':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = '<i>' + string.strip() + '</i> '
                    else:
                        replace_text = string

                elif stype == 'sup':
                    string = str(text)[offset:offset + length]

                    if string.strip():
                        replace_text = '<sup>' + string.strip() + '</sup>'
                    else:
                        replace_text = string

                elif stype == 'sub':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = '<sub>' + string.strip() + '</sub>'
                    else:
                        replace_text = string
                elif stype == 'bold':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = '<b>' + string.strip() + '</b> '
                    else:
                        replace_text = string
                elif stype == 'UNDERLINE':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = '<i>' + string.strip() + '</i> '
                    else:
                        replace_text = string
                elif stype == 'bold_italic':
                    string = str(text)[offset:offset + length]
                    if string.strip():
                        replace_text = '<strong><em>' + string.strip() + '</em></strong> '
                    else:
                        replace_text = string
                else:
                    print(f'extra style is {stype}')
                if string:
                    sub_map[(offset, offset + length)] = replace_text

        if sub_entityRanges:
            for sub_entityRange in sub_entityRanges:
                sub_key = sub_entityRange['key']
                sub_outsidemap = sub_entityMap.get(str(sub_key))
                sub_offset = sub_entityRange['offset']
                sub_length = sub_entityRange['length']
                sub_type = sub_outsidemap['type']
                sub_mutability = sub_outsidemap['mutability']
                sub_data = sub_outsidemap['data']

                if sub_type == 'link':
                    replace_text = get_sub_clean_link_text(sub_text)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'amount':

                    replace_text = get_sub_clean_amount_text(sub_data, units)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'temperature':

                    replace_text = get_sub_clean_tempature_text(sub_data, units)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'duration':
                    replace_text = get_sub_clean_duration_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'protocols':
                    replace_text = get_sub_clean_protocol_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text

                elif sub_type == 'image':
                    replace_text = get_clean_image_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'concentration':
                    replace_text = get_sub_clean_concentration_text(sub_data, units)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'reagents':
                    replace_text = get_sub_clean_reagents_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text

                elif sub_type == 'shaker':
                    replace_text = get_sub_clean_shaker_text(sub_data, units)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'geographic':
                    replace_text = get_sub_clean_geographic_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'thickness':
                    replace_text = get_sub_clean_thickness_text(sub_data, units)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'notes':
                    replace_text = get_simple_clean_notes_text(sub_data, units)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'safety':
                    replace_text = get_simple_clean_safety_text(sub_data, units)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'citation':
                    replace_text = get_clean_citation_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif sub_type == 'command':
                    replace_text = get_clean_command_text(sub_data)
                    command_list.append(replace_text)
                elif sub_type == 'tex_formula':
                    replace_text = get_sub_clean_tex_formula_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'video':
                    replace_text = get_clean_video_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'emoji':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_emoji_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'centrifugation':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_sub_clean_centrifugation_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'ph':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_sub_clean_ph_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'cost':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_sub_clean_cost_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'pressure':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_sub_clean_pressure_text(sub_data,units)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'humidity':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_sub_clean_humidity_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'humidity':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_sub_clean_sample_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'spectral':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_spectral_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'file':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_file_text(sub_data)
                    sub_map[(offset, offset + length)] = replace_text
                elif type == 'embed':
                    # text = outsidemap['text'] if outsidemap['text'] else ''
                    replace_text = get_clean_embed_text(sub_data)
                    embed_list.append(replace_text)
                else:
                    print(f'extra sub type is {type}')

            # 替换字符串
        if sub_map:
            if (0, len(sub_text)) in sub_map:
                new_s = sub_map[(0, len(sub_text))]
            else:
                # 替换字符串
                new_s = get_new_text(sub_map, sub_text)
        else:
            new_s = sub_text
        if not new_s.startswith('<'):
            sub_result = sub_result +  '<span>' + new_s + '</span>'
        else:
            sub_result = sub_result +  new_s
        if command_list:
            for command in command_list:
                sub_result=sub_result+command
        if embed_list:
            for embed in embed_list:
                sub_result=sub_result+embed


    return sub_result

def get_clean_imageblock_text(data,doi):
    if 'source' in dict(data).keys():
        source = data['source']
        regulate='尊敬的用户，由于网络监管政策的限制，部分内容暂时无法在本网站直接浏览。我们已经为您准备了相关原始数据和链接，感谢您的理解与支持。'
        if source:

            if 'googleusercontent' in source:
                result=f'\n```\n#{regulate}\n{source}\n```\n'
                return '\n'+result
            elif 'blob:' in source:
                return ''

            original_name = data['original_name']
            if original_name:
                return f'<img src="{source}" alt="{original_name}" loading="lazy" title="{original_name}"/>\n'
            else:
                return f'<img src="{source}" alt="" loading="lazy" title=""/>\n'
    else:

        result = dict()
        result['doi'] = doi
        result['reason'] = 'imageblock source not exist'
        get_data = {doi: result}
        # 更新字符串列表（这里假设你想要在读取的字符串后面追加新的字符串）
        # update_and_save_map('./resource_list/clean_fail.txt', get_data)
        # raise Exception('imageblock source not exist')




def get_clean_equipment_text(data):
    equipment_name = data['name'] if data['name'] else ''
    equipment_type = data['type'] if data['type'] else ''
    equipment_brand = data['brand'] if data['brand'] else ''
    equipment_sku = data['sku'] if data['sku'] else ''
    equipment_link = data['link'] if data['link'] else ''
    if 'vendor' in dict(data).keys() and data['vendor'] and not equipment_link:
        equipment_link = data['vendor']['link'] if data['vendor']['link'] else ''
    else:
        equipment_link = ''



    equipment_specifications = data['specifications'] if data['specifications'] else ''

    title = '\nEquipment\n\n'
    data = [['Value', 'Label']]

    if equipment_name:
        data.append([equipment_name, 'NAME'])
    if equipment_type:
        data.append([equipment_type, 'TYPE'])

    if equipment_brand:
        data.append([equipment_brand, 'BRAND'])

    if equipment_sku:
        data.append([equipment_sku, 'SKU'])

    if equipment_link:
        data.append([equipment_link, 'LINK'])

    if equipment_specifications:
        data.append([equipment_specifications, 'SPECIFICATIONS'])

    # array = [{'label': 'NAME', 'value': equipment_name}, {'label': 'TYPE', 'value': equipment_type},
    #          {'label': 'BRAND', 'value': equipment_brand},
    #          {'label': 'SKU', 'value': equipment_sku}, {'label': 'SPECIFICATIONS', 'value': equipment_specifications},
    #          {'label': 'LINK', 'link': equipment_link, 'value': equipment_link}]
    # replace_text = f'<Entity type="Equipment"  datasource="{array}" />'
    table = get_table_for_equipment(data)
    data = title + table
    return data


def get_clean_citation_text(data):
    citation_title = data['title']
    citation_journal = data['journal']
    uri = data['doi']
    authors = data['authors']
    date = data['date']
    data = ''

    if authors:
        data = data+f'{authors} '


    if date:
        year = timestamp_year(date)
        data = data + f'{year} '

    if citation_title:
        data = data + f'{citation_title} '

    if citation_journal:

        data = data + f' {citation_journal} '

    if uri:
        data = data + f'<a href="{uri}">{uri}</a>'
    data = data.replace('\n', '')
    result=f'<Note title="Citation" type="info" >{data}</Note>'
    return result


def get_clean_dataset_text(data):
    if 'affiliation' in dict(data).keys():
        affiliation = data['affiliation']
    else:
        affiliation = None

    uri = data['link']

    name = data['name']

    data=''

    if affiliation:
        data=data+affiliation


    if name:
        data = data + name
        # result = result + f'({name}) '

    if uri:
        data = data + f'<a href="{uri}">{uri}</a>'

        # result = result + f'<a href="{uri}">{uri}</a>'
    data = data.replace('\n', '')
    result = f'<Note title="Dateset" type="activity" >' + data+'</Note>'
    return result


def get_clean_protocol_text(data):
    protocol_name = data['title']
    protocol_uri = 'https://www.protocols.io/view/' + data['uri']
    # protocol_image_uri = data['image']['source']
    # author_name = data['creator']['name']
    # author_uri = data['creator']['link']
    # author_image_uri = data['creator']['user_image_file']['url']
    # array = [{'label': 'create by', 'link': author_uri, 'image': author_image_uri, 'value': author_name},
    #          {'label': 'title', 'link': protocol_uri, 'image': protocol_image_uri, 'value': protocol_name}]
    # replace_text = f'<Entity type="Protocol"  datasource="{array}" />'
    replace_text = f'[{protocol_name}]({protocol_uri})'
    return replace_text


def get_sub_clean_protocol_text(data):
    protocol_name = data['title']
    protocol_uri = 'https://www.protocols.io/view/' + data['uri']
    # protocol_image_uri = data['image']['source']
    # author_name = data['creator']['name']
    # author_uri = data['creator']['link']
    # author_image_uri = data['creator']['user_image_file']['url']
    # array = [{'label': 'create by', 'link': author_uri, 'image': author_image_uri, 'value': author_name},
    #          {'label': 'title', 'link': protocol_uri, 'image': protocol_image_uri, 'value': protocol_name}]
    # replace_text = f'<Entity type="Protocol"  datasource="{array}" />'
    replace_text = f'[{protocol_name}]({protocol_uri})'
    replace_text = f'<a href="{protocol_uri}" title="{protocol_name}">{protocol_name}</a>'
    return replace_text

def get_clean_tex_formula_text(data):
    text=data['formula']
    return f'${text}$'

def get_sub_clean_tex_formula_text(data):
    text = data['formula']
    return f'\n${text}$'
def get_clean_duration_text(data):
    duration = int(data['duration'])
    if not duration:
        return ''
    hours = duration // 3600
    minutes = duration // 60 - hours * 60
    seconds = duration % 60
    replace_text = f'`{hours}h {minutes}m {seconds}s`'
    return replace_text


def get_sub_clean_duration_text(data):
    duration = data['duration']
    hours = duration // 3600
    minutes = duration // 60 - hours * 60
    seconds = duration % 60
    replace_text = f'<b>{hours}h {minutes}m {seconds}s</b>'
    return replace_text


def get_sub_clean_tempature_text(data, units):
    amount = data['temperature']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'<b>{amount}{unit_name}</b>'
    else:
        replace_text = f'<b>{amount}</b>'

    return replace_text


def get_sub_clean_amount_text(data, units):
    amount = data['amount']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'<b>{amount}{unit_name}</b>'
    else:
        replace_text = f'<b>{amount}</b>'

    return replace_text


def get_clean_link_text(data, length, offset, text):
    uri = data['url']
    string = str(text)[offset:offset + length]
    if uri:
        replace_text = f'[{string}]({uri})'
    else:
        replace_text = f'<{string}>'

    return replace_text


def get_sub_clean_link_text(sub_text):
    replace_text = f'\n<b>{sub_text}</b>\n'
    return replace_text


def get_sub_clean_concentration_text(data, units):
    concentration = data['concentration']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'<b>{concentration}{unit_name}</b>'
    else:
        replace_text = f'<b>{concentration}</b>'

    return replace_text


def get_sub_clean_reagents_text(data):
    name = data['name']
    replace_text = f'<b>{name}</b>'
    return replace_text


def get_clean_gotostep_text(data):
    # replace_text = f'`gotostep`'
    replace_text = f''
    return replace_text


def get_sub_clean_shaker_text(data, units):
    shaker = data['shaker']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'<b>{shaker}{unit_name}</b>'
    else:
        replace_text = f'<b>{shaker}</b>'

    return replace_text


def get_table_for_equipment(data):
    # 构建 Markdown 表格
    markdown_table = "| " + " | ".join(data[0]) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(data[0])) + " |\n"
    markdown_length = 0
    for row in data:
        if markdown_length != 0:
            markdown_table += "| " + " | ".join(row) + " |\n"
        markdown_length = markdown_length + 1

    markdown_table = markdown_table + '\n'
    return markdown_table


# def get_clean_centrifuge_text(data, units):
#     centrifuge = data['centrifuge']
#     centrifuge_unit_key = data['unit']
#     centrifuge_unit = next((unit for unit in units if unit['id'] == centrifuge_unit_key), None)
#
#     if 'duration' in dict(data).keys():
#         duration = data['duration']
#     else:
#         duration = None
#
#     temperature = data.get['temperature']
#     temperature_unit_key = data['temperatureUnit']
#     temperature_unit = next((unit for unit in units if unit['id'] == temperature_unit_key), None)
#     centrifuge_unit_name = centrifuge_unit['name'] if centrifuge_unit else 'undefine'
#     temperature_unit_name = temperature_unit['name'] if temperature_unit else 'undefine'
#
#     if duration:
#         hours = duration // 3600
#         minutes = duration // 60 - hours * 60
#         seconds = duration % 60
#         replace_text = f'`{centrifuge}{centrifuge_unit_name},{temperature}{temperature_unit_name},{hours}h {minutes}m {seconds}s`'
#     else:
#         replace_text = f'`{centrifuge}{centrifuge_unit_name},{temperature}{temperature_unit_name}`'
#
#     return replace_text


def get_clean_centrifuge_text(data, units):


    if 'centrifuge' in dict(data).keys():
        centrifuge = data['centrifuge']
    else:
        centrifuge = None
    if centrifuge:
        centrifuge_unit_key = data['unit']
        centrifuge_unit = next((unit for unit in units if unit['id'] == centrifuge_unit_key), None)
        centrifuge_unit_name = centrifuge_unit['name'] if centrifuge_unit else 'undefine'
        replace_text = f'`{centrifuge}{centrifuge_unit_name}'
    else:
        replace_text = f'`'



    if 'temperature' in dict(data).keys():
        temperature = data['temperature']

    else:
        temperature = None
    if temperature:
        temperature = data['temperature']
        temperature_unit_key = data['temperatureUnit']
        temperature_unit = next((unit for unit in units if unit['id'] == temperature_unit_key), None)

        temperature_unit_name = temperature_unit['name'] if temperature_unit else 'undefine'
        replace_text = replace_text+f',{temperature}{temperature_unit_name}'



    if 'duration' in dict(data).keys():
        duration = int(data['duration']) if data['duration'] else 0
        if duration == 0:

            hours = duration // 3600
            minutes = duration // 60 - hours * 60
            seconds = duration % 60
            replace_text=replace_text+f',{hours}h {minutes}m {seconds}s`'
        else:
            replace_text = replace_text + f'`'
    else:
        replace_text = replace_text + f'`'


    return replace_text


def get_sub_clean_centrifuge_text(data, units):
    centrifuge = data['centrifuge']
    centrifuge_unit_key = data['unit']
    centrifuge_unit = next((unit for unit in units if unit['id'] == centrifuge_unit_key), None)

    if 'duration' in dict(data).keys():
        duration = data['duration']
    else:
        duration = None

    temperature = data['temperature']
    temperature_unit_key = data['temperatureUnit']
    temperature_unit = next((unit for unit in units if unit['id'] == temperature_unit_key), None)
    centrifuge_unit_name = centrifuge_unit['name'] if centrifuge_unit else 'undefine'
    temperature_unit_name = temperature_unit['name'] if temperature_unit else 'undefine'

    if duration:
        hours = duration // 3600
        minutes = duration // 60 - hours * 60
        seconds = duration % 60
        replace_text = f'<b>{centrifuge}{centrifuge_unit_name},{temperature}{temperature_unit_name},{hours}h {minutes}m {seconds}s</b>'
    else:
        replace_text = f'<b>{centrifuge}{centrifuge_unit_name},{temperature}{temperature_unit_name}</b>'
    return replace_text



def get_clean_centrifugation_text(data, units):


    if 'centrifuge' in dict(data).keys():
        centrifuge = data['centrifuge']
    else:
        centrifuge = None
    if centrifuge:
        centrifuge_unit_key = data['unit']
        centrifuge_unit = next((unit for unit in units if unit['id'] == centrifuge_unit_key), None)
        centrifuge_unit_name = centrifuge_unit['name'] if centrifuge_unit else 'undefine'
        replace_text = f'`{centrifuge}{centrifuge_unit_name}`'



    return replace_text


def get_sub_clean_centrifugation_text(data, units):
    centrifuge = data['centrifuge']
    centrifuge_unit_key = data['unit']
    centrifuge_unit = next((unit for unit in units if unit['id'] == centrifuge_unit_key), None)
    centrifuge_unit_name = centrifuge_unit['name'] if centrifuge_unit else 'undefine'


    replace_text = f'<b>{centrifuge}{centrifuge_unit_name}</b>'

    return replace_text


def get_clean_ph_text(data):


    if 'number' in dict(data).keys():
        number = data['number']
    else:
        number = None
    if number:
        replace_text = f'`{number}`'

    return replace_text


def get_sub_clean_ph_text(data):
    if 'number' in dict(data).keys():
        number = data['number']
    else:
        number = None
    if number:
        replace_text = f'<b>{number}</b>'

    return replace_text

def get_clean_cost_text(data):
    if 'value' in dict(data).keys():
        value = data['value']
    else:
        value = None
    if value:
        replace_text = f'`{value}`'
    else:
        return ''

    return replace_text


def get_sub_clean_cost_text(data):
    if 'value' in dict(data).keys():
        value = data['value']
    else:
        value = None
    if value:
        replace_text = f'<b>{value}</b>'

    return replace_text


def get_clean_sample_text(data, units):


    if 'name' in dict(data).keys():
        value = data['name']
    else:
        value = None
    if value:
        replace_text = f'`{value}`'
    else:
        replace_text = f'`Sample`'

    return replace_text


def get_sub_clean_sample_text(data, units):
    if 'name' in dict(data).keys():
        value = data['name']
    else:
        value = None
    if value:
        replace_text = f'<b>{value}</b>'
    else:
        replace_text = f'<b>Sample</b>'
    return replace_text

def get_clean_humidity_text(data):


    if 'amount' in dict(data).keys():
        value = data['amount']
    else:
        value = None
    if value:
        replace_text = f'`{value}`'

    return replace_text


def get_sub_clean_humidity_text(data):
    if 'amount' in dict(data).keys():
        value = data['amount']
    else:
        value = None
    if value:
        replace_text = f'<b>{value}</b>'

    return replace_text


def get_clean_pressure_text(data, units):


    if 'value' in dict(data).keys():
        value = data['value']
    else:
        value = None
    if value:
        pressure_unit_key=data['unit']
        pressure_unit = next((unit for unit in units if unit['id'] == pressure_unit_key), None)
        pressure_unit_name = pressure_unit['name'] if pressure_unit else 'undefine'
        replace_text = f'`{value} {pressure_unit_name}`'

    return replace_text


def get_sub_clean_pressure_text(data, units):
    if 'value' in dict(data).keys():
        value = data['value']
    else:
        value = None
    if value:
        pressure_unit_key = data['unit']
        pressure_unit = next((unit for unit in units if unit['id'] == pressure_unit_key), None)
        pressure_unit_name = pressure_unit['name'] if pressure_unit else 'undefine'
        replace_text = f'<b>{value} {pressure_unit_name}</b>'

    return replace_text

def get_simple_clean_notes_text(data, units):
    new_s = get_note_label_content(data, units)
    new_s=new_s.replace('\n','')

    result = f'<Note title="Note" type="warning" >{new_s}</Note>'

    return result


def get_simple_clean_safety_text(data, units):
    new_s = get_note_label_content(data, units)
    new_s=new_s.replace('\n','')

    result = f'<Note title="Safety information" type="error" >{new_s}</Note>'

    return result


def get_simple_clean_citation_text(data, units):
    new_s = get_note_label_content(data, units)
    new_s=new_s.replace('\n','')

    result = f'<Note title="Citation" type="info" >{new_s}</Note>'

    return result

def get_simple_clean_expected_result_text(data, units):
    new_s = get_note_label_content(data, units)
    new_s=new_s.replace('\n','')

    result = f'<Note title="Citation" type="success" >{new_s}</Note>'

    return result


def get_note_label_content(data, units):
    blocks = data['blocks']
    note_result = ''

    if 'entityMap' in data.keys() and data['entityMap']:
        if isinstance(data['entityMap'], list):
            len_map = len(data['entityMap'])
            keys = [str(index) for index in (0, len_map)]
            entityMap = OrderedDict(zip(keys, data['entityMap']))
        else:
            entityMap = dict(data['entityMap'])
    else:
        entityMap = {}


    if blocks:
        for e in blocks:
            text = e['text']
            map = dict()
            # 自己标签不做样式的区别 inlineStyleRanges = e['inlineStyleRanges']
            entityRanges = e['entityRanges']

            inlineStyleRanges = e['inlineStyleRanges']

            if inlineStyleRanges:
                inlineStyleRanges = get_new_inlineranges(inlineStyleRanges)
                for inlineStyleRange in inlineStyleRanges:
                    stype = inlineStyleRange['style']
                    offset = inlineStyleRange['offset']
                    length = inlineStyleRange['length']
                    string = None
                    replace_text = None
                    if stype == 'italic':
                        string = str(text)[offset:offset + length]
                        if string.strip():
                            replace_text = '<i>' + string.strip() + '</i> '
                        else:
                            replace_text = string

                    elif stype == 'sup':
                        string = str(text)[offset:offset + length]

                        if string.strip():
                            replace_text = '<sup>' + string.strip() + '</sup>'
                        else:
                            replace_text = string

                    elif stype == 'sub':
                        string = str(text)[offset:offset + length]
                        if string.strip():
                            replace_text = '<sub>' + string.strip() + '</sub>'
                        else:
                            replace_text = string
                    elif stype == 'bold':
                        string = str(text)[offset:offset + length]
                        if string.strip():
                            replace_text = '<b>' + string.strip() + '</b> '
                        else:
                            replace_text = string
                    elif stype == 'UNDERLINE':
                        string = str(text)[offset:offset + length]
                        if string.strip():
                            replace_text = '<i>' + string.strip() + '</i> '
                        else:
                            replace_text = string
                    elif stype == 'bold_italic':
                        string = str(text)[offset:offset + length]
                        if string.strip():
                            replace_text = '<strong><em>' + string.strip() + '</em></strong> '
                        else:
                            replace_text = string
                    else:
                        print(f'extra style is {stype}')
                    if string:
                        map[(offset, offset + length)] = replace_text

            if entityRanges:
                for entityRange in entityRanges:
                    key = entityRange['key']
                    outsidemap = entityMap.get(str(key), {})
                    offset = entityRange['offset']
                    length = entityRange['length']
                    type = outsidemap['type']
                    mutability = outsidemap['mutability']
                    data = outsidemap['data']

                    if type == 'link':
                        replace_text = get_sub_clean_link_text(text)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'amount':

                        replace_text = get_sub_clean_amount_text(data, units)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'temperature':

                        replace_text = get_sub_clean_tempature_text(data, units)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'duration':
                        replace_text = get_sub_clean_duration_text(data)
                        map[(offset, offset + length)] = replace_text

                    elif type == 'concentration':
                        replace_text = get_sub_clean_concentration_text(data, units)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'reagents':
                        replace_text = get_sub_clean_reagents_text(data)
                        map[(offset, offset + length)] = replace_text

                    elif type == 'shaker':
                        replace_text = get_sub_clean_shaker_text(data, units)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'centrifuge':
                        replace_text = get_sub_clean_centrifuge_text(data, units)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'geographic':
                        replace_text = get_sub_clean_geographic_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'thickness':
                        replace_text = get_sub_clean_thickness_text(data, units)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'file':
                        replace_text = get_sub_clean_file_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'image':
                        replace_text = get_clean_image_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'tex_formula':
                        replace_text = get_sub_clean_tex_formula_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'video':
                        replace_text = get_clean_video_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'emoji':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_clean_emoji_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'centrifugation':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_sub_clean_centrifugation_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'ph':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_sub_clean_ph_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'cost':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_sub_clean_cost_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'pressure':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_sub_clean_pressure_text(data,units)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'humidity':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_sub_clean_humidity_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'sample':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_sub_clean_sample_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'spectral':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_clean_spectral_text(data)
                        map[(offset, offset + length)] = replace_text
                    elif type == 'file':
                        # text = outsidemap['text'] if outsidemap['text'] else ''
                        replace_text = get_clean_file_text(data)
                        map[(offset, offset + length)] = replace_text
                    else:
                        print(f'extra type is {type}')
                # 替换字符串
            if map:
                if (0, len(text)) in map:
                    new_s = map[(0, len(text))]
                else:
                    # 替换字符串
                    new_s = get_new_text(map, text)
            else:
                new_s = text
            if not new_s.startswith('<'):
                note_result = note_result  + '<span>' + new_s + '</span>'
            else:
                note_result = note_result  + new_s
    return note_result


def get_steps_section_map(steps):
    # 手动构建字典进行分组
    grouped_data = {}
    for item in steps:
        category = item["section"]

        if category not in grouped_data:
            grouped_data[category] = []
        grouped_data[category].append(item)
    return grouped_data


def get_clean_file_text(data):
    original_name = data['original_name']
    source = data['source']
    if source:
        regulate = '尊敬的用户，由于网络监管政策的限制，部分内容暂时无法在本网站直接浏览。我们已经为您准备了相关原始数据和链接，感谢您的理解与支持。'
        if 'googleusercontent' in source:
            result = f'\n```\n#{regulate}\n{source}\n```\n'
            result='\n' + result

            return result

    return f'[{original_name}]({source})'




def get_sub_clean_file_text(data):
    original_name = data['original_name']
    source = data['source']
    return f'<a href="{source}">{source}</a>'


def get_clean_geographic_text(data):
    value = data['value']
    match = re.findall(r"[-+]?\d*\.\d+|\d+", value)
    if not value:
        return ''
    string = match[0] + ';' + match[1]
    uri = f'https://geohack.toolforge.org/geohack.php?params={string}'
    return f'[ {value}]({uri})'


def get_clean_thickness_text(data, units):
    label = data['label']
    value = data['value']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'`{value} {unit_name} {label}`'
    else:
        replace_text = f'`{value} {label}`'

    return replace_text


def get_clean_software_text(data):
    link = data['link'] if data['link'] else ''
    os_name = data['os_name'] if data['os_name'] else ''
    name = data['name'] if data['name'] else ''
    os_version = data['os_version'] if data['os_version'] else ''
    repository = data['repository'] if data['repository'] else ''
    version = data['version'] if data['version'] else ''
    developer = data['developer'] if data['developer'] else ''

    title = '\nSoftware\n\n'
    data = [['Value', 'Label']]
    if name:
        data.append([name, 'NAME'])
    if os_name:
        data.append([os_name, 'OS_NAME'])
    if os_version:
        data.append([os_version, 'OS_VERSION'])
    if repository:
        data.append( [repository, 'REPOSITORY'])
    if developer:
        data.append( [developer, 'DEVELOPER'])
    if link:
        data.append([link, 'LINK'])
    if version:
        data.append([version, 'VERSION'])


    table = get_table_for_equipment(data)
    data = title + table
    return data


def get_sub_clean_geographic_text(data):
    value = data['value']
    match = re.findall(r"[-+]?\d*\.\d+|\d+", value)
    string = match[0] + ';' + match[1]
    uri = f'https://geohack.toolforge.org/geohack.php?params={string}'
    replace_text = f'<a href="{uri}" title="{value}">{value}</a>'
    return replace_text


def get_sub_clean_thickness_text(data, units):
    label = data['label']
    value = data['value']
    unit_key = data['unit']
    unit = next((unit for unit in units if unit['id'] == unit_key), None)
    if unit:
        unit_name = unit['name']
        replace_text = f'<b>{value} {unit_name} {label}</b>'
    else:
        replace_text = f'<b>{value} {label}</b>'

    return replace_text


def get_normal_content(data):

    if isinstance(data, dict):
        note_result = get_normal_cntent_result(data)
    else:
        try:
            data = str(data)
            data=json.loads(data)
            data=dict(data)
            note_result = get_normal_cntent_result(data)
        except Exception as e:
            return str(data)

    return note_result


def get_normal_cntent_result(data):
    blocks = data['blocks']
    note_result = ''
    if data['entityMap']:
        entityMap = dict(data['entityMap'])
    else:
        entityMap = {}
    if blocks:
        for e in blocks:
            text = e['text']
            map = dict()
            # 自己标签不做样式的区别 inlineStyleRanges = e['inlineStyleRanges']
            # 替换字符串
            if map:
                if (0, len(text)) in map:
                    new_s = map[(0, len(text))]
                else:
                    # 替换字符串
                    new_s = get_new_text(map, text)
            else:
                new_s = text

            note_result = note_result + '\n' + new_s
    return note_result


def get_clean_code_text(data, code_type):
    text = get_normal_content(data)
    return f'```{code_type}{text}\n```'


def get_clean_emoji_text(data):
    text = str(data['name'])
    text = text.replace(':', '')
    if  'tm' ==text.strip():
        text='TM'
    elif 'registered'==text.strip():
        text='®'

    return f'<sup>{text}</sup>'


def get_clean_command_text(data):
    command_name = data['command_name']
    name = data['name']
    os_name = data['os_name']
    os_version = data['os_version']
    add_string=''
    if os_name:
        add_string=f'({os_name}'
    if os_version:
        add_string=add_string+f' {os_version}'
    if os_name:
        add_string=add_string+')'
    if command_name:
        return f'\n\n\n```\n#{command_name} {add_string}\n{name}\n```'
    else:
        return f'\n\n\n```\n{name}\n```'




def get_clean_embed_text(data):

    code = data['code']
    regulate='尊敬的用户，由于网络监管政策的限制，部分内容暂时无法在本网站直接浏览。我们已经为您准备了相关原始数据和链接，感谢您的理解与支持。'
    result='\n'+f'```\n#{regulate}\n{code}\n```\n'

    return result

def get_clean_well_plate_map_text(data):
    dataSource=data['well']
    if 'wellColumns' in dict(data).keys():

        wellColumns=data['wellColumns']
        # wellColumns = json.dumps(wellColumns)
    else:
        wellColumns=''

    # dataSource=json.dumps(dataSource)

    return f'<Well data="{dataSource}" columns="{wellColumns}" />'


def get_text_from_documents(documents):
    result=''
    for document in documents:
        url = document['url']
        name=document['ofn'] if document['ofn'] else document['url']

        text=f'[ {name}]({url})'
        result=result+'\n'+text
    return result


def get_abstart_flag(content):
    flag = False
    if isinstance(content, dict):
        content = json.loads(content)
        description = dict(content)
        blocks = description['blocks']
        for block in blocks:
            if block['text']:
                flag = True
                break
    elif isinstance(content, str):
        if content:
            flag=True
    return flag


def get_abstartct(original_data, units,resources,doi):
    abstract = ''
    # if original_data.disclaimer and get_abstart_flag(original_data.disclaimer):
    #     content3 = '\n# Disclaimer \n'
    #     result1 = get_md_result_from_blocks(original_data.disclaimer, content3, units)
    #     abstract = abstract + result1
    if original_data.description and get_abstart_flag(original_data.description):
        result2 = get_md_result_from_blocks(original_data.description, '', units, 'abstract',doi)
        result2 = get_replace_resource(resources, result2)
        result2 = content_deal(result2)
        abstract = abstract + result2
    # if original_data.before_start and get_abstart_flag(original_data.before_start):
    #     content2 = '\n# Before_start \n'
    #
    #     result3 = get_md_result_from_blocks(original_data.before_start, content2, units)
    #     abstract = abstract + result3

    return abstract





def get_content_from_steps(original_data, units, resources,doi):
    result_map=dict()
    # if original_data.description and get_abstart_flag(original_data.description):
    #     content1 = '\n# Abstract \n'
    #     result2 = get_md_result_from_blocks(original_data.description, content1, units, 'abstract')
    #     section_result = section_result + result2 + '\n'

    if original_data.disclaimer and get_abstart_flag(original_data.disclaimer):
        content2 = '\n'

        result3 = get_md_result_from_blocks(original_data.disclaimer, content2, units, 'content',doi)
        result3 = get_replace_resource(resources, result3)
        result3 = content_deal(result3)
        result_map['disclaimer']=result3
    if original_data.description and get_abstart_flag(original_data.description):
        content2 = '\n'

        result3 = get_md_result_from_blocks(original_data.description, content2, units, 'content',doi)
        result3 = get_replace_resource(resources, result3)
        result3 = content_deal(result3)
        result_map['abstract']=result3
    if original_data.before_start and get_abstart_flag(original_data.before_start):
        content2 = '\n'

        result3 = get_md_result_from_blocks(original_data.before_start, content2, units, 'content',doi)
        result3 = get_replace_resource(resources, result3)
        result3 = content_deal(result3)
        result_map['beforeStart']=result3

    if original_data.documents :

        result3 = get_text_from_documents(original_data.documents)
        result3 = get_replace_resource(resources, result3)
        result3 = content_deal(result3)
        result_map['attachments'] = result3
    steps = original_data.steps
    step_list = []
    if steps:
        steps = [step for step in steps if step['number']]
        steps = sorted(steps, key=lambda x: natural_keys(x['number']))
        # 排序列表
        steps = sorted(steps, key=lambda x: float(x["number"]))
        section_list=[]

        for step in steps:
            section = step['section']
            if section :
                soup = bs4.BeautifulSoup(section, 'html.parser')
                section_text=soup.text
                if section_text not in section_list:
                    section={'type':'section', 'data':section_text,'number':None}
                    step_list.append(section)
                    section_list.append(section_text)
            number=step['number']
            if number == '22':
                print()
            if str(step['step']):
                content = get_md_result_from_blocks(str(step['step']), '', units, 'content',doi)
            else:
                content=''
                print(f'step is null')
            content=get_replace_resource(resources,content)
            content = content_deal(content)
            step_e={'data':content,'number':number,'type':'step'}
            step_list.append(step_e)
    result_map['steps']=step_list
    return result_map

def get_abstartct_backup(original_data, units,doi):
    abstract = ''
    # if original_data.disclaimer and get_abstart_flag(original_data.disclaimer):
    #     content3 = '\n# Disclaimer \n'
    #     result1 = get_md_result_from_blocks(original_data.disclaimer, content3, units)
    #     abstract = abstract + result1
    if original_data.description and get_abstart_flag(original_data.description):
        result2 = get_md_result_from_blocks(original_data.description, '', units, 'abstract',doi)
        abstract = abstract + result2
    # if original_data.before_start and get_abstart_flag(original_data.before_start):
    #     content2 = '\n# Before_start \n'
    #
    #     result3 = get_md_result_from_blocks(original_data.before_start, content2, units)
    #     abstract = abstract + result3

    return abstract


def get_content_from_steps_backup(original_data, units, resources,doi):
    section_result = ''
    if original_data.description and get_abstart_flag(original_data.description):
        content1 = '\n# Abstract \n'
        result2 = get_md_result_from_blocks(original_data.description, content1, units, 'abstract',doi)
        section_result = section_result + result2 + '\n'
    if original_data.before_start and get_abstart_flag(original_data.before_start):
        content2 = '\n# Before_start \n'

        result3 = get_md_result_from_blocks(original_data.before_start, content2, units, 'abstract',doi)
        section_result = section_result + result3 + '\n'
    steps = original_data.steps
    if steps:
        steps=[step for step in steps if step["number"]]
        # 排序列表
        steps = sorted(steps, key=lambda x: float(x["number"]))

        grouped_data = get_steps_section_map(steps)

        for category in grouped_data:
            sub_steps = grouped_data[category]
            section = sub_steps[0]['section']
            if section is None:
                continue
            soup = bs4.BeautifulSoup(section, 'html.parser')
            result = ''
            for step in sub_steps:
                step_number = step['number']

                start = f'{step_number} '
                content = ''
                if str(step['step']):
                    content = get_md_result_from_blocks(str(step['step']), '', units, 'content',doi)

                single_result = start + content + "\n\n"
                result = result + single_result
            if soup.text:
                section_result = section_result + f'# {soup.text}\n' + result
            else:
                section_result = section_result + result

        if resources:
            seen_names = set()
            resources = list(resource for resource in resources if resource.oss_path not in seen_names and not seen_names.add(resource.oss_path))
            for resource in resources:
                if resource.oss_path:
                    if str(resource.original_path) in str(section_result):
                        section_result = section_result.replace(resource.original_path,
                                                                f'https://static.yanyin.tech/{resource.oss_path}')
                    else:

                        get_url = get_url_from_text(section_result, resource.original_path.split('?')[0])
                        if not get_url:
                            get_url=resource.original_path
                        section_result = section_result.replace(get_url,
                                                                f'https://static.yanyin.tech/{resource.oss_path}')

        section_result=content_deal(section_result)
        content1, content2, content3 = content_split(section_result)

        return content1, content2, content3
    return '', '', ''

