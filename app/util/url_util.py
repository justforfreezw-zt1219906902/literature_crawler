import logging
from urllib.parse import urlparse


logger=logging.getLogger(__name__)
def is_relative_path(path):
    """
    判断给定的路径是否为相对路径。

    参数:
    path (str): 需要判断的路径。

    返回:
    bool: 如果路径是相对路径则返回 True，否则返回 False。
    """
    parsed_url = urlparse(path)
    return not (parsed_url.scheme and parsed_url.netloc)


def is_html_link(url):
    """
    判断 URL 是否指向 HTML 页面。
    """
    if not is_download(url):
        logger.error(
            "ERROR, something went wrong" + f' can not download {url} ')
        return True
    return False

def is_download(url):
    if '.google.' in url:
        return False
    if 'doi.org' in url:
        return False
    if '.gov' in url:
        return False
    if 'github' in url:
        return False
    if 'redirect_uri=' in url and 'https://idp.nature.com/auth/personal/springernature' in url:
        return False
    if 'redirect' in url and 'https://currentprotocols.onlinelibrary.wiley.com/action/getFTRLinkout' in url:
        return False
    if '.ad' in url or '/ad' in url:
        return False
    # if 'https://currentprotocols.onlinelibrary.wiley.com/action/downloadSupplement' in url:
    #     return False
    # if 'https://www.semanticscholar.org/paper/Bioschemas' in url:
    #     return False
    if 'https://pdfs.semanticscholar.org' in url:
        return False
    if 'https://www.academia.edu/download' in url:
        return False
    if '@' in url:
        return False
    if 'https://toolkit.tuebingen.mpg.de' in url:
        return False
    if 'http://www.peterbeerli.com/programs/migrate/distribution' in url:
        return False
    # if 'https://www.hycultbiotech.com/media' in url:
    #     return False
    if 'https://www.neb.com/-/media/catalog/application-notes' in url:
        return False
    if 'https://sfvideo.blob.core.windows.net/sitefinity/docs/default-source/application-note' in url:
        return False
    # if 'https://peterbeerli.com/programs/migrate' in url:
    #     return False
    # if 'https://ac.els-cdn.com/' in url:
    #     return False
    if 'https://www.oecd.org/sti/emerging-tech' in url:
        return False
    if 'http://microscopy.arizona.edu/sites/default/files/sites/default/files/upload' in url:
        return False
    if 'https://www.biosigma.com/Catalogue' in url:
        return False
    if 'https://webcdn.leica-microsystems.com/fileadmin/academy' in url:
        return False

    if 'https://www.mpimp-golm.mpg.de/' in url:
        return False
    if 'http://gmd.mpimp-golm.mpg.de/' in url:
        return False

    if 'https://www.liberliber.it/mediateca/libri/g/galilei/sidereus_nuncius' in url:
        return False
    if 'http://calmview.bham.ac.uk/' in url:
        return False
    if '//www.agilent.com/en/products/automation-solutions/protein-sample-preparation/' in url:
        return False
    if 'http://www.beckmancoulter.com/literature' in url:
        return False
    if 'http://www.brendan.com/pdf_files' in url:
        return False
    if 'http://www.stat.ncsu.edu/information/library' in url:
        return False
    if 'https://ncardia.com/files/documents/manuals' in url:
        return False
    if 'https://tools.lifetechnologies.com/content/sfs/manuals' in url:

        return False
    if 'https://www.who.int/biologicals' in url:
        return False

    if 'https://nrims.harvard.edu/files/nrims/files/' in url:
        return False


    return True