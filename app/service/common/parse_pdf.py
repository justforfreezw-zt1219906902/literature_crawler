import logging
import oss2
import fitz
import tempfile

from app.models.clean_data import CleanDataNatureProtocol
from app.util.oss_util import get_default_bucket
from app.service import pdf2doi
from extensions.ext_database import db

from app.util.redis_util import add_to_array , batch_hash_set
from app.service import count_key, success_count_key, fail_count_key, total_count_key, success_list_key, fail_list_key
from extensions.ext_redis import redis_client

logger = logging.getLogger(__name__)
log_prefix = '[parse_pdf] '
timeout = 3600 * 10

oss_prefix = 'https://static.yanyin.tech/'


def parse_pdf(task_id, task_setup):
    logger.info(f'{log_prefix}taskId is {task_id}, task_setup is {task_setup}')
    conflict_strategy = task_setup['conflict_strategy']
    pdf_path = task_setup['pdf_path']

    """初始化redis中的进度信息"""
    batch_hash_set(f'{count_key}{task_id}', {success_count_key: 0, fail_count_key: 0, total_count_key: 0}, timeout)

    bucket = get_default_bucket()

    total_count = 0
    for obj in oss2.ObjectIterator(bucket, prefix=pdf_path):
        if not obj.key.endswith('.pdf'):
            continue
        total_count += 1
    """设置任务待处理的总数"""
    redis_client.hset(f'{count_key}{task_id}', total_count_key, total_count)

    for obj in oss2.ObjectIterator(bucket, prefix=pdf_path):
        if not obj.key.endswith('.pdf'):
            continue

        pdf_key = obj.key
        original_file_name = pdf_key.split('/')[-1]
        logger.info(f'{log_prefix}pdf key is {pdf_key}')
        pdf_file = bucket.get_object(pdf_key)

        try:
            with tempfile.NamedTemporaryFile(dir='/tmp', suffix='.pdf') as temp_file:
                temp_file.write(pdf_file.read())

                # 读取PDF文件
                pdf_document = fitz.open(temp_file.name)

                subject = pdf_document.metadata['subject']

                if subject is None or subject == '':
                    # 部分meta中没有subject的文章通过pdf2doi获取doi
                    logger.info(f'{log_prefix}subject is None, try to get doi from pdf, pdf_key is {pdf_key}')
                    doi = get_doi_from_pdf(pdf_document)
                    logger.info(f'{log_prefix}get doi from pdf, doi is {doi}')
                else:
                    doi = subject.split('doi:')[1].strip()

                if doi is None:
                    logger.error(f'{log_prefix}get doi failed, doi is None, pdf_key is {pdf_key}')
                    raise Exception(f'get doi failed, doi is None, pdf_key is {pdf_key}')

                logger.info(f'{log_prefix}doi is {doi}')

                clean_data = CleanDataNatureProtocol.query.filter_by(doi=doi).first()
                if clean_data is None:
                    logger.error(f'{log_prefix}clean data not found, doi is {doi}')
                    raise Exception(f'clean data not found, doi is {doi}')

                if clean_data.file_info is not None and conflict_strategy == 'skip':
                    logger.info(f'{log_prefix}skip this file, doi is {doi}')

                    """更新成功状态"""
                    add_to_array(f'{success_list_key}{task_id}', original_file_name, timeout)
                    redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
                    continue

                logger.info(f'{log_prefix}clean data found, doi is {doi}, data id is {clean_data.id}')

                # 上传PDF文件到特定目录
                oss_folder = f'literature/nature_protocol/{doi}/'
                oss_path = oss_folder + "original_pdf/" + temp_file.name.split('/')[-1]
                response = bucket.put_object_from_file(oss_path, temp_file.name)
                if response is None:
                    logger.error(f'{log_prefix}upload pdf failed, pdf_key is {pdf_key}, oss_path is {oss_path}')
                    raise Exception(f'upload pdf failed, pdf_key is {pdf_key}, oss_path is {oss_path}')

                etag = response.etag
                uploaded_pdf_path = oss_prefix + oss_path

                logger.info(f'{log_prefix}upload pdf success, doi is {doi}, oss_path is {oss_path}')

                # 解析2、3级书签及对应页码，并转换为层级嵌套结构的JSON
                bookmarks = get_bookmarks(pdf_document)

                logger.info(f'{log_prefix}parse bookmarks success, doi is {doi}')

                # 将PDF转换为PNG图片并上传到OSS
                document_info = pdf_to_png_and_upload(bucket, oss_folder, pdf_document)

                logger.info(f'{log_prefix}pdf to png and upload success, doi is {doi}')

                # 保存信息到数据库
                file_info = {
                    "md5": etag,
                    "ossPath": uploaded_pdf_path,
                    "bookmarks": bookmarks,
                    "pages": document_info['pages']
                }

                clean_data.file_info = file_info
                db.session.commit()

                logger.info(f'{log_prefix}save file info success, doi is {doi}')

                """更新成功状态"""
                add_to_array(f'{success_list_key}{task_id}', original_file_name, timeout)
                redis_client.hincrby(f'{count_key}{task_id}', success_count_key)
        except Exception as e:
            logger.error(f'{log_prefix}parse pdf failed with exception {e}')

            """更新失败状态"""
            add_to_array(f'{fail_list_key}{task_id}', original_file_name, timeout)
            redis_client.hincrby(f'{count_key}{task_id}', fail_count_key)
            continue
        finally:
            temp_file.close()
    return


