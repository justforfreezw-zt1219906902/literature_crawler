import uuid
from datetime import datetime

from extensions.ext_database import db
from app.models import StringUUID


class OriginalDataCurrentProtocol(db.Model):
    __tablename__ = 'original_data_current_protocol'

    id = db.Column(db.String(255), primary_key=True, default=uuid.uuid4)
    doi = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    volume = db.Column(db.String(255))
    issue = db.Column(db.String(255))
    keywords = db.Column(db.JSON)
    content = db.Column(db.Text)

    uri = db.Column(db.String(255))
    category_name = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, doi, title, content=None, uri=None, id=None
                 , volume=None, issue=None, keywords=None, category_name=None):
        self.doi = doi
        self.title = title
        self.content = content
        self.uri = uri
        self.volume = volume
        self.issue = issue
        self.keywords = keywords

        self.id = id  # 如果没有传入id，则自动生成一个UUID
        self.category_name = category_name

    def __repr__(self):
        return f"<Meta_data(doi='{self.doi}', name='{self.title}')>"


class CurrentProtocolResources(db.Model):
    __tablename__ = 'original_resource_current_protocol'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='original_resource_current_protocol_pkey'),
    )

    id = db.Column(db.String(255), primary_key=True, default=uuid.uuid4)

    original_path = db.Column(db.Text)
    oss_path = db.Column(db.Text)
    oss_bucket = db.Column(db.String(256))
    description = db.Column(db.Text)
    doi = db.Column(db.String(255))
    md5 = db.Column(db.String(255))

    resource_type = db.Column(db.String(255))
    content = db.Column(db.LargeBinary)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, oss_path=None, id=None, doi=None, original_path=None, content=None, resource_type=None,
                 oss_bucket=None, description=None, md5=None):
        self.original_path = original_path
        self.oss_path = oss_path
        self.doi = doi
        self.content = content
        self.resource_type = resource_type
        self.id = id  # 如果没有传入id，则自动生成一个UUID
        self.oss_bucket = oss_bucket
        self.description = description
        self.md5 = md5

    def __repr__(self):
        return f"<original_resource_current_protocol(id='{self.id}', original_path='{self.original_path}')>"


class ProtocolIoResources(db.Model):
    __tablename__ = 'original_resource_protocol_io'
    __table_args__ = (
        db.PrimaryKeyConstraint('id', name='original_resource_protocol_io_pkey'),
    )

    id = db.Column(db.String(255), primary_key=True, default=uuid.uuid4)

    original_path = db.Column(db.Text)
    oss_path = db.Column(db.Text)
    oss_bucket = db.Column(db.String(256))
    doi = db.Column(db.String(255))

    resource_type = db.Column(db.String(255))
    content = db.Column(db.LargeBinary)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, oss_path=None, id=None, doi=None, original_path=None, content=None, resource_type=None,
                 oss_bucket=None):
        self.original_path = original_path
        self.oss_path = oss_path
        self.doi = doi
        self.content = content
        self.resource_type = resource_type
        self.id = id  # 如果没有传入id，则自动生成一个UUID
        self.oss_bucket = oss_bucket

    def __repr__(self):
        return f"<original_resource_protocol_io(id='{self.id}', original_path='{self.original_path}')>"


