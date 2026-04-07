from __future__ import annotations

import logging
from types import SimpleNamespace

from app.core.config import get_settings
from app.models import Meeting, Project
from app.services.chunk_service import ChunkPayload
from app.services.llm_service import OpenAICompatibleClient
from app.services.vector_service import VectorStoreService


def test_openai_compatible_client_uses_chat_and_embedding_models(monkeypatch, caplog):
    get_settings.cache_clear()
    monkeypatch.setenv('LLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    monkeypatch.setenv('LLM_API_KEY', 'test-key')
    monkeypatch.setenv('CHAT_MODEL', 'qwen3-max')
    monkeypatch.setenv('EMBEDDING_MODEL', 'text-embedding-v4')

    calls: list[tuple[str, str, int | None]] = []

    class FakeOpenAI:
        def __init__(self, *, base_url, api_key):
            assert base_url == 'https://dashscope.aliyuncs.com/compatible-mode/v1'
            assert api_key == 'test-key'
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._chat_create))
            self.embeddings = SimpleNamespace(create=self._embedding_create)

        def _chat_create(self, *, model, messages, temperature):
            calls.append(('chat', model, None))
            assert temperature == 0.2
            assert messages[-1]['content'] == 'user prompt'
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='chat output'))]
            )

        def _embedding_create(self, *, model, input, dimensions=None):
            calls.append(('embedding', model, dimensions))
            assert input == 'embed me'
            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])])

    monkeypatch.setattr('app.services.llm_service.OpenAI', FakeOpenAI)

    with caplog.at_level(logging.INFO):
        client = OpenAICompatibleClient()
        assert client.chat('system prompt', 'user prompt') == 'chat output'
        assert client.embed_text('embed me', dimensions=128) == [0.1, 0.2, 0.3]

    assert calls == [('chat', 'qwen3-max', None), ('embedding', 'text-embedding-v4', 128)]
    assert 'LLM chat request: model=qwen3-max' in caplog.text
    assert 'LLM embedding success: model=text-embedding-v4 dims=3' in caplog.text

    get_settings.cache_clear()


def test_vector_store_uses_llm_embeddings_instead_of_local_hashing(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv('CHROMA_COLLECTION', 'test_llm_embeddings')

    chunk = ChunkPayload(
        chunk_uuid='chunk-1',
        text='alpha project plan',
        source_type='project_doc',
        turn_start=None,
        turn_end=None,
        start_time_sec=None,
        end_time_sec=None,
        speaker_list=[],
        topic_hint='alpha',
        summary_short='alpha project plan',
        keywords=['alpha', 'project'],
    )

    vector_store = VectorStoreService()
    monkeypatch.setattr(
        vector_store.chunk_service,
        'embed_text',
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError('local hash embeddings should not be used')),
    )
    monkeypatch.setattr(vector_store.llm_client, 'embed_text', lambda text, dimensions=None: [0.25, 0.75] if text else None)

    vector_store.upsert_chunks([chunk], meeting_id=123, source_doc_id=9)
    rows = vector_store.query('alpha project plan', n_results=1, where={'source_type': 'project_doc'})

    assert len(rows) == 1
    assert rows[0]['chunk_id'] == 'chunk-1'

    get_settings.cache_clear()


def test_meeting_model_generates_legacy_meeting_uuid_on_flush(db_session):
    project = Project(slug='meeting-uuid-test', name='Meeting UUID Test', description='debug', owner='tester', status='active')
    db_session.add(project)
    db_session.flush()

    meeting = Meeting(project_id=project.id, title='Test meeting')
    db_session.add(meeting)
    db_session.flush()

    assert meeting.meeting_uuid