def get_file_info(temp_file,pdf_file,pdf_key,conflict_strategy,bucket):
    temp_file.write(pdf_file.read())

    # 读取PDF文件
    pdf_document = fitz.open(temp_file.name)

    subject = pdf_document.metadata['subject']

    if subject is None or subject == '':
        # 部分meta中没有subject的文章通过pdf2doi获取doi
        logger.info(f'{log_prefix}subject is None, try to get doi from pdf, pdf_key is {pdf_key}')
        doi = get_doi_from_pdf(pdf_document)
        logger.info(f'{log_prefix}get doi from pdf, doi is {doi}')
    else:
        doi = subject.split('doi:')[1].strip()

    if doi is None:
        logger.error(f'{log_prefix}get doi failed, doi is None, pdf_key is {pdf_key}')
        return None

    logger.info(f'{log_prefix}doi is {doi}')

    clean_data = CleanDataNatureProtocol.query.filter_by(doi=doi).first()
    if clean_data is None:
        logger.error(f'{log_prefix}clean data not found, doi is {doi}')
        return None

    if clean_data.file_info is not None and conflict_strategy == 'skip':
        logger.info(f'{log_prefix}skip this file, doi is {doi}')


    logger.info(f'{log_prefix}clean data found, doi is {doi}, data id is {clean_data.id}')

    # 上传PDF文件到特定目录
    oss_folder = f'literature/nature_protocol/{doi}/'
    oss_path = oss_folder + "original_pdf/" + temp_file.name.split('/')[-1]
    response = bucket.put_object_from_file(oss_path, temp_file.name)
    if response is None:
        logger.error(f'{log_prefix}upload pdf failed, pdf_key is {pdf_key}, oss_path is {oss_path}')
        return None

    etag = response.etag
    uploaded_pdf_path = oss_prefix + oss_path

    logger.info(f'{log_prefix}upload pdf success, doi is {doi}, oss_path is {oss_path}')

    # 解析2、3级书签及对应页码，并转换为层级嵌套结构的JSON
    bookmarks = get_bookmarks(pdf_document)

    logger.info(f'{log_prefix}parse bookmarks success, doi is {doi}')

    # 将PDF转换为PNG图片并上传到OSS
    document_info = pdf_to_png_and_upload(bucket, oss_folder, pdf_document)

    logger.info(f'{log_prefix}pdf to png and upload success, doi is {doi}')

    # 保存信息到数据库
    file_info = {
        "md5": etag,
        "ossPath": uploaded_pdf_path,
        "bookmarks": bookmarks,
        "pages": document_info['pages']
    }

    return file_info



