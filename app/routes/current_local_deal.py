import os
import time
from http.client import HTTPException
from random import random

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from app.util.current_protocol_crawl_util import get_driver, LOG_FILE, get_all_resource_from_soup, \
    filter_resource_by_original_name
from app.util.current_protocol_migrate_util import migrate_data
from app.util.migrate_util import connect
from app.util.pic_back_deal import remove_black_border
from app.util.text_deal import get_url_from_text, get_url_from_html, get_description_from_html
from app.util.oss_util import upload_file, get_file_md5
from app.util.text_deal import get_file_extension
from app.util.url_util import is_download
from extensions.ext_database import db

from flask import Blueprint

from app.models.crawl_data import (OriginalDataCurrentProtocol, CurrentProtocolResources)

from app.models.clean_data import (CurrentData)
import undetected_chromedriver as uc
from app.models.task import CleanMission
from app.util.current_protocol_clean_util import get_tre_data

current_deal = Blueprint('current_deal', __name__)


@current_deal.route('/crawl/post_deal/fill_original_path_and_fill_description')
def fill_original_path():
    session = db.session
    cleanmission = CleanMission.query.filter_by(id=10).first()

    if cleanmission.status == 0:
        try:
            cleanmission.status = 1

            db.session.commit()

            resources_list = CurrentProtocolResources.query.filter_by().all()
            resources_dict = {
                doi: [i for i in resources_list if i.doi == doi]
                for doi in set([i.doi for i in resources_list])
            }
            html_not_ok = []

            for doi in resources_dict.keys():
                print(doi)

                original_data = OriginalDataCurrentProtocol.query.filter_by(doi=doi).first()
                soup = BeautifulSoup(original_data.content, 'html.parser')
                doi_resources = resources_dict.get(doi)
                for resource in doi_resources:
                    oss_path = resource.oss_path
                    if '.pdf' in oss_path or '.mp4' in oss_path:
                        continue
                    name = str(oss_path).split('/')[-1]
                    if not resource.original_path:
                        url = get_url_from_html(original_data.content, name, 'https://currentprotocols.onlinelibrary'
                                                                             '.wiley.com')
                        if url == False:
                            html_not_ok.append(doi)
                        else:
                            resource.original_path = url
                    if not resource.description:

                        description = get_description_from_html(soup, name)
                        if description == False:
                            html_not_ok.append(doi)
                        else:
                            resource.description = description
                    session.commit()
                    time.sleep(0.2)

            session.close()

        finally:
            print(html_not_ok)
            cleanmission.status = 0

    return 'ok'


@current_deal.route('/crawl/post_deal/download_pdf')
def download_pdf():
    session = db.session
    cleanmission = CleanMission.query.filter_by(id=11).first()

    if cleanmission.status == 0:
        try:
            cleanmission.status = 1

            session.commit()
            rows = OriginalDataCurrentProtocol.query.filter_by().all()

            doi_list = []
            for literature_row in rows:
                doi_list.append(literature_row.doi)
            fail_list = []
            bucket_name = os.getenv('BUCKET_NAME')
            i=1

            for doi in doi_list:


                # 设置下载路径
                download_path = f'{LOG_FILE}/nature_protocol/resource/{doi}'
                if not os.path.exists(download_path):
                    os.makedirs(download_path)

                try:
                    # 访问目标网址
                    url = f'https://currentprotocols.onlinelibrary.wiley.com/doi/pdfdirect/{doi}?download=true'  # 替换为目标文件的 URL
                    get_resource = CurrentProtocolResources.query.filter_by(original_path=url).first()
                    if get_resource:
                        continue
                    download_file(bucket_name, doi, download_path, session, url, None,'pdf')

                except Exception as e:

                    fail_list.append(doi)
                    continue
                finally:
                    i=i+1


        finally:
            print(fail_list)
            cleanmission.status = 0

    return 'ok'


def download_file(bucket_name, doi, download_path, session, url, description,download_type):
    try:

        print(f'start to download file,url is {url}')
        if download_type == 'pdf':
            type='pdf'
        else:
            type = get_file_extension(url)

        driver = get_driver(download_path, False)
        driver.get(url)
        # 检查是否有错误信息
        # if "403" in driver.page_source:
        #     print("Received a 403 Forbidden error.")
        #     raise HTTPException(status_code=403)
        # else:
        #     print("Page loaded successfully.")

        file_name = None
        flag = True

        strart_time=0
        file_name=None

        while flag:

            files_in_folder = os.listdir(download_path)
            for file in files_in_folder:
                if type in file and 'crdownload' not  in file:
                    file_name = file
                    flag = False
                    break
            if strart_time>10:
                if type == 'png' or type == 'jpg':
                    element = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '/html/body/img'))
                    )
                if type == 'jpg' or type == 'png':
                    screenshot_path = os.path.join(download_path,
                                                       'screen'+'.'+type)
                    # 确保截图目录存在
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    driver.save_screenshot(screenshot_path)
                    remove_black_border(screenshot_path, screenshot_path)
                    file_name='screen' + '.' + type
                    flag = False

            if strart_time > 600:
                break
            time.sleep(1)
            strart_time = strart_time + 1



        if download_type == 'pdf':
            path = download_path + '/' + file_name
            pdf_name = str(doi).split('/')[-1]
            oss_path = f'literature/current_protocol/{doi}/original_pdf/' + pdf_name + '.pdf'
        else:
            path = download_path + '/' + file_name
            pdf_name = str(url).split('?')[0].split('/')[-1]
            if type  in pdf_name:
                file_name=pdf_name
            oss_path = f'literature/current_protocol/{doi}/attachments/' + file_name
        resource = CurrentProtocolResources(original_path=url, oss_bucket=bucket_name, oss_path=oss_path,
                                            doi=doi, resource_type=type, description=description
                                            )
        if path:
            # if ('.mp4' in name or '.MP4' in name or 'avi' in name or '.AVI' in name) or upload_file(oss_path, path):
            if upload_file(oss_path, path):
                md5 = get_file_md5(oss_path)
                resource.md5 = md5
                session.add(resource)
                session.commit()
                print(f' download file successfully,url is {url}')
            os.remove(path)
    except Exception as e:
        raise e

    finally:
        driver.quit()


