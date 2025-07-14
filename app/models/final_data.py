# from extensions.ext_database import db
# from models import StringUUID
#
#
# class ImageMeta(db.Model):
#     __tablename__ = 'meta_image'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='meta_image_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#     image_name = db.Column(db.String(255))
#     image_size = db.Column(db.BIGINT)
#     image_data = db.Column(db.LargeBinary)
#     image_path = db.Column(db.Text)
#
#     def __init__(self, image_name=None, image_size=None, image_data=None, image_path=None, id=None):
#         self.image_name = image_name
#         self.image_size = image_size
#         self.image_data = image_data
#         self.image_path = image_path
#
#         self.id = db.text('uuid_generate_v4()')  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<Meta_Image(id='{self.id}', name='{self.image_name}')>"
#
#
# class Author(db.Model):
#     __tablename__ = 'author'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='author_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#     type = db.Column(db.String(255))
#     orcid = db.Column(db.String(255))
#     full_name = db.Column(db.String(255))
#     last_name = db.Column(db.String(255))
#     first_name = db.Column(db.String(255))
#     middle_name = db.Column(db.String(255))
#     email = db.Column(db.String(255))
#     institution = db.Column(db.String(255))
#     avatar = db.Column(db.String(255))
#
#     description = db.Column(db.Text)
#
#     def __init__(self, full_name, type=None, orcid=None, last_name=None, first_name=None, middle_name=None,
#                  email=None, institution=None, avatar=None, description=None):
#         self.type = type
#         self.orcid = orcid
#         self.full_name = full_name
#         self.last_name = last_name
#         self.first_name = first_name
#         self.middle_name = middle_name
#         self.email = email
#         self.institution = institution
#         self.avatar = avatar
#         self.description = description
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<Author(id='{self.id}', name='{self.full_name}')>"
#
#
# class LiteratureAuthors(db.Model):
#     __tablename__ = 'literature_authors'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='literature_authors_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#     type = db.Column(db.String(255))
#     literature_id = db.Column(db.String(255))
#     author_id = db.Column(db.String(255))
#
#     def __init__(self, literature_id=None, author_id=None, id=None, type=None):
#         self.type = type
#         self.literature_id = literature_id
#         self.author_id = author_id
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<LiteratureAuthors(id='{self.id}', literature_id='{self.literature_id}'), author_id='{self.author_id}')>"
#
#
# class Journal(db.Model):
#     __tablename__ = 'journal'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='journal_pkey'),
#         db.Index('journal_idx', 'venue')
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#
#     venue = db.Column(db.String(255), nullable=False)
#
#     eissn = db.Column(db.String(9))
#     issn = db.Column(db.String(9))
#     logo = db.Column(db.String(255))
#     type = db.Column(db.String(255))
#
#     def __init__(self, venue, id=None, eissn=None, issn=None, logo=None, type=None):
#         self.type = type
#         self.venue = venue
#         self.eissn = eissn
#         self.issn = issn
#         self.logo = logo
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<Journal(id='{self.id}', name='{self.venue}')>"
#
#
# class LiteratureCategories(db.Model):
#     __tablename__ = 'literature_categories'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='literature_categories_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#
#     literature_id = db.Column(db.String(255))
#     category_id = db.Column(db.String(255))
#
#     def __init__(self, literature_id=None, category_id=None, id=None):
#         self.literature_id = literature_id
#         self.category_id = category_id
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<LiteratureCategories(id='{self.id}', literature_id='{self.literature_id}'), category_id='{self.category_id}')>"
#
#
# class Literature(db.Model):
#     __tablename__ = 'literature'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='literature_pkey'),
#     )
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#     abstract = db.Column(db.Text)
#     content = db.Column(db.Text)
#     journal_id = db.Column(db.String(255))
#     doi = db.Column(db.String(255))
#     issue = db.Column(db.String(255))
#     title = db.Column(db.String(255), nullable=False)
#     volume = db.Column(db.String(255))
#     original_article_img = db.Column(db.String(255))
#     original_article_link = db.Column(db.String(255))
#     original_article_doi = db.Column(db.String(255))
#     type = db.Column(db.String(255))
#     collection_id = db.Column(db.String(255))
#     published_date = db.Column(db.Date)
#
#     file_info = db.Column(db.JSON)
#
#     def __init__(self, title, abstract=None, journal_id=None, doi=None, issue=None, volume=None,
#                  original_article_img=None, original_article_link=None, original_article_doi=None
#                  , type=None, collection_id=None, published_date=None, file_info=None):
#         self.id = id
#         self.title = title
#         self.abstract = abstract
#         self.journal_id = journal_id
#         self.doi = doi
#         self.issue = issue
#         self.volume = volume
#         self.original_article_img = original_article_img
#         self.original_article_link = original_article_link
#         self.original_article_doi = original_article_doi
#         self.type = type
#         self.collection_id = collection_id
#         self.published_date = published_date
#         self.file_info = file_info
#
#     def __repr__(self):
#         return f"<Literature(id='{self.id}', title='{self.title}')>"
#
#
# class RelevantLiteratures(db.Model):
#     __tablename__ = 'relevant_literatures'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='relevant_literatures_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#
#     literature_id = db.Column(db.String(255))
#     doi = db.Column(db.String(255))
#     ref_text = db.Column(db.JSON)
#
#     def __init__(self, literature_id=None, doi=None, id=None, ref_text=None):
#         self.literature_id = literature_id
#         self.doi = doi
#         self.ref_text = ref_text
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<RelevantLiteratures(id='{self.id}', literature_id='{self.literature_id}'), doi='{self.doi}')>"
#
#
# class LiteratureCategory(db.Model):
#     __tablename__ = 'literature_category'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='literature_category_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#
#     name = db.Column(db.String(255))
#     name_cn = db.Column(db.String(255))
#     parent_id = db.Column(db.String(255))
#
#     def __init__(self, name=None, name_cn=None, parent_id=None):
#         self.name = name
#         self.name_cn = name_cn
#         self.parent_id = parent_id
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<LiteratureCategory(id='{self.id}', name='{self.name}')>"
#
#
# class LiteratureKeywords(db.Model):
#     __tablename__ = 'literature_keywords'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='literature_keywords_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#
#     literature_id = db.Column(db.String(255))
#     keywords_id = db.Column(db.String(255))
#
#     def __init__(self, literature_id=None, keywords_id=None):
#         self.literature_id = literature_id
#         self.keywords_id = keywords_id
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<LiteratureKeywords(id='{self.id}', literature_id='{self.literature_id}', keywords_id='{self.keywords_id}')>"
#
#
# class ReferenceLiteratures(db.Model):
#     __tablename__ = 'reference_literatures'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='reference_literatures_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#
#     literature_id = db.Column(db.String(255))
#     article_links = db.Column(db.ARRAY(db.String))
#     doi = db.Column(db.String(255))
#     ref_text = db.Column(db.JSON)
#
#     def __init__(self, literature_id=None, doi=None, id=None, ref_text=None, article_links=None):
#         self.literature_id = literature_id
#         self.doi = doi
#         self.ref_text = ref_text
#         self.article_links = article_links
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<ReferenceLiteratures(id='{self.id}', literature_id='{self.literature_id}'), doi='{self.doi}')>"
#
#
# class keywords(db.Model):
#     __tablename__ = 'keywords'
#     __table_args__ = (
#         db.PrimaryKeyConstraint('id', name='keywords_pkey'),
#     )
#
#     id = db.Column(StringUUID, primary_key=True, server_default=db.text('uuid_generate_v4()'))
#
#     name = db.Column(db.String(255))
#     name_cn = db.Column(db.String(255))
#     type = db.Column(db.String(255))
#
#     def __init__(self, name=None, name_cn=None, type=None):
#         self.name = name
#         self.name_cn = name_cn
#         self.type = type
#
#         self.id = id  # 如果没有传入id，则自动生成一个UUID
#
#     def __repr__(self):
#         return f"<keywords(id='{self.id}', name='{self.name}')>"