def get_doi_from_pdf(pdf_document):
    try:
        with tempfile.NamedTemporaryFile(dir='/tmp', suffix='page0.pdf') as temp_pdf_file:
            # 仅提取第一页用于获取DOI
            pdf_writer = fitz.open()
            pdf_writer.insert_pdf(pdf_document, from_page=0, to_page=0)
            pdf_writer.save(temp_pdf_file.name)
            pdf_writer.close()
            # Increase verbosity.
            # By default, only a table with the found identifiers will be printed as output.
            pdf2doi.config.set('verbose', False)
            # Disable any method to find identifiers which requires internet searches
            pdf2doi.config.set('webvalidation', False)
            # Disable the online validation of identifiers
            pdf2doi.config.set('websearch', False)
            # Disable stores the string IDENTIFIER in the metadata of the target pdf file
            # with key '/pdf2doi_identifier'.
            pdf2doi.config.set('save_identifier_metadata', False)
            result = pdf2doi.pdf2doi(temp_pdf_file.name)
            if result is not None and result['identifier_type'] == 'DOI':
                return result['identifier']
            else:
                logger.info(f'{log_prefix}get doi from pdf failed, result is {result}')
                return None
    except Exception as e:
        logger.error(f'{log_prefix}get doi from pdf failed with exception {e}')
        return None


# 解析书签并转换为层级结构
def get_bookmarks(pdf):
    toc = pdf.get_toc()  # 获取书签（目录），以 (level, title, page_num) 的元组列表返回
    bookmarks = []

    def add_bookmark(bookmark_list, level, title, page_num):
        """递归函数：将书签添加到相应的层级"""
        bookmark = {"level": level, "title": title, "page": page_num, "children": []}
        if not bookmark_list:
            bookmark_list.append(bookmark)
        else:
            # 获取上一个书签
            last_bookmark = bookmark_list[-1]
            if level > last_bookmark['level']:
                # 当前书签是上一个书签的子级
                add_bookmark(last_bookmark['children'], level, title, page_num)
            else:
                # 当前书签是同级或上一级
                bookmark_list.append(bookmark)

    # 遍历目录项并构建层级结构
    for item in toc:
        level, title, page_num = item
        if title is not None and title.endswith('\r'):
            title = title[:-1]
        add_bookmark(bookmarks, level, title, page_num)

    return bookmarks


# 将PDF转换为PNG并上传到OSS，返回JSON格式的信息
def pdf_to_png_and_upload(oss_bucket, oss_folder, pdf_document):
    pages_info = []
    for i in range(len(pdf_document)):
        with tempfile.NamedTemporaryFile(dir='/tmp', suffix=f"_page_{i}.png") as temp_png:
            # 保存每一页的PNG
            page = pdf_document[i]
            matrix = fitz.Matrix(2.5, 2.5)
            pix = page.get_pixmap(matrix=matrix)
            pix.save(temp_png.name)

            # 获取图片宽高
            width, height = pix.width, pix.height

            # 构建OSS路径
            oss_page_path = f"{oss_folder}pages/page_{i}.png"

            # 第二步：上传图片到OSS
            res = oss_bucket.put_object_from_file(oss_page_path, temp_png.name)
            if res is None:
                logger.error(f'{log_prefix}upload png failed, oss_page_path is {oss_page_path}')
                # 抛出异常
                raise Exception(f'upload png failed, oss_page_path is {oss_page_path}')

            # 第三步：将信息保存为字典
            page_info = {
                "type": "png",
                "pageId": i,
                "pageUrl": oss_prefix + oss_page_path,
                "pageWidth": width,
                "pageHeight": height
            }

            pages_info.append(page_info)

    # 将所有页的信息保存为JSON格式
    document_info = {
        "pages": pages_info
    }

    return document_info