@current_deal.route('/crawl/update/all_current_protocol')
def update_fifty_current_protocol():
    try:
        doi_list = ['10.1002/cpz1.275', '10.1002/cpz1.139', '10.1002/cpz1.697', '10.1002/cpz1.671', '10.1002/cpz1.682', '10.1002/cpz1.664', '10.1002/cpz1.1060', '10.1002/cpz1.700', '10.1002/cpz1.1064', '10.1002/cpz1.1045', '10.1002/cpz1.1028', '10.1002/cpcb.99', '10.1002/cpz1.604', '10.1002/cpz1.621', '10.1002/cpz1.506', '10.1002/cpz1.494', '10.1002/cpz1.484', '10.1002/cpz1.442', '10.1002/cpz1.411', '10.1002/cpz1.373', '10.1002/cpz1.355', '10.1002/cpz1.323', '10.1002/cpz1.305', '10.1002/cpz1.270', '10.1002/cpz1.258', '10.1002/cpz1.252', '10.1002/cpz1.218', '10.1002/cpz1.217', '10.1002/cpz1.192', '10.1002/cpz1.60', '10.1002/cpz1.45', '10.1002/cpbi.108', '10.1002/cpbi.106', '10.1002/cpbi.105', '10.1002/cpbi.104', '10.1002/cpbi.103', '10.1002/cpbi.100', '10.1002/cpbi.99', '10.1002/cpbi.97', '10.1002/cpbi.90', '10.1002/cpbi.89', '10.1002/cpbi.87', '10.1002/cpbi.81', '10.1002/cpz1.393', '10.1002/cpz1.308', '10.1002/cpz1.157', '10.1002/cpz1.139', '10.1002/cpcb.113', '10.1002/cpcb.104', '10.1002/cpcb.105', '10.1002/cpz1.487', '10.1002/cpcy.72', '10.1002/cpz1.940', '10.1002/cpz1.930', '10.1002/cpz1.922', '10.1002/cpz1.876', '10.1002/cpz1.722', '10.1002/cpz1.733', '10.1002/cpz1.731', '10.1002/cpcb.98', '10.1002/cpcb.95', '10.1002/cpcb.56', '10.1002/cpz1.490', '10.1002/cpch.86', '10.1002/cpz1.419', '10.1002/cpch.80', '10.1002/cpch.78', '10.1002/cpch.71', '10.1002/cpz1.986', '10.1002/cpz1.663', '10.1002/cpz1.1070', '10.1002/cpz1.113', '10.1002/cpz1.46', '10.1002/cpz1.59', '10.1002/cpz1.943', '10.1002/cpz1.942', '10.1002/cpz1.859', '10.1002/cpz1.794', '10.1002/cpz1.788', '10.1002/cpz1.774', '10.1002/cpz1.718', '10.1002/cpz1.739', '10.1002/cpz1.724', '10.1002/cpz1.536', '10.1002/cpz1.524', '10.1002/cpz1.485', '10.1002/cpz1.433', '10.1002/cpz1.408', '10.1002/cpz1.957', '10.1002/cpz1.822', '10.1002/cpz1.559', '10.1002/cpz1.945', '10.1002/cpz1.898', '10.1002/cpz1.825', '10.1002/cpz1.785', '10.1002/cpz1.1036', '10.1002/cpz1.745', '10.1002/cpz1.713', '10.1002/cpz1.689', '10.1002/cpz1.625', '10.1002/cpz1.589', '10.1002/cpz1.508', '10.1002/cpz1.400', '10.1002/cpz1.222', '10.1002/cpcy.75', '10.1002/cpcy.73', '10.1002/cpcy.66', '10.1002/cpz1.1042', '10.1002/cpz1.891', '10.1002/cpz1.727', '10.1002/cpz1.221', '10.1002/cpz1.1046', '10.1002/cpz1.29', '10.1002/cpet.46', '10.1002/cpet.36', '10.1002/cpet.35', '10.1002/cpz1.1087', '10.1002/cpz1.977', '10.1002/cpz1.953', '10.1002/cpz1.931', '10.1002/cpz1.906', '10.1002/cpz1.888', '10.1002/cpz1.865', '10.1002/cpz1.857', '10.1002/cpz1.818', '10.1002/cpz1.696', '10.1002/cpz1.963', '10.1002/cpz1.564', '10.1002/cpz1.997', '10.1002/cpz1.443', '10.1002/cpz1.462', '10.1002/cpz1.440', '10.1002/cpz1.427', '10.1002/cpz1.392', '10.1002/cpz1.149', '10.1002/cpz1.111', '10.1002/cphg.105', '10.1002/cpz1.1053', '10.1002/cpz1.1023', '10.1002/cpz1.1022', '10.1002/cpz1.985', '10.1002/cpz1.993', '10.1002/cpz1.991', '10.1002/cpz1.987', '10.1002/cpz1.958', '10.1002/cpz1.951', '10.1002/cpz1.1092', '10.1002/cpz1.933', '10.1002/cpz1.925', '10.1002/cpz1.897', '10.1002/cpz1.734', '10.1002/cpz1.864', '10.1002/cpz1.824', '10.1002/cpz1.783', '10.1002/cpz1.613', '10.1002/cpz1.584', '10.1002/cpz1.685', '10.1002/cpz1.557', '10.1002/cpz1.558', '10.1002/cpz1.1035', '10.1002/cpz1.561', '10.1002/cpz1.515', '10.1002/cpz1.505', '10.1002/cpz1.504', '10.1002/cpz1.516', '10.1002/cpz1.456', '10.1002/cpz1.407', '10.1002/cpz1.366', '10.1002/cpz1.359', '10.1002/cpz1.311', '10.1002/cpz1.251', '10.1002/cpz1.144', '10.1002/cpz1.934', '10.1002/cpim.111', '10.1002/cpim.106', '10.1002/cpim.104', '10.1002/cpim.100', '10.1002/cpim.93', '10.1002/cpim.85', '10.1002/cpz1.1098', '10.1002/cpz1.1069', '10.1002/cpz1.871', '10.1002/cpz1.1034', '10.1002/cpz1.1039', '10.1002/cpz1.1021', '10.1002/cpz1.1024', '10.1002/cpz1.1007', '10.1002/cpz1.932', '10.1002/cpz1.950', '10.1002/cpz1.954', '10.1002/cpz1.937', '10.1002/cpz1.912', '10.1002/cpz1.853', '10.1002/cpz1.828', '10.1002/cpz1.737', '10.1002/cpz1.716', '10.1002/cpz1.702', '10.1002/cpz1.642', '10.1002/cpz1.639', '10.1002/cpz1.588', '10.1002/cpz1.548', '10.1002/cpz1.523', '10.1002/cpz1.465', '10.1002/cpz1.463', '10.1002/cpz1.448', '10.1002/cpz1.453', '10.1002/cpz1.368', '10.1002/cpz1.309', '10.1002/cpz1.257', '10.1002/cpz1.145', '10.1002/cpz1.57', '10.1002/cpz1.44', '10.1002/cpz1.691', '10.1002/cpmc.112', '10.1002/cpmc.105', '10.1002/cpmc.100', '10.1002/cpmc.91', '10.1002/cpmc.89', '10.1002/cpmc.90', '10.1002/cpmc.88', '10.1002/cpmc.87', '10.1002/cpmb.100', '10.1002/cpmc.86', '10.1002/cpz1.1059', '10.1002/cpz1.1000', '10.1002/cpz1.1017', '10.1002/cpz1.1016', '10.1002/cpz1.970', '10.1002/cpz1.947', '10.1002/cpz1.882', '10.1002/cpz1.843', '10.1002/cpz1.805', '10.1002/cpz1.798', '10.1002/cpz1.753', '10.1002/cpz1.771', '10.1002/cpns.88', '10.1002/cpz1.76', '10.1002/cpz1.919', '10.1002/cpz1.761', '10.1002/cpz1.690', '10.1002/cpz1.683', '10.1002/cpz1.645', '10.1002/cpz1.635', '10.1002/cpz1.595', '10.1002/cpz1.532', '10.1002/cpz1.535', '10.1002/cpz1.421', '10.1002/cpz1.351', '10.1002/cpz1.316', '10.1002/cpz1.277', '10.1002/cpz1.266', '10.1002/cpz1.667', '10.1002/cpz1.236', '10.1002/cpz1.207', '10.1002/cpz1.174', '10.1002/cpz1.198', '10.1002/cpz1.187', '10.1002/cpz1.159', '10.1002/cpz1.130', '10.1002/cpz1.85', '10.1002/cpmb.131', '10.1002/cpmb.125', '10.1002/cpmb.124', '10.1002/cpmb.115', '10.1002/cpmb.108', '10.1002/cpmb.105', '10.1002/cpz1.1068', '10.1002/cpz1.1062', '10.1002/cpz1.921', '10.1002/cpz1.920', '10.1002/cpz1.800', '10.1002/cpz1.765', '10.1002/cpz1.509', '10.1002/cpz1.488', '10.1002/cpz1.239', '10.1002/cpz1.570', '10.1002/cpz1.147', '10.1002/cpz1.116', '10.1002/cpmo.65', '10.1002/cpmo.62', '10.1002/cpns.105', '10.1002/cpns.103', '10.1002/cpns.96', '10.1002/cpz1.1057', '10.1002/cpz1.996', '10.1002/cpz1.1008', '10.1002/cpz1.904', '10.1002/cpz1.972', '10.1002/cpz1.1040', '10.1002/cpz1.900', '10.1002/cpz1.841', '10.1002/cpz1.836', '10.1002/cpz1.786', '10.1002/cpz1.791', '10.1002/cpz1.719', '10.1002/cpz1.704', '10.1002/cpz1.688', '10.1002/cpz1.654', '10.1002/cpz1.493', '10.1002/cpz1.255', '10.1002/cpz1.1088', '10.1002/cpz1.1029', '10.1002/cpz1.878', '10.1002/cpz1.834', '10.1002/cpz1.740', '10.1002/cpz1.710', '10.1002/cpz1.612', '10.1002/cpz1.500', '10.1002/cpz1.39', '10.1002/cpnc.116', '10.1002/cpnc.108', '10.1002/cpz1.78', '10.1002/cpph.81', '10.1002/cpph.78', '10.1002/cpz1.1109', '10.1002/cpz1.544', '10.1002/cpph.77', '10.1002/cpph.69', '10.1002/cpph.59', '10.1002/cpz1.1025', '10.1002/cpz1.1005', '10.1002/cpz1.852', '10.1002/cpz1.840', '10.1002/cpz1.835', '10.1002/cpz1.831', '10.1002/cpz1.742', '10.1002/cpz1.757', '10.1002/cpz1.711', '10.1002/cpz1.650', '10.1002/cpz1.693', '10.1002/cpz1.695', '10.1002/cpz1.712', '10.1002/cpz1.692', '10.1002/cpz1.668', '10.1002/cpz1.601', '10.1002/cpz1.596', '10.1002/cpz1.915', '10.1002/cpz1.302', '10.1002/cpz1.272', '10.1002/cpz1.114', '10.1002/cpz1.127', '10.1002/cpz1.103', '10.1002/cpz1.65', '10.1002/cpz1.58', '10.1002/cppb.20118', '10.1002/cppb.20114', '10.1002/cppb.20108', '10.1002/cppb.20107', '10.1002/cppb.20106', '10.1002/cppb.20102', '10.1002/cppb.20101', '10.1002/cppb.20100', '10.1002/cppb.20099', '10.1002/cppb.20097', '10.1002/cppb.20090', '10.1002/cpz1.1090', '10.1002/cpz1.1054', '10.1002/cpz1.952', '10.1002/cpz1.903', '10.1002/cpz1.844', '10.1002/cpz1.705', '10.1002/cpz1.673', '10.1002/cpz1.620', '10.1002/cpz1.591', '10.1002/cpz1.598', '10.1002/cpz1.577', '10.1002/cpz1.562', '10.1002/cpz1.541', '10.1002/cpz1.425', '10.1002/cpz1.417', '10.1002/cpz1.371', '10.1002/cpz1.362', '10.1002/cpz1.191', '10.1002/cpz1.133', '10.1002/cpz1.134', '10.1002/cpz1.875', '10.1002/cpz1.927', '10.1002/cpz1.901', '10.1002/cpz1.908', '10.1002/cpsc.122', '10.1002/cpz1.1047', '10.1002/cpz1.694', '10.1002/cpz1.870', '10.1002/cpbi.83', '10.1002/cpcb.116', '10.1002/cpz1.965', '10.1002/cpz1.746', '10.1002/cpz1.208', '10.1002/cpz1.974', '10.1002/cpz1.962', '10.1002/cpz1.960', '10.1002/cpz1.966', '10.1002/cpz1.936', '10.1002/cpps.115', '10.1002/cpz1.519', '10.1002/cpz1.801', '10.1002/cpz1.762', '10.1002/cpz1.414', '10.1002/cpz1.401', '10.1002/cpz1.296', '10.1002/cpz1.186', '10.1002/cpz1.129', '10.1002/cpz1.55', '10.1002/cpps.114', '10.1002/cpz1.232', '10.1002/cpz1.137', '10.1002/cpz1.88', '10.1002/cpsc.120', '10.1002/cpsc.121', '10.1002/cpz1.622', '10.1002/cpsc.123', '10.1002/cpsc.124', '10.1002/cpsc.125', '10.1002/cpsc.127', '10.1002/cpsc.128', '10.1002/cpsc.117', '10.1002/cpsc.116', '10.1002/cpsc.115', '10.1002/cpsc.108', '10.1002/cpsc.102', '10.1002/cpsc.99', '10.1002/cpz1.1012', '10.1002/cpz1.979', '10.1002/cpz1.877', '10.1002/cpz1.850', '10.1002/cpz1.759', '10.1002/cpz1.714', '10.1002/cpz1.606', '10.1002/cpz1.565', '10.1002/cpz1.435', '10.1002/cpz1.423', '10.1002/cpz1.325', '10.1002/cpz1.290', '10.1002/cpz1.263', '10.1002/cpz1.244', '10.1002/cpz1.245', '10.1002/cpz1.1096', '10.1002/cpz1.1067', '10.1002/cpz1.1015', '10.1002/cpz1.975', '10.1002/cpz1.866', '10.1002/cpz1.744', '10.1002/cpz1.615', '10.1002/cpz1.573', '10.1002/cpz1.563', '10.1002/cpz1.555', '10.1002/cpz1.542', '10.1002/cpz1.533', '10.1002/cpz1.461', '10.1002/cpz1.357', '10.1002/cpz1.288', '10.1002/cpz1.158', '10.1002/cpz1.1099', '10.1002/cpz1.1065', '10.1002/cpz1.1055', '10.1002/cpz1.995', '10.1002/cptx.99', '10.1002/cptx.96', '10.1002/cptx.87', '10.1002/cpz1.672', '10.1002/cpz1.1094', '10.1002/cpz1.873', '10.1002/cpz1.640', '10.1002/cpz1.32', '10.1002/cpmc.130', '10.1002/cpmc.128', '10.1002/cpmb.102', '10.1002/cpz1.428', '10.1002/cpz1.224', '10.1002/cpmo.84', '10.1002/cppb.20117', '10.1002/cppb.20115', '10.1002/cpz1.341']



        filter_doi_list=['10.1002/cpz1.1060', '10.1002/cpz1.494', '10.1002/cpz1.1064', '10.1002/cpz1.442', '10.1002/cpz1.217', '10.1002/cpbi.87', '10.1002/cpbi.81', '10.1002/cpz1.419', '10.1002/cpz1.940', '10.1002/cpz1.986', '10.1002/cpz1.433', '10.1002/cpz1.898', '10.1002/cpz1.825', '10.1002/cpz1.625', '10.1002/cpz1.589', '10.1002/cpz1.221', '10.1002/cpz1.29', '10.1002/cpz1.931', '10.1002/cpz1.865', '10.1002/cpz1.1023', '10.1002/cpz1.951', '10.1002/cpz1.897', '10.1002/cpz1.734', '10.1002/cpz1.584', '10.1002/cpz1.366', '10.1002/cpz1.558', '10.1002/cpz1.561', '10.1002/cpz1.1098', '10.1002/cpz1.1024', '10.1002/cpz1.932', '10.1002/cpz1.465', '10.1002/cpz1.463', '10.1002/cpz1.368', '10.1002/cpmc.91', '10.1002/cpz1.1059', '10.1002/cpz1.1000', '10.1002/cpz1.882', '10.1002/cpz1.771', '10.1002/cpz1.645', '10.1002/cpz1.635', '10.1002/cpz1.421', '10.1002/cpz1.277', '10.1002/cpz1.174', '10.1002/cpz1.85', '10.1002/cpmb.131', '10.1002/cpmb.124', '10.1002/cpmb.108', '10.1002/cpz1.1057', '10.1002/cpz1.719', '10.1002/cpz1.704', '10.1002/cpz1.688', '10.1002/cpz1.654', '10.1002/cpz1.1029', '10.1002/cpph.77', '10.1002/cpph.59', '10.1002/cpz1.835', '10.1002/cpz1.831', '10.1002/cpz1.650', '10.1002/cpz1.668', '10.1002/cpz1.692', '10.1002/cpz1.114', '10.1002/cppb.20114', '10.1002/cppb.20106', '10.1002/cppb.20102', '10.1002/cppb.20097', '10.1002/cppb.20090', '10.1002/cpz1.1090', '10.1002/cpz1.598', '10.1002/cpz1.927', '10.1002/cpch.80', '10.1002/cpz1.557', '10.1002/cpim.111', '10.1002/cpcb.116', '10.1002/cpz1.974', '10.1002/cpz1.962', '10.1002/cpz1.801', '10.1002/cpz1.129', '10.1002/cpz1.622', '10.1002/cpsc.128', '10.1002/cpsc.117', '10.1002/cpz1.565', '10.1002/cpz1.744', '10.1002/cptx.96', '10.1002/cpz1.357', '10.1002/cpz1.158', '10.1002/cptx.87']


        session = db.session
        fail_list=[]

        fail_not_hava_list = ['10.1002/cpz1.217', '10.1002/cpbi.87', '10.1002/cpbi.81', '10.1002/cpz1.221', '10.1002/cpmc.91', '10.1002/cpz1.277', '10.1002/cpz1.174', '10.1002/cpmb.131', '10.1002/cpmb.124', '10.1002/cpmb.108', '10.1002/cpph.77', '10.1002/cpph.59', '10.1002/cpz1.114', '10.1002/cppb.20114', '10.1002/cppb.20106', '10.1002/cppb.20102', '10.1002/cppb.20097', '10.1002/cppb.20090', '10.1002/cpch.80', '10.1002/cpim.111', '10.1002/cpcb.116', '10.1002/cpsc.128', '10.1002/cpsc.117', '10.1002/cptx.96', '10.1002/cpz1.158', '10.1002/cptx.87']

        success_list = ['10.1002/cpz1.275', '10.1002/cpz1.139', '10.1002/cpz1.697', '10.1002/cpz1.671', '10.1002/cpz1.682', '10.1002/cpz1.664', '10.1002/cpz1.1060', '10.1002/cpz1.700', '10.1002/cpz1.1064', '10.1002/cpz1.1045', '10.1002/cpz1.1028', '10.1002/cpcb.99', '10.1002/cpz1.604', '10.1002/cpz1.621', '10.1002/cpz1.506', '10.1002/cpz1.494', '10.1002/cpz1.484', '10.1002/cpz1.442', '10.1002/cpz1.411', '10.1002/cpz1.373', '10.1002/cpz1.355', '10.1002/cpz1.323', '10.1002/cpz1.305', '10.1002/cpz1.270', '10.1002/cpz1.258', '10.1002/cpz1.252', '10.1002/cpz1.218', '10.1002/cpz1.217', '10.1002/cpz1.192', '10.1002/cpz1.60', '10.1002/cpz1.45', '10.1002/cpbi.108', '10.1002/cpbi.106', '10.1002/cpbi.105', '10.1002/cpbi.104', '10.1002/cpbi.103', '10.1002/cpbi.100', '10.1002/cpbi.99', '10.1002/cpbi.97', '10.1002/cpbi.90', '10.1002/cpbi.89', '10.1002/cpbi.87', '10.1002/cpbi.81', '10.1002/cpz1.393', '10.1002/cpz1.308', '10.1002/cpz1.157', '10.1002/cpz1.139', '10.1002/cpcb.113', '10.1002/cpcb.104', '10.1002/cpcb.105', '10.1002/cpz1.487', '10.1002/cpcy.72', '10.1002/cpz1.940', '10.1002/cpz1.930', '10.1002/cpz1.922', '10.1002/cpz1.876', '10.1002/cpz1.722', '10.1002/cpz1.733', '10.1002/cpz1.731', '10.1002/cpcb.98', '10.1002/cpcb.95', '10.1002/cpcb.56', '10.1002/cpz1.490', '10.1002/cpch.86', '10.1002/cpz1.419', '10.1002/cpch.80', '10.1002/cpch.78', '10.1002/cpch.71', '10.1002/cpz1.986', '10.1002/cpz1.663', '10.1002/cpz1.1070', '10.1002/cpz1.113', '10.1002/cpz1.46', '10.1002/cpz1.59', '10.1002/cpz1.943', '10.1002/cpz1.942', '10.1002/cpz1.859', '10.1002/cpz1.794', '10.1002/cpz1.788', '10.1002/cpz1.774', '10.1002/cpz1.718', '10.1002/cpz1.739', '10.1002/cpz1.724', '10.1002/cpz1.536', '10.1002/cpz1.524', '10.1002/cpz1.485', '10.1002/cpz1.433', '10.1002/cpz1.408', '10.1002/cpz1.957', '10.1002/cpz1.822', '10.1002/cpz1.559', '10.1002/cpz1.945', '10.1002/cpz1.898', '10.1002/cpz1.825', '10.1002/cpz1.785', '10.1002/cpz1.1036', '10.1002/cpz1.745', '10.1002/cpz1.713', '10.1002/cpz1.689', '10.1002/cpz1.625', '10.1002/cpz1.589', '10.1002/cpz1.508', '10.1002/cpz1.400', '10.1002/cpz1.222', '10.1002/cpcy.75', '10.1002/cpcy.73', '10.1002/cpcy.66', '10.1002/cpz1.1042', '10.1002/cpz1.891', '10.1002/cpz1.727', '10.1002/cpz1.221', '10.1002/cpz1.1046', '10.1002/cpz1.29', '10.1002/cpet.46', '10.1002/cpet.36', '10.1002/cpet.35', '10.1002/cpz1.1087', '10.1002/cpz1.977', '10.1002/cpz1.953', '10.1002/cpz1.931', '10.1002/cpz1.906', '10.1002/cpz1.888', '10.1002/cpz1.865', '10.1002/cpz1.857', '10.1002/cpz1.818', '10.1002/cpz1.696', '10.1002/cpz1.963', '10.1002/cpz1.564', '10.1002/cpz1.997', '10.1002/cpz1.443', '10.1002/cpz1.462', '10.1002/cpz1.440', '10.1002/cpz1.427', '10.1002/cpz1.392', '10.1002/cpz1.149', '10.1002/cpz1.111', '10.1002/cphg.105', '10.1002/cpz1.1053', '10.1002/cpz1.1023', '10.1002/cpz1.1022', '10.1002/cpz1.985', '10.1002/cpz1.993', '10.1002/cpz1.991', '10.1002/cpz1.987', '10.1002/cpz1.958', '10.1002/cpz1.951', '10.1002/cpz1.1092', '10.1002/cpz1.933', '10.1002/cpz1.925', '10.1002/cpz1.897', '10.1002/cpz1.734', '10.1002/cpz1.864', '10.1002/cpz1.824', '10.1002/cpz1.783', '10.1002/cpz1.613', '10.1002/cpz1.584', '10.1002/cpz1.685', '10.1002/cpz1.557', '10.1002/cpz1.558', '10.1002/cpz1.1035', '10.1002/cpz1.561', '10.1002/cpz1.515', '10.1002/cpz1.505', '10.1002/cpz1.504', '10.1002/cpz1.516', '10.1002/cpz1.456', '10.1002/cpz1.407', '10.1002/cpz1.366', '10.1002/cpz1.359', '10.1002/cpz1.311', '10.1002/cpz1.251', '10.1002/cpz1.144', '10.1002/cpz1.934', '10.1002/cpim.111', '10.1002/cpim.106', '10.1002/cpim.104', '10.1002/cpim.100', '10.1002/cpim.93', '10.1002/cpim.85', '10.1002/cpz1.1098', '10.1002/cpz1.1069', '10.1002/cpz1.871', '10.1002/cpz1.1034', '10.1002/cpz1.1039', '10.1002/cpz1.1021', '10.1002/cpz1.1024', '10.1002/cpz1.1007', '10.1002/cpz1.932', '10.1002/cpz1.950', '10.1002/cpz1.954', '10.1002/cpz1.937', '10.1002/cpz1.912', '10.1002/cpz1.853', '10.1002/cpz1.828', '10.1002/cpz1.737', '10.1002/cpz1.716', '10.1002/cpz1.702', '10.1002/cpz1.642', '10.1002/cpz1.639', '10.1002/cpz1.588', '10.1002/cpz1.548', '10.1002/cpz1.523', '10.1002/cpz1.465', '10.1002/cpz1.463', '10.1002/cpz1.448', '10.1002/cpz1.453', '10.1002/cpz1.368', '10.1002/cpz1.309', '10.1002/cpz1.257', '10.1002/cpz1.145', '10.1002/cpz1.57', '10.1002/cpz1.44', '10.1002/cpz1.691', '10.1002/cpmc.112', '10.1002/cpmc.105', '10.1002/cpmc.100', '10.1002/cpmc.91', '10.1002/cpmc.89', '10.1002/cpmc.90', '10.1002/cpmc.88', '10.1002/cpmc.87', '10.1002/cpmb.100', '10.1002/cpmc.86', '10.1002/cpz1.1059', '10.1002/cpz1.1000', '10.1002/cpz1.1017', '10.1002/cpz1.1016', '10.1002/cpz1.970', '10.1002/cpz1.947', '10.1002/cpz1.882', '10.1002/cpz1.843', '10.1002/cpz1.805', '10.1002/cpz1.798', '10.1002/cpz1.753', '10.1002/cpz1.771', '10.1002/cpns.88', '10.1002/cpz1.76', '10.1002/cpz1.919', '10.1002/cpz1.761', '10.1002/cpz1.690', '10.1002/cpz1.683', '10.1002/cpz1.645', '10.1002/cpz1.635', '10.1002/cpz1.595', '10.1002/cpz1.532', '10.1002/cpz1.535', '10.1002/cpz1.421', '10.1002/cpz1.351', '10.1002/cpz1.316', '10.1002/cpz1.277', '10.1002/cpz1.266', '10.1002/cpz1.667', '10.1002/cpz1.236', '10.1002/cpz1.207', '10.1002/cpz1.174', '10.1002/cpz1.198', '10.1002/cpz1.187', '10.1002/cpz1.159', '10.1002/cpz1.130', '10.1002/cpz1.85', '10.1002/cpmb.131', '10.1002/cpmb.125', '10.1002/cpmb.124', '10.1002/cpmb.115', '10.1002/cpmb.108', '10.1002/cpmb.105', '10.1002/cpz1.1068', '10.1002/cpz1.1062', '10.1002/cpz1.921', '10.1002/cpz1.920', '10.1002/cpz1.800', '10.1002/cpz1.765', '10.1002/cpz1.509', '10.1002/cpz1.488', '10.1002/cpz1.239', '10.1002/cpz1.570', '10.1002/cpz1.147', '10.1002/cpz1.116', '10.1002/cpmo.65', '10.1002/cpmo.62', '10.1002/cpns.105', '10.1002/cpns.103', '10.1002/cpns.96', '10.1002/cpz1.1057', '10.1002/cpz1.996', '10.1002/cpz1.1008', '10.1002/cpz1.904', '10.1002/cpz1.972', '10.1002/cpz1.1040', '10.1002/cpz1.900', '10.1002/cpz1.841', '10.1002/cpz1.836', '10.1002/cpz1.786', '10.1002/cpz1.791', '10.1002/cpz1.719', '10.1002/cpz1.704', '10.1002/cpz1.688', '10.1002/cpz1.654', '10.1002/cpz1.493', '10.1002/cpz1.255', '10.1002/cpz1.1088', '10.1002/cpz1.1029', '10.1002/cpz1.878', '10.1002/cpz1.834', '10.1002/cpz1.740', '10.1002/cpz1.710', '10.1002/cpz1.612', '10.1002/cpz1.500', '10.1002/cpz1.39', '10.1002/cpnc.116', '10.1002/cpnc.108', '10.1002/cpz1.78', '10.1002/cpph.81', '10.1002/cpph.78', '10.1002/cpz1.1109', '10.1002/cpz1.544', '10.1002/cpph.77', '10.1002/cpph.69', '10.1002/cpph.59', '10.1002/cpz1.1025', '10.1002/cpz1.1005', '10.1002/cpz1.852', '10.1002/cpz1.840', '10.1002/cpz1.835', '10.1002/cpz1.831', '10.1002/cpz1.742', '10.1002/cpz1.757', '10.1002/cpz1.711', '10.1002/cpz1.650', '10.1002/cpz1.693', '10.1002/cpz1.695', '10.1002/cpz1.712', '10.1002/cpz1.692', '10.1002/cpz1.668', '10.1002/cpz1.601', '10.1002/cpz1.596', '10.1002/cpz1.915', '10.1002/cpz1.302', '10.1002/cpz1.272', '10.1002/cpz1.114', '10.1002/cpz1.127', '10.1002/cpz1.103', '10.1002/cpz1.65', '10.1002/cpz1.58', '10.1002/cppb.20118', '10.1002/cppb.20114', '10.1002/cppb.20108', '10.1002/cppb.20107', '10.1002/cppb.20106', '10.1002/cppb.20102', '10.1002/cppb.20101', '10.1002/cppb.20100', '10.1002/cppb.20099', '10.1002/cppb.20097', '10.1002/cppb.20090', '10.1002/cpz1.1090', '10.1002/cpz1.1054', '10.1002/cpz1.952', '10.1002/cpz1.903', '10.1002/cpz1.844', '10.1002/cpz1.705', '10.1002/cpz1.673', '10.1002/cpz1.620', '10.1002/cpz1.591', '10.1002/cpz1.598', '10.1002/cpz1.577', '10.1002/cpz1.562', '10.1002/cpz1.541', '10.1002/cpz1.425', '10.1002/cpz1.417', '10.1002/cpz1.371', '10.1002/cpz1.362', '10.1002/cpz1.191', '10.1002/cpz1.133', '10.1002/cpz1.134', '10.1002/cpz1.875', '10.1002/cpz1.927', '10.1002/cpz1.901', '10.1002/cpz1.908', '10.1002/cpsc.122', '10.1002/cpz1.1047', '10.1002/cpz1.694', '10.1002/cpz1.870', '10.1002/cpbi.83', '10.1002/cpcb.116', '10.1002/cpz1.965', '10.1002/cpz1.746', '10.1002/cpz1.208', '10.1002/cpz1.974', '10.1002/cpz1.962', '10.1002/cpz1.960', '10.1002/cpz1.966', '10.1002/cpz1.936', '10.1002/cpps.115', '10.1002/cpz1.519', '10.1002/cpz1.801', '10.1002/cpz1.762', '10.1002/cpz1.414', '10.1002/cpz1.401', '10.1002/cpz1.296', '10.1002/cpz1.186', '10.1002/cpz1.129', '10.1002/cpz1.55', '10.1002/cpps.114', '10.1002/cpz1.232', '10.1002/cpz1.137', '10.1002/cpz1.88', '10.1002/cpsc.120', '10.1002/cpsc.121', '10.1002/cpz1.622', '10.1002/cpsc.123', '10.1002/cpsc.124', '10.1002/cpsc.125', '10.1002/cpsc.127', '10.1002/cpsc.128', '10.1002/cpsc.117', '10.1002/cpsc.116', '10.1002/cpsc.115', '10.1002/cpsc.108', '10.1002/cpsc.102', '10.1002/cpsc.99', '10.1002/cpz1.1012', '10.1002/cpz1.979', '10.1002/cpz1.877', '10.1002/cpz1.850', '10.1002/cpz1.759', '10.1002/cpz1.714', '10.1002/cpz1.606', '10.1002/cpz1.565', '10.1002/cpz1.435', '10.1002/cpz1.423', '10.1002/cpz1.325', '10.1002/cpz1.290', '10.1002/cpz1.263', '10.1002/cpz1.244', '10.1002/cpz1.245', '10.1002/cpz1.1096', '10.1002/cpz1.1067', '10.1002/cpz1.1015', '10.1002/cpz1.975', '10.1002/cpz1.866', '10.1002/cpz1.744', '10.1002/cpz1.615', '10.1002/cpz1.573', '10.1002/cpz1.563', '10.1002/cpz1.555', '10.1002/cpz1.542', '10.1002/cpz1.533', '10.1002/cpz1.461', '10.1002/cpz1.357', '10.1002/cpz1.288', '10.1002/cpz1.158', '10.1002/cpz1.1099', '10.1002/cpz1.1065', '10.1002/cpz1.1055', '10.1002/cpz1.995', '10.1002/cptx.99', '10.1002/cptx.96', '10.1002/cptx.87', '10.1002/cpz1.672', '10.1002/cpz1.1094', '10.1002/cpz1.873', '10.1002/cpz1.640', '10.1002/cpz1.32', '10.1002/cpmc.130', '10.1002/cpmc.128', '10.1002/cpmb.102', '10.1002/cpz1.428', '10.1002/cpz1.224', '10.1002/cpmo.84', '10.1002/cppb.20117', '10.1002/cppb.20115', '10.1002/cpz1.341']

        success_len=len(success_list)
        print(f'has already success {success_len} data')
        i=0
        for doi in doi_list:
            try:
                print(f'this is index {i} data')
                i=i+1
                if doi in success_list:
                    continue
                if doi in fail_list:
                    continue

                print(f'start to crawl doi is {doi}')
                original_data = OriginalDataCurrentProtocol.query.filter_by(doi=doi).first()
                # 访问目标网址
                url = f'https://doi.org/{doi}'  # 替换为目标文件的 URL
                # driver = uc.Chrome();
                driver = get_driver('./', False)
                driver.get(url)
                content=original_data.content
                is_click_cited=True
                original_soup = BeautifulSoup(content, 'html.parser')
                if doi in filter_doi_list:

                    equation=original_soup.find_all('span',class_='fallback__mathEquation')
                cited_literature=original_soup.find('section',class_='article-section article-section__citedBy cited-by')
                if not cited_literature:
                    is_click_cited=False
                # 滚动页面到底部

                time.sleep(3)

                element = WebDriverWait(driver, 1000).until(
                    EC.presence_of_element_located((By.CLASS_NAME,
                                                         'article__body '))
                )
                total_height = int(driver.execute_script("return document.body.scrollHeight"))
                total_height=total_height-1400
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
                # literature_cited_element.click()
                if doi in filter_doi_list:
                    load_annotations(driver,len(equation))
                    new_count = len(driver.find_elements(By.TAG_NAME, 'annotation'))

                    if new_count == 0:
                        # driver.quit()
                        if doi in fail_not_hava_list:
                            fail_not_hava_list.append(doi)
                            print(f'doi not have equation already in list,doi is {doi} continue to update')
                        else:

                            print(f'fail to crawl doi,doi not have equation,doi is {doi} continue to update')
                else:
                    load_drivger(driver)



                soup = BeautifulSoup(driver.page_source, 'html.parser')

                text = soup.find(class_='page-body pagefulltext')
                original_data.content = str(text)
                session.commit()
                driver.quit()
                success_list.append(doi)
            except Exception as e:
                # raise e
                fail_list.append(doi)
                continue


    finally:
        print(fail_list)
        print(fail_not_hava_list)
        print(success_list)
        session.close()

    # open('./md_back/content.md_back', 'w').write(content_tag)

    return 'ok'


