from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Meeting Assistant API'
    app_env: str = 'development'
    database_url: Optional[str] = Field(default=None, alias='DATABASE_URL')

    mysql_host: str = Field(default='127.0.0.1', alias='MYSQL_HOST')
    mysql_port: int = Field(default=3306, alias='MYSQL_PORT')
    mysql_db: str = Field(default='meeting_assistant', alias='MYSQL_DB')
    mysql_user: str = Field(default='meeting', alias='MYSQL_USER')
    mysql_password: str = Field(default='meeting', alias='MYSQL_PASSWORD')

    upload_dir: str = Field(default='backend/data/uploads', alias='UPLOAD_DIR')
    chroma_persist_dir: str = Field(default='backend/data/chroma', alias='CHROMA_PERSIST_DIR')
    chroma_collection: str = Field(default='meeting_assistant_chunks', alias='CHROMA_COLLECTION')

    llm_base_url: Optional[str] = Field(default=None, alias='LLM_BASE_URL')
    llm_api_key: Optional[str] = Field(default=None, alias='LLM_API_KEY')
    chat_model: Optional[str] = Field(default=None, alias='CHAT_MODEL')
    embedding_model: Optional[str] = Field(default=None, alias='EMBEDDING_MODEL')
    rerank_base_url: Optional[str] = Field(default=None, alias='RERANK_BASE_URL')
    rerank_api_key: Optional[str] = Field(default=None, alias='RERANK_API_KEY')
    rerank_model: Optional[str] = Field(default=None, alias='RERANK_MODEL')

    feishu_app_id: Optional[str] = Field(default=None, alias='FEISHU_APP_ID')
    feishu_app_secret: Optional[str] = Field(default=None, alias='FEISHU_APP_SECRET')
    feishu_enabled: bool = Field(default=False, alias='FEISHU_ENABLED')

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f'mysql+pymysql://{self.mysql_user}:{self.mysql_password}'
            f'@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4'
        )

    def ensure_directories(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