class OriginalDataProtocolIO(db.Model):
    __tablename__ = 'original_data_protocol_io'

    id = db.Column(db.String(255), primary_key=True)
    access = db.Column(db.JSON)
    authors = db.Column(db.JSON)
    before_start = db.Column(db.Text)
    created_on = db.Column(db.Integer)
    creator = db.Column(db.JSON)
    cross_cloud_origin = db.Column(db.Text)
    # cross_cloud_origin = db.Column(db.String(255))
    description = db.Column(db.Text)
    disclaimer = db.Column(db.Text)
    documents = db.Column(db.JSON)
    doi = db.Column(db.String(255))
    ethics_statement = db.Column(db.Text)
    # fork_id = db.Column(db.String(255))
    fork_id = db.Column(db.String(255))
    # funders = db.Column(db.JSON)
    guid = db.Column(db.String(255))
    guidelines = db.Column(db.Text)
    image = db.Column(db.JSON)
    is_content_confidential = db.Column(db.Boolean)
    is_content_warning = db.Column(db.Boolean)
    is_doi_reserved = db.Column(db.Boolean)
    is_in_pending_publishing = db.Column(db.Boolean)
    is_in_transfer = db.Column(db.Boolean)
    is_owner = db.Column(db.Boolean)
    is_research = db.Column(db.Boolean)
    is_subprotocol = db.Column(db.Boolean)
    item_id = db.Column(db.Integer)
    journal = db.Column(db.JSON)
    protocol_id = db.Column(db.String(255))
    keywords = db.Column(db.Text)
    # link = db.Column(db.String(255))
    link = db.Column(db.Text)
    manuscript_citation = db.Column(db.Text)
    materials = db.Column(db.JSON)
    materials_text = db.Column(db.Text)
    protocol_references = db.Column(db.Text)
    public = db.Column(db.Boolean)
    published_on = db.Column(db.Integer)
    reserved_doi = db.Column(db.String(255))
    space_id = db.Column(db.Integer)
    stats = db.Column(db.JSON)
    status = db.Column(db.JSON)
    steps = db.Column(db.JSON)
    title = db.Column(db.Text)
    title_html = db.Column(db.Text)
    type_id = db.Column(db.Integer)
    units = db.Column(db.JSON)
    uri = db.Column(db.Text)
    url = db.Column(db.Text)
    funders = db.Column(db.JSON)
    acknowledgements = db.Column(db.Text)
    version_class = db.Column(db.Integer)
    version_data = db.Column(db.Text)
    version_id = db.Column(db.Integer)
    version_uri = db.Column(db.Text)
    versions = db.Column(db.JSON)
    warning = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def __init__(self, doi=None, protocol_id=None, id=None, **kwargs):
    self.protocol_id = protocol_id
    self.doi = doi
    self.id = id
    for key, value in kwargs.items():
        setattr(self, key, value)


# 如果需要，可以添加额外的方法，比如表示对象的字符串方法
def __repr__(self):
    return f"<OriginalDataProtocolIO(id={self.id}, title='{self.title}')>"


class OriginalDataNatureProtocol(db.Model):
    __tablename__ = 'original_data_nature_protocol'

    id = db.Column(db.String(255), primary_key=True, default=uuid.uuid4)
    doi = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    type = db.Column(db.String(1024), nullable=False)
    issue = db.Column(db.String(1024), nullable=False)
    volume = db.Column(db.String(1024), nullable=False)

    content = db.Column(db.Text)
    article_description = db.Column(db.Text)

    uri = db.Column(db.String(1024))
    published_on = db.Column(db.BigInteger)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, doi, title, content=None, type=None, article_description=None, uri=None, id=None
                 , issue=None, published_on=None, volume=None):
        self.doi = doi
        self.title = title
        self.content = content
        self.uri = uri
        self.published_on = published_on
        self.issue = issue
        self.volume = volume

        self.type = type
        self.article_description = article_description
        self.id = id  # 如果没有传入id，则自动生成一个UUID

    def __repr__(self):
        return f"<Original_data_nature_protocol(doi='{self.doi}', name='{self.title}')>"


class NatureProtocolResources(db.Model):
    __tablename__ = 'original_resource_nature_protocol'

    id = db.Column(db.String(255), primary_key=True, default=uuid.uuid4)

    original_path = db.Column(db.String(1024))
    original_name = db.Column(db.String(1024))
    md5 = db.Column(db.String(1024))
    description = db.Column(db.Text)
    oss_path = db.Column(db.String(1024))
    oss_bucket = db.Column(db.String(256))
    doi = db.Column(db.String(255))

    resource_type = db.Column(db.String(255))
    content = db.Column(db.LargeBinary)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, oss_path=None, id=None, doi=None, original_path=None, content=None, resource_type=None,
                 oss_bucket=None, original_name=None, md5=None, description=None):
        self.original_path = original_path
        self.oss_path = oss_path
        self.doi = doi
        self.content = content
        self.resource_type = resource_type
        self.id = id  # 如果没有传入id，则自动生成一个UUID
        self.oss_bucket = oss_bucket
        self.original_name = original_name
        self.md5 = md5
        self.description = description

    def __repr__(self):
        return f"<original_resource_nature_protocol(id='{self.id}', original_path='{self.original_path}')>"