def load_annotations(driver,total):
    index=0
    while True:
        index=index+1

        driver.execute_script("window.scrollTo(0, 0);")
        scroll_and_load_more(driver)
        # 等待一段时间，让动态内容加载
        # element = WebDriverWait(driver, 1000).until(
        #     EC.presence_of_all_elements_located((By.TAG_NAME,
        #                                          'annotation'))
        # )

        # 获取当前页面的 <annotation> 标签数量
        new_count = len(driver.find_elements(By.TAG_NAME, 'annotation'))

        # 如果没有新的 <annotation> 标签加载，则退出循环
        if new_count == total:
            break
        if index>3 and new_count==0:
            break

        if index>8 :
            break

def load_drivger(driver):
    index=0
    while True:
        index=index+1

        driver.execute_script("window.scrollTo(0, 0);")
        scroll_and_load_more(driver)

        if index>0 :
            break




def scroll_and_load_more(driver):
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    current_height = 200
    last_height=total_height
    while True:
        # 逐步增加滚动距离
        driver.execute_script(f"window.scrollTo(0, {current_height});")
        current_height += 200  # 每次增加 100 像素
        time.sleep(0.1)  # 等待 0.1 秒，以便模拟平滑滚动

        # 检查页面是否加载了新内容
        new_height = int(driver.execute_script("return document.body.scrollHeight"))
        if new_height > last_height :
            last_height = new_height
            time.sleep(3)  # 等待一段时间，让新内容加载
        elif current_height<=last_height:
            time.sleep(0.1)
        else:
            break


