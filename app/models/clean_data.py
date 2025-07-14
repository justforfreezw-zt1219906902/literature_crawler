from datetime import datetime

from extensions.ext_database import db


class CurrentData(db.Model):
    __tablename__ = 'clean_data_current_protocol'

    id = db.Column(db.String(255), primary_key=True)

    reference = db.Column(db.JSON, nullable=True)  # 引用列表

    relates = db.Column(db.JSON, nullable=True)  # 相关列表

    author_list = db.Column(db.JSON, nullable=True)  # 相关列表
    abstract_text = db.Column(db.Text, nullable=True)  # 摘要
    content = db.Column(db.JSON, nullable=True)  # 内容部分 1
    file_info = db.Column(db.JSON, nullable=True)  # 内容部分 1
    figures = db.Column(db.JSON, nullable=True)  # 内容部分 1

    doi = db.Column(db.String(255), unique=True, index=True)  # DOI，具有唯一性

    keywords = db.Column(db.JSON, nullable=True)  # 关键词列表
    title = db.Column(db.String(1024), nullable=True)  # 标题
    volume = db.Column(db.String(255), nullable=True)  # 卷号
    issue = db.Column(db.String(255), nullable=True)  # 期号
    publish_date = db.Column(db.String(255), nullable=True)  # 发布日期
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, doi, title=None, abstract_text=None, content=None,
                 keywords=None, reference=None, relates=None, volume=None, issue=None, publish_date=None,author_list=None,file_info=None,figures=None):
        self.doi = doi
        self.title = title
        self.abstract_text = abstract_text
        self.content = content

        self.keywords = keywords
        self.reference = reference
        self.relates = relates
        self.volume = volume
        self.issue = issue
        self.publish_date = publish_date
        self.author_list = author_list
        self.file_info = file_info
        self.figures = figures


    def __repr__(self):
        return f"<CurrentData(id={self.id}, doi='{self.doi}', title='{self.title}')>"



class IOData(db.Model):
    __tablename__ = 'clean_data_protocol_io'

    id = db.Column(db.String(255), primary_key=True)
    reference = db.Column(db.JSON, nullable=True)  # 引用列表
    relates = db.Column(db.JSON, nullable=True)  # 相关列表
    author_list = db.Column(db.JSON, nullable=True)  # 相关列表
    abstract_text = db.Column(db.Text, nullable=True)  # 摘要
    content = db.Column(db.JSON, nullable=True)  # 内容部分 1
    file_info = db.Column(db.JSON, nullable=True)  # 内容部分 1
    # content2 = db.Column(db.Text, nullable=True)  # 内容部分 2
    # content3 = db.Column(db.Text, nullable=True)  # 内容部分 3
    doi = db.Column(db.String(255), unique=True, index=True)  # DOI，具有唯一性
    keywords = db.Column(db.JSON, nullable=True)  # 关键词列表
    figures = db.Column(db.JSON, nullable=True)
    title = db.Column(db.String(1024), nullable=True)  # 标题

    publish_date = db.Column(db.String(255), nullable=True)  # 发布日期
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, doi,id=None, title=None, abstract_text=None, content=None,
                 keywords=None, reference=None, relates=None,  publish_date=None,author_list=None,img_length=None,file_info=None,figures=None):
        self.doi = doi
        self.title = title
        self.abstract_text = abstract_text
        self.content = content

        self.keywords = keywords
        self.reference = reference
        self.relates = relates

        self.publish_date = publish_date
        self.author_list = author_list
        self.img_length = img_length
        self.id=id
        self.file_info =file_info
        self.figures = figures

    def __repr__(self):
        return (f"<IOData(id={self.id}, "
                f"\ndoi='{self.doi}', "
                f"\ntitle='{self.title}',"
                f"\npublish_date='{self.publish_date}',"
                
                f"\nkeywords='{self.keywords}'"
                f",\nreference='{self.reference}'"
                f",\nrelates='{self.relates}'"
                f"\nabstract_text='{self.abstract_text}',"
            
                f""
                f")>")


class CleanDataNatureProtocol(db.Model):
    __tablename__ = 'clean_data_nature_protocol'

    id = db.Column(db.String(255), primary_key=True)
    reference = db.Column(db.JSON, nullable=True)  # 引用列表
    relates = db.Column(db.JSON, nullable=True)  # 引用列表
    author_list = db.Column(db.JSON, nullable=True)  # 相关列表
    abstract_text = db.Column(db.Text, nullable=True)  # 摘要
    content = db.Column(db.JSON, nullable=True)  # 内容部分 1

    doi = db.Column(db.String(255), unique=True, index=True)  # DOI，具有唯一性
    keywords = db.Column(db.JSON, nullable=True)  # 关键词列表
    key_points = db.Column(db.JSON, nullable=True)  # 关键词列表
    title = db.Column(db.String(1024), nullable=True)  # 标题
    volume = db.Column(db.String(255), nullable=True)  # 卷号
    issue = db.Column(db.String(255), nullable=True)  # 期号
    publish_date = db.Column(db.String(255), nullable=True)  # 发布日期

    file_info = db.Column(db.JSON, nullable=True)  # 关键词列表
    figures = db.Column(db.JSON, nullable=True)  # 关键词列表
    paper_type = db.Column(db.String(255), nullable=True)  # 关键词列表
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, doi, id=None,title=None, abstract_text=None, content=None,
                 keywords=None, reference=None, volume=None, issue=None, publish_date=None,author_list=None,file_info=None,relates=None,paper_type=None,key_points=None,figures=None):
        self.doi = doi
        self.title = title
        self.abstract_text = abstract_text
        self.content = content
        self.keywords = keywords
        self.reference = reference
        self.volume = volume
        self.issue = issue
        self.publish_date = publish_date
        self.author_list = author_list
        self.file_info = file_info
        self.id = id
        self.paper_type = paper_type
        self.relates = relates
        self.key_points = key_points
        self.figures = figures

    def __repr__(self):
        return f"<CleanDataNatureProtocol(id={self.id}, doi='{self.doi}', title='{self.title}')>"