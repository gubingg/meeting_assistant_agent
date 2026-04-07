import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.docs import router as docs_router
from app.api.export import router as export_router
from app.api.meetings import router as meetings_router
from app.api.projects import router as projects_router
from app.api.qa import router as qa_router
from app.api.tasks import router as tasks_router
from app.core.config import get_settings
from app.core.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s - %(message)s',
)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def on_startup() -> None:
    logger.info('Backend startup: initializing database and compatibility migrations')
    init_db()
    logger.info('Backend startup completed')


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


app.include_router(projects_router)
app.include_router(meetings_router)
app.include_router(tasks_router)
app.include_router(docs_router)
app.include_router(qa_router)
app.include_router(export_router)
