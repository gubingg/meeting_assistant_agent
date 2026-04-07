import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / '.pytest_runtime'
TMP_DIR.mkdir(parents=True, exist_ok=True)
os.environ['DATABASE_URL'] = f"sqlite:///{TMP_DIR / 'test.db'}"
os.environ['UPLOAD_DIR'] = str(TMP_DIR / 'uploads')
os.environ['CHROMA_PERSIST_DIR'] = str(TMP_DIR / 'chroma')

sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.core.db import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope='session', autouse=True)
def cleanup_tempdir():
    yield
    shutil.rmtree(TMP_DIR, ignore_errors=True)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