@current_deal.route('/crawel/clean/redownload_all_resource')
def redownload_all_resource():
    try:

        session = db.session
        doi_list = ['10.1002/cpz1.275','10.1002/cpz1.139',
            '10.1002/cpz1.697', '10.1002/cpz1.671', '10.1002/cpz1.682', '10.1002/cpz1.664', '10.1002/cpz1.1060',
                    '10.1002/cpz1.700', '10.1002/cpz1.1064', '10.1002/cpz1.1045', '10.1002/cpz1.1028',
                    '10.1002/cpcb.99', '10.1002/cpz1.604', '10.1002/cpz1.621', '10.1002/cpz1.506', '10.1002/cpz1.494',
                    '10.1002/cpz1.484', '10.1002/cpz1.442', '10.1002/cpz1.411', '10.1002/cpz1.373', '10.1002/cpz1.355',
                    '10.1002/cpz1.323', '10.1002/cpz1.305', '10.1002/cpz1.270', '10.1002/cpz1.258', '10.1002/cpz1.252',
                    '10.1002/cpz1.218', '10.1002/cpz1.217', '10.1002/cpz1.192', '10.1002/cpz1.60', '10.1002/cpz1.45',
                    '10.1002/cpbi.108', '10.1002/cpbi.106', '10.1002/cpbi.105', '10.1002/cpbi.104', '10.1002/cpbi.103',
                    '10.1002/cpbi.100', '10.1002/cpbi.99', '10.1002/cpbi.97', '10.1002/cpbi.90', '10.1002/cpbi.89',
                    '10.1002/cpbi.87', '10.1002/cpbi.81', '10.1002/cpz1.393', '10.1002/cpz1.308', '10.1002/cpz1.157',
                    '10.1002/cpz1.139', '10.1002/cpcb.113', '10.1002/cpcb.104', '10.1002/cpcb.105', '10.1002/cpz1.487',
                    '10.1002/cpcy.72', '10.1002/cpz1.940', '10.1002/cpz1.930', '10.1002/cpz1.922', '10.1002/cpz1.876',
                    '10.1002/cpz1.722', '10.1002/cpz1.733', '10.1002/cpz1.731', '10.1002/cpcb.98', '10.1002/cpcb.95',
                    '10.1002/cpcb.56', '10.1002/cpz1.490', '10.1002/cpch.86', '10.1002/cpz1.419', '10.1002/cpch.80',
                    '10.1002/cpch.78', '10.1002/cpch.71', '10.1002/cpz1.986', '10.1002/cpz1.663', '10.1002/cpz1.1070',
                    '10.1002/cpz1.113', '10.1002/cpz1.46', '10.1002/cpz1.59', '10.1002/cpz1.943', '10.1002/cpz1.942',
                    '10.1002/cpz1.859', '10.1002/cpz1.794', '10.1002/cpz1.788', '10.1002/cpz1.774', '10.1002/cpz1.718',
                    '10.1002/cpz1.739', '10.1002/cpz1.724', '10.1002/cpz1.536', '10.1002/cpz1.524', '10.1002/cpz1.485',
                    '10.1002/cpz1.433', '10.1002/cpz1.408', '10.1002/cpz1.957', '10.1002/cpz1.822', '10.1002/cpz1.559',
                    '10.1002/cpz1.945', '10.1002/cpz1.898', '10.1002/cpz1.825', '10.1002/cpz1.785', '10.1002/cpz1.1036',
                    '10.1002/cpz1.745', '10.1002/cpz1.713', '10.1002/cpz1.689', '10.1002/cpz1.625', '10.1002/cpz1.589',
                    '10.1002/cpz1.508', '10.1002/cpz1.400', '10.1002/cpz1.222', '10.1002/cpcy.75', '10.1002/cpcy.73',
                    '10.1002/cpcy.66', '10.1002/cpz1.1042', '10.1002/cpz1.891', '10.1002/cpz1.727', '10.1002/cpz1.221',
                    '10.1002/cpz1.1046', '10.1002/cpz1.29', '10.1002/cpet.46', '10.1002/cpet.36', '10.1002/cpet.35',
                    '10.1002/cpz1.1087', '10.1002/cpz1.977', '10.1002/cpz1.953', '10.1002/cpz1.931', '10.1002/cpz1.906',
                    '10.1002/cpz1.888', '10.1002/cpz1.865', '10.1002/cpz1.857', '10.1002/cpz1.818', '10.1002/cpz1.696',
                    '10.1002/cpz1.963', '10.1002/cpz1.564', '10.1002/cpz1.997', '10.1002/cpz1.443', '10.1002/cpz1.462',
                    '10.1002/cpz1.440', '10.1002/cpz1.427', '10.1002/cpz1.392', '10.1002/cpz1.149', '10.1002/cpz1.111',
                    '10.1002/cphg.105', '10.1002/cpz1.1053', '10.1002/cpz1.1023', '10.1002/cpz1.1022',
                    '10.1002/cpz1.985', '10.1002/cpz1.993', '10.1002/cpz1.991', '10.1002/cpz1.987', '10.1002/cpz1.958',
                    '10.1002/cpz1.951', '10.1002/cpz1.1092', '10.1002/cpz1.933', '10.1002/cpz1.925', '10.1002/cpz1.897',
                    '10.1002/cpz1.734', '10.1002/cpz1.864', '10.1002/cpz1.824', '10.1002/cpz1.783', '10.1002/cpz1.613',
                    '10.1002/cpz1.584', '10.1002/cpz1.685', '10.1002/cpz1.557', '10.1002/cpz1.558', '10.1002/cpz1.1035',
                    '10.1002/cpz1.561', '10.1002/cpz1.515', '10.1002/cpz1.505', '10.1002/cpz1.504', '10.1002/cpz1.516',
                    '10.1002/cpz1.456', '10.1002/cpz1.407', '10.1002/cpz1.366', '10.1002/cpz1.359', '10.1002/cpz1.311',
                    '10.1002/cpz1.251', '10.1002/cpz1.144', '10.1002/cpz1.934', '10.1002/cpim.111', '10.1002/cpim.106',
                    '10.1002/cpim.104', '10.1002/cpim.100', '10.1002/cpim.93', '10.1002/cpim.85', '10.1002/cpz1.1098',
                    '10.1002/cpz1.1069', '10.1002/cpz1.871', '10.1002/cpz1.1034', '10.1002/cpz1.1039',
                    '10.1002/cpz1.1021', '10.1002/cpz1.1024', '10.1002/cpz1.1007', '10.1002/cpz1.932',
                    '10.1002/cpz1.950', '10.1002/cpz1.954', '10.1002/cpz1.937', '10.1002/cpz1.912', '10.1002/cpz1.853',
                    '10.1002/cpz1.828', '10.1002/cpz1.737', '10.1002/cpz1.716', '10.1002/cpz1.702', '10.1002/cpz1.642',
                    '10.1002/cpz1.639', '10.1002/cpz1.588', '10.1002/cpz1.548', '10.1002/cpz1.523', '10.1002/cpz1.465',
                    '10.1002/cpz1.463', '10.1002/cpz1.448', '10.1002/cpz1.453', '10.1002/cpz1.368', '10.1002/cpz1.309',
                    '10.1002/cpz1.257', '10.1002/cpz1.145', '10.1002/cpz1.57', '10.1002/cpz1.44', '10.1002/cpz1.691',
                    '10.1002/cpmc.128', '10.1002/cpmc.112', '10.1002/cpmc.105', '10.1002/cpmc.100', '10.1002/cpmc.91',
                    '10.1002/cpmc.89', '10.1002/cpmc.90', '10.1002/cpmc.88', '10.1002/cpmc.87', '10.1002/cpmb.100',
                    '10.1002/cpmc.86', '10.1002/cpz1.1059', '10.1002/cpz1.1000', '10.1002/cpz1.1017',
                    '10.1002/cpz1.1016', '10.1002/cpz1.970', '10.1002/cpz1.947', '10.1002/cpz1.882', '10.1002/cpz1.843',
                    '10.1002/cpz1.805', '10.1002/cpz1.798', '10.1002/cpz1.753', '10.1002/cpz1.771', '10.1002/cpns.88',
                    '10.1002/cpz1.76', '10.1002/cpz1.919', '10.1002/cpz1.761', '10.1002/cpz1.690', '10.1002/cpz1.683',
                    '10.1002/cpz1.645', '10.1002/cpz1.635', '10.1002/cpz1.595', '10.1002/cpz1.532', '10.1002/cpz1.535',
                    '10.1002/cpz1.421', '10.1002/cpz1.351', '10.1002/cpz1.316', '10.1002/cpz1.277', '10.1002/cpz1.266',
                    '10.1002/cpz1.667', '10.1002/cpz1.236', '10.1002/cpz1.207', '10.1002/cpz1.174', '10.1002/cpz1.198',
                    '10.1002/cpz1.187', '10.1002/cpz1.159', '10.1002/cpz1.130', '10.1002/cpz1.85', '10.1002/cpmb.131',
                    '10.1002/cpmb.125', '10.1002/cpmb.124', '10.1002/cpmb.115', '10.1002/cpmb.108', '10.1002/cpmb.102',
                    '10.1002/cpmb.105', '10.1002/cpz1.1068', '10.1002/cpz1.1062', '10.1002/cpz1.921',
                    '10.1002/cpz1.920', '10.1002/cpz1.800', '10.1002/cpz1.765', '10.1002/cpz1.509', '10.1002/cpz1.488',
                    '10.1002/cpz1.428', '10.1002/cpz1.239', '10.1002/cpz1.570', '10.1002/cpz1.224', '10.1002/cpz1.147',
                    '10.1002/cpz1.116', '10.1002/cpmo.84', '10.1002/cpmo.65', '10.1002/cpmo.62', '10.1002/cpns.105',
                    '10.1002/cpns.103', '10.1002/cpns.96', '10.1002/cpz1.1057', '10.1002/cpz1.996', '10.1002/cpz1.1008',
                    '10.1002/cpz1.904', '10.1002/cpz1.972', '10.1002/cpz1.1040', '10.1002/cpz1.900', '10.1002/cpz1.841',
                    '10.1002/cpz1.836', '10.1002/cpz1.786', '10.1002/cpz1.791', '10.1002/cpz1.719', '10.1002/cpz1.704',
                    '10.1002/cpz1.688', '10.1002/cpz1.654', '10.1002/cpz1.493', '10.1002/cpz1.255', '10.1002/cpz1.1088',
                    '10.1002/cpz1.1029', '10.1002/cpz1.878', '10.1002/cpz1.834', '10.1002/cpz1.740', '10.1002/cpz1.710',
                    '10.1002/cpz1.612', '10.1002/cpz1.500', '10.1002/cpz1.39', '10.1002/cpnc.116', '10.1002/cpnc.108',
                    '10.1002/cpz1.78', '10.1002/cpph.81', '10.1002/cpph.78', '10.1002/cpz1.1109', '10.1002/cpz1.544',
                    '10.1002/cpph.77', '10.1002/cpph.69', '10.1002/cpph.59', '10.1002/cpz1.1025', '10.1002/cpz1.1005',
                    '10.1002/cpz1.852', '10.1002/cpz1.840', '10.1002/cpz1.835', '10.1002/cpz1.831', '10.1002/cpz1.742',
                    '10.1002/cpz1.757', '10.1002/cpz1.711', '10.1002/cpz1.650', '10.1002/cpz1.693', '10.1002/cpz1.695',
                    '10.1002/cpz1.712', '10.1002/cpz1.692', '10.1002/cpz1.668', '10.1002/cpz1.601', '10.1002/cpz1.596',
                    '10.1002/cpz1.915', '10.1002/cpz1.302', '10.1002/cpz1.272', '10.1002/cpz1.114', '10.1002/cpz1.127',
                    '10.1002/cpz1.103', '10.1002/cpz1.65', '10.1002/cpz1.58', '10.1002/cppb.20118',
                    '10.1002/cppb.20117', '10.1002/cppb.20115', '10.1002/cppb.20114', '10.1002/cppb.20108',
                    '10.1002/cppb.20107', '10.1002/cppb.20106', '10.1002/cppb.20102', '10.1002/cppb.20101',
                    '10.1002/cppb.20100', '10.1002/cppb.20099', '10.1002/cppb.20097', '10.1002/cppb.20090',
                    '10.1002/cpz1.1090', '10.1002/cpz1.1054', '10.1002/cpz1.952', '10.1002/cpz1.903',
                    '10.1002/cpz1.844', '10.1002/cpz1.705', '10.1002/cpz1.673', '10.1002/cpz1.620', '10.1002/cpz1.591',
                    '10.1002/cpz1.598', '10.1002/cpz1.577', '10.1002/cpz1.562', '10.1002/cpz1.541', '10.1002/cpz1.425',
                    '10.1002/cpz1.417', '10.1002/cpz1.371', '10.1002/cpz1.362', '10.1002/cpz1.191', '10.1002/cpz1.133',
                    '10.1002/cpz1.134', '10.1002/cpz1.875', '10.1002/cpz1.927', '10.1002/cpz1.901', '10.1002/cpz1.908',
                    '10.1002/cpsc.122', '10.1002/cpz1.1047', '10.1002/cpz1.694', '10.1002/cpz1.870', '10.1002/cpbi.83',
                    '10.1002/cpcb.116', '10.1002/cpz1.965', '10.1002/cpz1.746', '10.1002/cpz1.208', '10.1002/cpz1.974',
                    '10.1002/cpz1.962', '10.1002/cpz1.960', '10.1002/cpz1.966', '10.1002/cpz1.936', '10.1002/cpps.115',
                    '10.1002/cpz1.519', '10.1002/cpz1.801', '10.1002/cpz1.762', '10.1002/cpz1.414', '10.1002/cpz1.401',
                    '10.1002/cpz1.296', '10.1002/cpz1.186', '10.1002/cpz1.129', '10.1002/cpz1.55', '10.1002/cpps.114',
                    '10.1002/cpz1.232', '10.1002/cpz1.137', '10.1002/cpz1.88', '10.1002/cpsc.120', '10.1002/cpsc.121',
                    '10.1002/cpz1.622', '10.1002/cpsc.123', '10.1002/cpsc.124', '10.1002/cpsc.125', '10.1002/cpsc.127',
                    '10.1002/cpsc.128', '10.1002/cpsc.117', '10.1002/cpsc.116', '10.1002/cpsc.115', '10.1002/cpsc.108',
                    '10.1002/cpsc.102', '10.1002/cpsc.99', '10.1002/cpz1.1012', '10.1002/cpz1.979', '10.1002/cpz1.877',
                    '10.1002/cpz1.850', '10.1002/cpz1.759', '10.1002/cpz1.714', '10.1002/cpz1.606', '10.1002/cpz1.565',
                    '10.1002/cpz1.435', '10.1002/cpz1.341', '10.1002/cpz1.423', '10.1002/cpz1.325',
                    '10.1002/cpz1.290', '10.1002/cpz1.263', '10.1002/cpz1.244', '10.1002/cpz1.245', '10.1002/cpz1.1096',
                    '10.1002/cpz1.1067', '10.1002/cpz1.1015', '10.1002/cpz1.975', '10.1002/cpz1.866',
                    '10.1002/cpz1.744', '10.1002/cpz1.615', '10.1002/cpz1.573', '10.1002/cpz1.563', '10.1002/cpz1.555',
                    '10.1002/cpz1.542', '10.1002/cpz1.533', '10.1002/cpz1.461', '10.1002/cpz1.357', '10.1002/cpz1.288',
                    '10.1002/cpz1.158', '10.1002/cpz1.1099', '10.1002/cpz1.1065', '10.1002/cpz1.1055',
                    '10.1002/cpz1.995', '10.1002/cptx.99', '10.1002/cptx.96', '10.1002/cptx.87', '10.1002/cpz1.672',
                    '10.1002/cpz1.1094', '10.1002/cpz1.873', '10.1002/cpz1.640', '10.1002/cpz1.32', '10.1002/cpmc.130']

        fail_list = []
        fail_url_list = []
        bucket_name = os.getenv('BUCKET_NAME')
        doi_list=['10.1002/cpz1.535']
        i=1
        for doi in doi_list:
            try:
                print(f'start to crawl index {i} literature')
                print(f'start to crawl to literature doi is {doi}')
                download_path = f'{LOG_FILE}/nature_protocol/resource/{doi}'
                if not os.path.exists(download_path):
                    os.makedirs(download_path)

                original_data = OriginalDataCurrentProtocol.query.filter_by(doi=doi).first()
                soup = BeautifulSoup(original_data.content, 'html.parser')
                doi_resources = CurrentProtocolResources.query.filter_by(doi=doi).all()
                name_list = []
                for resource in doi_resources:
                    oss_path = resource.oss_path
                    name = str(oss_path).split('/')[-1]
                    name_list.append(name)

                resource_all = get_all_resource_from_soup(soup)

                resource_filter_all = filter_resource_by_original_name(resource_all, name_list)
                # 设置下载路径
                resource_filter_all=[resource for resource in resource_filter_all if resource]

                seen = set()
                unique_data = []

                for item in resource_filter_all:
                    second_element = item[1]
                    if second_element not in seen:
                        unique_data.append(item)
                        seen.add(second_element)

                for resource in unique_data:
                    try:
                        time.sleep(0.1)
                        new_url=resource[1]
                        if not is_download( resource[1]):
                            print(f'{new_url}   is not supported')
                            continue
                        type = get_file_extension( resource[1])
                        if type == 'gif':
                            print(f'{new_url}   is not supported')
                            continue

                        download_file(bucket_name, doi, download_path, session, resource[1], resource[2],'all')
                    except Exception as e:
                        print(f'download file error: {e}  url is {resource[1]}')
                        # raise e
                        fail_url_list.append(doi)
                        continue


            except Exception as e:
                raise e
                fail_list.append(doi)
                continue
            finally:
                i=i+1


    finally:
        print(fail_list)
        session.close()

    # open('./md_back/content.md_back', 'w').write(content_tag)

    return 'ok'


