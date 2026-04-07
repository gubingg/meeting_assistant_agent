from app.rag.retriever import ProjectRetriever


class FakeIndexClient:
    def __init__(self, rows):
        self.rows = rows

    def query(self, **kwargs):
        return list(self.rows)


class FakeLLMClient:
    def __init__(self, rerank_results=None):
        self.rerank_results = rerank_results
        self.calls = []

    def rerank(self, query, documents, top_n=None):
        self.calls.append({'query': query, 'documents': documents, 'top_n': top_n})
        return self.rerank_results


def make_row(chunk_id, *, score, source_type='project_doc_version', doc_type='reference', title='Doc', snippet='Snippet', text='Full text'):
    return {
        'chunk_id': chunk_id,
        'meeting_id': None,
        'source_type': source_type,
        'source_id': 1,
        'doc_id': 1,
        'doc_version_id': 1,
        'title': title,
        'doc_type': doc_type,
        'doc_type_label': None,
        'snippet': snippet,
        'score': score,
        'text': text,
    }


def test_project_retriever_uses_reranker_order_when_available():
    rows = [
        make_row('chunk-1', score=0.88, doc_type='prd', text='Product scope and goals'),
        make_row('chunk-2', score=0.41, doc_type='reference', text='Implementation details'),
    ]
    llm_client = FakeLLMClient(
        rerank_results=[
            {'index': 1, 'score': 0.96},
            {'index': 0, 'score': 0.62},
        ]
    )
    retriever = ProjectRetriever(client=FakeIndexClient(rows), llm_client=llm_client)

    items = retriever.retrieve(
        1,
        'How is this implemented?',
        {'project_doc_version'},
        top_k=2,
        preferred_doc_types=['prd'],
    )

    assert [item.chunk_id for item in items] == ['chunk-2', 'chunk-1']
    assert items[0].rerank_score == 0.96
    assert items[1].rerank_score == 0.62
    assert llm_client.calls[0]['top_n'] == 2


def test_project_retriever_falls_back_to_existing_sort_when_reranker_is_unavailable():
    rows = [
        make_row('chunk-1', score=0.91, doc_type='reference'),
        make_row('chunk-2', score=0.35, doc_type='prd'),
    ]
    llm_client = FakeLLMClient(rerank_results=None)
    retriever = ProjectRetriever(client=FakeIndexClient(rows), llm_client=llm_client)

    items = retriever.retrieve(
        1,
        'What is the project goal?',
        {'project_doc_version'},
        top_k=2,
        preferred_doc_types=['prd'],
    )

    assert [item.chunk_id for item in items] == ['chunk-2', 'chunk-1']
    assert items[0].rerank_score is None
    assert items[1].rerank_score is None
