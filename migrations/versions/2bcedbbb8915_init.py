"""init

Revision ID: 2bcedbbb8915
Revises: 
Create Date: 2024-09-21 11:31:32.932579

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '2bcedbbb8915'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    op.create_table('clean_data_current_protocol',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.ARRAY(sa.JSON()), nullable=True),
    sa.Column('relates', sa.ARRAY(sa.JSON()), nullable=True),
    sa.Column('author_list', sa.ARRAY(sa.JSON()), nullable=True),
    sa.Column('abstract', sa.Text(), nullable=True),
    sa.Column('content1', sa.Text(), nullable=True),
    sa.Column('content2', sa.Text(), nullable=True),
    sa.Column('content3', sa.Text(), nullable=True),
    sa.Column('doi', sa.String(length=255), nullable=True),
    sa.Column('keywords', sa.ARRAY(sa.Text()), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('volume', sa.String(length=255), nullable=True),
    sa.Column('issue', sa.String(length=255), nullable=True),
    sa.Column('publish_date', sa.String(length=255), nullable=True),
    sa.Column('img_length', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('clean_data_current_protocol', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_clean_data_current_protocol_doi'), ['doi'], unique=True)
        batch_op.create_index(batch_op.f('ix_clean_data_current_protocol_id'), ['id'], unique=False)

    op.create_table('clean_data_protocol_io',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reference', sa.JSON(), nullable=True),
    sa.Column('relates', sa.JSON(), nullable=True),
    sa.Column('author_list', sa.JSON(), nullable=True),
    sa.Column('abstract_text', sa.Text(), nullable=True),
    sa.Column('content', sa.JSON(), nullable=True),
    sa.Column('doi', sa.String(length=255), nullable=True),
    sa.Column('keywords', sa.JSON(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('publish_date', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('clean_data_protocol_io', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_clean_data_protocol_io_doi'), ['doi'], unique=True)
        batch_op.create_index(batch_op.f('ix_clean_data_protocol_io_id'), ['id'], unique=False)

    op.create_table('clean_data_record_mission',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('clean_data_record_mission', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_clean_data_record_mission_id'), ['id'], unique=False)

    # op.create_table('datasets_default_setting',
    # sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    # sa.Column('embedding_model_name', sa.String(length=100), nullable=True),
    # sa.Column('embedding_provider_name', sa.String(length=100), nullable=True),
    # sa.Column('reranking_model_name', sa.String(length=100), nullable=True),
    # sa.Column('reranking_provider_name', sa.String(length=100), nullable=True),
    # sa.Column('embedding_available', sa.Boolean(), nullable=True),
    # sa.Column('reranking_enable', sa.Boolean(), nullable=True),
    # sa.Column('score_threshold_enable', sa.Boolean(), nullable=True),
    # sa.Column('index_model', sa.Integer(), nullable=True),
    # sa.Column('search_method', sa.Integer(), nullable=True),
    # sa.Column('score_threshold', sa.Integer(), nullable=True),
    # sa.Column('topk', sa.Integer(), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='datasets_default_setting_pkey')
    # )
    op.create_table('datasets_task',
    sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('type', sa.String(length=255), nullable=True),
    sa.Column('journal_name', sa.String(length=255), nullable=True),
    sa.Column('parent_task_id', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=255), nullable=True),
    sa.Column('task_setup', sa.JSON(), nullable=True),
    sa.Column('result_detail', sa.JSON(), nullable=True),
    sa.Column('success_count', sa.Integer(), nullable=True),
    sa.Column('failed_count', sa.Integer(), nullable=True),
    sa.Column('total_count', sa.Integer(), nullable=True),
    sa.Column('create_time', sa.Date(), nullable=True),
    sa.Column('end_time', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # op.create_table('journal',
    # sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    # sa.Column('venue', sa.String(length=255), nullable=False),
    # sa.Column('eissn', sa.String(length=9), nullable=True),
    # sa.Column('issn', sa.String(length=9), nullable=True),
    # sa.Column('logo', sa.String(length=255), nullable=True),
    # sa.Column('type', sa.String(length=255), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='journal_pkey')
    # )
    # with op.batch_alter_table('journal', schema=None) as batch_op:
    #     batch_op.create_index('journal_idx', ['venue'], unique=False)

    # op.create_table('journals',
    # sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    # sa.Column('external_id', sa.String(length=255), nullable=False),
    # sa.Column('name', sa.String(length=255), nullable=False),
    # sa.Column('classification', sa.String(length=255), nullable=True),
    # sa.Column('eissn', sa.String(length=9), nullable=True),
    # sa.Column('issn', sa.String(length=9), nullable=True),
    # sa.Column('region', sa.String(length=255), nullable=True),
    # sa.Column('year_published', sa.Integer(), nullable=True),
    # sa.Column('languages', sa.String(length=255), nullable=True),
    # sa.Column('publisher', sa.String(length=255), nullable=True),
    # sa.Column('open_access_flag', sa.Boolean(), nullable=True),
    # sa.Column('quartile', sa.String(length=255), nullable=True),
    # sa.Column('frequency', sa.Integer(), nullable=True),
    # sa.Column('category', sa.String(length=255), nullable=True),
    # sa.Column('category_name', sa.String(length=255), nullable=True),
    # sa.Column('search_start', sa.String(length=255), nullable=True),
    # sa.Column('search_number', sa.Integer(), nullable=True),
    # sa.Column('source', sa.String(length=255), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='journals_pkey')
    # )
    # with op.batch_alter_table('journals', schema=None) as batch_op:
    #     batch_op.create_index('journals_idx', ['external_id', 'name', 'year_published'], unique=False)


    # op.create_table('literature_crossref_info',
    # sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    # sa.Column('authors_info', sa.JSON(), nullable=False),
    # sa.Column('ref_info', sa.JSON(), nullable=False),
    # sa.Column('literature_id', sa.String(length=255), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='literature_crossref_info_pkey')
    # )

    # op.create_table('literatures',
    # sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    # sa.Column('abstract', sa.Text(), nullable=True),
    # sa.Column('authors_info', sa.JSON(), nullable=False),
    # sa.Column('journal_id', sa.String(length=255), nullable=True),
    # sa.Column('doi', sa.String(length=255), nullable=True),
    # sa.Column('issn', sa.String(length=9), nullable=True),
    # sa.Column('issue', sa.String(length=255), nullable=True),
    # sa.Column('keywords', sa.Text(), nullable=True),
    # sa.Column('title', sa.Text(), nullable=False),
    # sa.Column('volume', sa.String(length=255), nullable=True),
    # sa.Column('year', sa.Integer(), nullable=False),
    # sa.Column('file_id', sa.String(length=255), nullable=True),
    # sa.Column('source', sa.String(length=255), nullable=True),
    # sa.Column('external_id', sa.String(length=255), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='literatures_pkey')
    # )
    # with op.batch_alter_table('literatures', schema=None) as batch_op:
    #     batch_op.create_index('literatures_idx', ['external_id', 'title', 'year'], unique=False)

    # op.create_table('meta_article_current_protocol_undetected_chromedriver',
    # sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    # sa.Column('doi', sa.String(length=255), nullable=False),
    # sa.Column('title', sa.String(length=255), nullable=False),
    # sa.Column('volume', sa.String(length=255), nullable=True),
    # sa.Column('issue', sa.String(length=255), nullable=True),
    # sa.Column('key_words', sa.ARRAY(sa.Text()), nullable=True),
    # sa.Column('content', sa.Text(), nullable=True),
    # sa.Column('content1', sa.Text(), nullable=True),
    # sa.Column('content2', sa.Text(), nullable=True),
    # sa.Column('uri', sa.String(length=255), nullable=True),
    # sa.Column('category_name', sa.String(length=255), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='meta_article_current_protocol_undetected_chromedriver_pkey')
    # )
    # with op.batch_alter_table('meta_article_current_protocol_undetected_chromedriver', schema=None) as batch_op:
    #     batch_op.create_index('meta_article_current_protocol_undetected_chromedriver_idx', ['doi'], unique=False)

    # op.create_table('meta_image',
    # sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    # sa.Column('image_name', sa.String(length=255), nullable=True),
    # sa.Column('image_size', sa.BIGINT(), nullable=True),
    # sa.Column('image_data', sa.LargeBinary(), nullable=True),
    # sa.Column('image_path', sa.Text(), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='meta_image_pkey')
    # )

    op.create_table('original_data_current_protocol',
    sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('doi', sa.String(length=255), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('volume', sa.String(length=255), nullable=True),
    sa.Column('issue', sa.String(length=255), nullable=True),
    sa.Column('keywords', sa.ARRAY(sa.Text()), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('content1', sa.Text(), nullable=True),
    sa.Column('content2', sa.Text(), nullable=True),
    sa.Column('uri', sa.String(length=255), nullable=True),
    sa.Column('category_name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id', name='meta_article_pkey')
    )
    with op.batch_alter_table('original_data_current_protocol', schema=None) as batch_op:
        batch_op.create_index('meta_article_idx', ['doi'], unique=False)

    # op.create_table('original_data_protocol_io_backup',
    # sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    # sa.Column('access', sa.JSON(), nullable=True),
    # sa.Column('authors', sa.JSON(), nullable=True),
    # sa.Column('before_start', sa.Text(), nullable=True),
    # sa.Column('created_on', sa.Integer(), nullable=True),
    # sa.Column('creator', sa.JSON(), nullable=True),
    # sa.Column('cross_cloud_origin', sa.Text(), nullable=True),
    # sa.Column('description', sa.Text(), nullable=True),
    # sa.Column('disclaimer', sa.Text(), nullable=True),
    # sa.Column('documents', sa.JSON(), nullable=True),
    # sa.Column('doi', sa.String(length=255), nullable=True),
    # sa.Column('ethics_statement', sa.Text(), nullable=True),
    # sa.Column('fork_id', sa.String(length=255), nullable=True),
    # sa.Column('guid', sa.String(length=255), nullable=True),
    # sa.Column('guidelines', sa.Text(), nullable=True),
    # sa.Column('image', sa.JSON(), nullable=True),
    # sa.Column('is_content_confidential', sa.Boolean(), nullable=True),
    # sa.Column('is_content_warning', sa.Boolean(), nullable=True),
    # sa.Column('is_doi_reserved', sa.Boolean(), nullable=True),
    # sa.Column('is_in_pending_publishing', sa.Boolean(), nullable=True),
    # sa.Column('is_in_transfer', sa.Boolean(), nullable=True),
    # sa.Column('is_owner', sa.Boolean(), nullable=True),
    # sa.Column('is_research', sa.Boolean(), nullable=True),
    # sa.Column('is_subprotocol', sa.Boolean(), nullable=True),
    # sa.Column('item_id', sa.Integer(), nullable=True),
    # sa.Column('journal', sa.JSON(), nullable=True),
    # sa.Column('protocol_id', sa.String(length=255), nullable=True),
    # sa.Column('keywords', sa.Text(), nullable=True),
    # sa.Column('link', sa.Text(), nullable=True),
    # sa.Column('manuscript_citation', sa.Text(), nullable=True),
    # sa.Column('materials', sa.JSON(), nullable=True),
    # sa.Column('materials_text', sa.Text(), nullable=True),
    # sa.Column('protocol_references', sa.Text(), nullable=True),
    # sa.Column('public', sa.Boolean(), nullable=True),
    # sa.Column('published_on', sa.Integer(), nullable=True),
    # sa.Column('reserved_doi', sa.String(length=255), nullable=True),
    # sa.Column('space_id', sa.Integer(), nullable=True),
    # sa.Column('stats', sa.JSON(), nullable=True),
    # sa.Column('status', sa.JSON(), nullable=True),
    # sa.Column('steps', sa.JSON(), nullable=True),
    # sa.Column('title', sa.Text(), nullable=True),
    # sa.Column('title_html', sa.Text(), nullable=True),
    # sa.Column('type_id', sa.Integer(), nullable=True),
    # sa.Column('units', sa.JSON(), nullable=True),
    # sa.Column('uri', sa.Text(), nullable=True),
    # sa.Column('url', sa.Text(), nullable=True),
    # sa.Column('version_class', sa.Integer(), nullable=True),
    # sa.Column('version_data', sa.Text(), nullable=True),
    # sa.Column('version_id', sa.Integer(), nullable=True),
    # sa.Column('version_uri', sa.Text(), nullable=True),
    # sa.Column('versions', sa.JSON(), nullable=True),
    # sa.Column('warning', sa.Text(), nullable=True),
    # sa.PrimaryKeyConstraint('id')
    # )
    op.create_table('original_resource_current_protocol',
    sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('original_path', sa.Text(), nullable=True),
    sa.Column('oss_path', sa.Text(), nullable=True),
    sa.Column('oss_bucket', sa.String(length=256), nullable=True),
    sa.Column('doi', sa.String(length=255), nullable=True),
    sa.Column('resource_type', sa.String(length=255), nullable=True),
    sa.Column('content', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id', name='original_resource_current_protocol_pkey')
    )

    op.create_table('original_resource_protocol_io',
    sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('original_path', sa.Text(), nullable=True),
    sa.Column('oss_path', sa.Text(), nullable=True),
    sa.Column('oss_bucket', sa.String(length=256), nullable=True),
    sa.Column('doi', sa.String(length=255), nullable=True),
    sa.Column('resource_type', sa.String(length=255), nullable=True),
    sa.Column('content', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id', name='original_resource_protocol_io_pkey')
    )

    # op.create_table('relevant_literatures',
    # sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    # sa.Column('literature_id', sa.String(length=255), nullable=True),
    # sa.Column('doi', sa.String(length=255), nullable=True),
    # sa.Column('ref_text', sa.JSON(), nullable=True),
    # sa.PrimaryKeyConstraint('id', name='relevant_literatures_pkey')
    # )

    # op.create_table('task_records',
    # sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    # sa.Column('task_type', sa.String(length=255), nullable=True),
    # sa.Column('is_increment', sa.Boolean(), nullable=True),
    # sa.Column('data_source', sa.String(length=255), nullable=True),
    # sa.Column('crawel_data_record', sa.JSON(), nullable=True),
    # sa.Column('task_status', sa.Integer(), nullable=True),
    # sa.Column('success_list', sa.ARRAY(sa.String()), nullable=True),
    # sa.Column('fail_list', sa.ARRAY(sa.String()), nullable=True),
    # sa.Column('skip_list', sa.ARRAY(sa.String()), nullable=True),
    # sa.Column('retry_count', sa.Integer(), nullable=True),
    # sa.Column('create_time', sa.Date(), nullable=True),
    # sa.Column('end_time', sa.Date(), nullable=True),
    # sa.PrimaryKeyConstraint('id')
    # )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('task_records')
    with op.batch_alter_table('relevant_literatures', schema=None) as batch_op:
        batch_op.drop_index('relevant_literatures_idx')

    op.drop_table('relevant_literatures')
    with op.batch_alter_table('reference_literatures', schema=None) as batch_op:
        batch_op.drop_index('reference_literatures_idx')

    op.drop_table('reference_literatures')
    with op.batch_alter_table('original_resource_protocol_io', schema=None) as batch_op:
        batch_op.drop_index('original_resource_protocol_io_idx')

    op.drop_table('original_resource_protocol_io')
    with op.batch_alter_table('original_resource_current_protocol', schema=None) as batch_op:
        batch_op.drop_index('original_resource_current_protocol_idx')

    op.drop_table('original_resource_current_protocol')
    op.drop_table('original_data_protocol_io_backup')
    with op.batch_alter_table('original_data_current_protocol', schema=None) as batch_op:
        batch_op.drop_index('meta_article_idx')

    op.drop_table('original_data_current_protocol')
    with op.batch_alter_table('meta_image', schema=None) as batch_op:
        batch_op.drop_index('meta_image_idx')

    op.drop_table('meta_image')
    with op.batch_alter_table('meta_article_current_protocol_undetected_chromedriver', schema=None) as batch_op:
        batch_op.drop_index('meta_article_current_protocol_undetected_chromedriver_idx')

    op.drop_table('meta_article_current_protocol_undetected_chromedriver')
    with op.batch_alter_table('literatures', schema=None) as batch_op:
        batch_op.drop_index('literatures_idx')

    op.drop_table('literatures')
    with op.batch_alter_table('literature_keywords', schema=None) as batch_op:
        batch_op.drop_index('literature_keywords_idx')

    op.drop_table('literature_crossref_info')
    with op.batch_alter_table('literature_category', schema=None) as batch_op:
        batch_op.drop_index('literature_category_idx')

    op.drop_table('journals')
    with op.batch_alter_table('journal', schema=None) as batch_op:
        batch_op.drop_index('journal_idx')

    op.drop_table('journal')
    op.drop_table('datasets_task')
    op.drop_table('datasets_default_setting')
    with op.batch_alter_table('clean_data_record_mission', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_clean_data_record_mission_id'))

    op.drop_table('clean_data_record_mission')
    with op.batch_alter_table('clean_data_protocol_io', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_clean_data_protocol_io_id'))
        batch_op.drop_index(batch_op.f('ix_clean_data_protocol_io_doi'))

    op.drop_table('clean_data_protocol_io')
    with op.batch_alter_table('clean_data_current_protocol', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_clean_data_current_protocol_id'))
        batch_op.drop_index(batch_op.f('ix_clean_data_current_protocol_doi'))

    op.drop_table('clean_data_current_protocol')
    with op.batch_alter_table('author', schema=None) as batch_op:
        batch_op.drop_index('author_idx')

    # ### end Alembic commands ###