@current_deal.route('/clean/data_current_protocol')
def clean_data_current_protocol():
    session = db.session
    cleanmission = CleanMission.query.filter_by(id=1).first()
    filter_doi_list = ['10.1002/cpz1.565', '10.1002/cpz1.158', '10.1002/cpz1.714', '10.1002/cpz1.606',
                       '10.1002/cpz1.245', '10.1002/cpz1.1067', '10.1002/cpz1.357', '10.1002/cptx.87', '10.1002/cpz1.563',
                       '10.1002/cptx.96', '10.1002/cpz1.696', '10.1002/cpz1.672', '10.1002/cpz1.1094', '10.1002/cpz1.113',
                       '10.1002/cpz1.1036', '10.1002/cpz1.1000', '10.1002/cpz1.595', '10.1002/cpz1.866', '10.1002/cpz1.573',
                       '10.1002/cpz1.1065', '10.1002/cpz1.995', '10.1002/cpz1.1099', '10.1002/cpz1.873', '10.1002/cpz1.640', '10.1002/cpz1.32']



    if cleanmission.status == 0:

        cleanmission.status = 1
        session.add(cleanmission)
        session.commit()
        meta_data_list = OriginalDataCurrentProtocol.query.filter_by().all()
        clean_list = CurrentData.query.filter_by().all()

        doi_list = [e.doi for e in clean_list]

        for meta_data in meta_data_list:
            try:
                if meta_data.doi not in filter_doi_list:
                    continue
                if meta_data.doi in doi_list:
                    continue
                # 404
                print(f'start to clean data doi is' + meta_data.doi)

                # if meta_data.doi in ['10.1002/cpz1.950','10.1002/cpz1.972','10.1002/cpz1.1094','10.1002/cpz1.1109','10.1002/cpz1.1092']:
                #     continue

                true_data = get_tre_data(meta_data)

                data = CurrentData(**true_data)
                data.id=meta_data.id
                session.add(data)
                session.commit()
                time.sleep(0.1)

            except Exception as e:
                raise e
                continue




    return 'ok'



