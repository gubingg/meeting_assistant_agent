from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.constants.doc_types import normalize_doc_type
from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.resolved_database_url(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


TABLE_COLUMN_DDLS = {
    'meetings': {
        'meeting_uuid': "meeting_uuid VARCHAR(64) NOT NULL DEFAULT ''",
        'project_id': 'project_id INTEGER NULL',
        'meeting_date': 'meeting_date DATETIME NULL',
        'meeting_time': 'meeting_time DATETIME NULL',
        'participants': 'participants JSON NULL',
        'participants_json': 'participants_json JSON NULL',
        'raw_json': 'raw_json JSON NULL',
        'raw_text': 'raw_text LONGTEXT NULL',
        'summary': 'summary LONGTEXT NULL',
        'decisions_json': 'decisions_json JSON NULL',
        'risks_json': 'risks_json JSON NULL',
        'transcript_file_path': 'transcript_file_path VARCHAR(500) NULL',
        'source_file_name': 'source_file_name VARCHAR(255) NULL',
    },
    'tasks': {
        'project_id': 'project_id INTEGER NULL',
        'latest_update_meeting_id': 'latest_update_meeting_id INTEGER NULL',
    },
    'project_docs': {
        'project_id': 'project_id INTEGER NULL',
        'title': "title VARCHAR(255) NOT NULL DEFAULT ''",
        'content': 'content LONGTEXT NULL',
        'parse_status': "parse_status VARCHAR(20) NOT NULL DEFAULT 'processing'",
        'qa_enabled': 'qa_enabled BOOLEAN NOT NULL DEFAULT 0',
    },
    'chat_logs': {
        'project_id': 'project_id INTEGER NULL',
    },
    'task_link_suggestions': {
        'project_id': 'project_id INTEGER NULL',
    },
}


INDEX_DDLS = {
    'meetings': {
        'project_id': 'CREATE INDEX ix_meetings_project_id ON meetings (project_id)',
    },
    'tasks': {
        'project_id': 'CREATE INDEX ix_tasks_project_id ON tasks (project_id)',
    },
    'project_docs': {
        'project_id': 'CREATE INDEX ix_project_docs_project_id ON project_docs (project_id)',
    },
    'chat_logs': {
        'project_id': 'CREATE INDEX ix_chat_logs_project_id ON chat_logs (project_id)',
    },
    'task_link_suggestions': {
        'project_id': 'CREATE INDEX ix_task_link_suggestions_project_id ON task_link_suggestions (project_id)',
    },
}


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def _ensure_table_columns() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, column_ddls in TABLE_COLUMN_DDLS.items():
            if table_name not in table_names:
                continue

            existing_columns = {column['name'] for column in inspector.get_columns(table_name)}
            for column_name, ddl in column_ddls.items():
                if column_name in existing_columns:
                    continue
                connection.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {ddl}'))

            existing_indexes = {index['name'] for index in inspector.get_indexes(table_name)}
            for column_name, ddl in INDEX_DDLS.get(table_name, {}).items():
                index_name = f'ix_{table_name}_{column_name}'
                if index_name in existing_indexes:
                    continue
                connection.execute(text(ddl))



def _backfill_legacy_meeting_columns() -> None:
    from app.models import Meeting

    inspector = inspect(engine)
    if 'meetings' not in inspector.get_table_names():
        return

    with SessionLocal() as session:
        meetings = session.scalars(select(Meeting)).all()
        updated = False
        for meeting in meetings:
            if not meeting.meeting_uuid:
                meeting.meeting_uuid = uuid4().hex
                updated = True
            if meeting.meeting_time is None and meeting.meeting_date is not None:
                meeting.meeting_time = meeting.meeting_date
                updated = True
            if meeting.meeting_date is None and meeting.meeting_time is not None:
                meeting.meeting_date = meeting.meeting_time
                updated = True
            if not meeting.participants_json and meeting.participants:
                meeting.participants_json = meeting.participants
                updated = True
            if not meeting.participants and meeting.participants_json:
                meeting.participants = meeting.participants_json
                updated = True
            if meeting.summary is None:
                meeting.summary = ''
                updated = True
            if not meeting.source_file_name and meeting.transcript_file_path:
                meeting.source_file_name = meeting.transcript_file_path
                updated = True
            if not meeting.transcript_file_path and meeting.source_file_name:
                meeting.transcript_file_path = meeting.source_file_name
                updated = True
            session.add(meeting)
        if updated:
            session.commit()



def _run_compatibility_migrations() -> None:
    from app.models import ProjectDoc

    _ensure_table_columns()
    _backfill_legacy_meeting_columns()

    with SessionLocal() as session:
        docs = session.scalars(select(ProjectDoc)).all()
        updated = False
        for doc in docs:
            normalized = normalize_doc_type(doc.doc_type)
            if normalized and normalized != doc.doc_type:
                doc.doc_type = normalized
                updated = True
            if not getattr(doc, 'title', None):
                doc.title = doc.doc_name
                updated = True
            if not getattr(doc, 'parse_status', None):
                doc.parse_status = 'completed'
                updated = True
            if getattr(doc, 'qa_enabled', None) is None:
                doc.qa_enabled = True
                updated = True
            if not getattr(doc, 'content', None) and doc.current_version is not None:
                doc.content = doc.current_version.content_raw
                updated = True
            session.add(doc)
        if updated:
            session.commit()



def init_db() -> None:
    from app.models import BaseModelMixin  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_compatibility_migrations()