@current_deal.route('/migrate/data_current_protocol')
def migrate_data_current_protocol():
    session = db.session
    cleanmission = CleanMission.query.filter_by(id=13).first()
    filter_doi_list = ['10.1002/cpz1.113','10.1002/cpz1.1000','10.1002/cpz1.595','10.1002/cpz1.696','10.1002/cpz1.1036',
                '10.1002/cpz1.714', '10.1002/cpz1.606', '10.1002/cpz1.565', '10.1002/cpz1.245', '10.1002/cpz1.1067',
                '10.1002/cpz1.866', '10.1002/cpz1.573', '10.1002/cpz1.563', '10.1002/cpz1.357', '10.1002/cpz1.158',
                '10.1002/cpz1.1099', '10.1002/cpz1.1065', '10.1002/cpz1.995', '10.1002/cptx.96', '10.1002/cptx.87',
                '10.1002/cpz1.672', '10.1002/cpz1.1094', '10.1002/cpz1.873', '10.1002/cpz1.640', '10.1002/cpz1.32']

    if cleanmission.status == 0:

        cleanmission.status = 1
        session.add(cleanmission)
        session.commit()

        clean_list = CurrentData.query.filter_by().all()

        doi_list = [e.doi for e in clean_list]

        conn=connect()

        migrate_data(conn,'skip',doi_list,None)


    return 'ok'
