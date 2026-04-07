import json

from app.models import ProjectDoc, Task


def create_project(client, name='Apollo 海外发布升级'):
    response = client.post(
        '/api/projects',
        json={
            'name': name,
            'description': '围绕海外版本发布节奏，统一需求澄清、交付排期、风险跟踪和跨团队同步。',
            'owner': 'Luna',
            'start_date': '2026-03-28T14:30:00',
        },
    )
    assert response.status_code == 200
    return response.json()


def upload_doc(client, project_id, file_name, doc_type, content, title=None):
    data = {'doc_type': doc_type}
    if title is not None:
        data['title'] = title
    return client.post(
        f'/api/projects/{project_id}/docs/upload',
        files={'file': (file_name, content.encode('utf-8'), 'text/markdown')},
        data=data,
    )


def test_project_list_create_archive_flow(client):
    project = create_project(client)

    list_response = client.get('/api/projects', params={'status': 'all'})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]['meeting_count'] == 0

    archive_response = client.post(f"/api/projects/{project['id']}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()['status'] == 'archived'

    archived_list = client.get('/api/projects', params={'status': 'archived'})
    assert archived_list.status_code == 200
    assert len(archived_list.json()) == 1

    reopen_response = client.post(f"/api/projects/{project['id']}/reopen")
    assert reopen_response.status_code == 200
    assert reopen_response.json()['status'] == 'active'
    assert reopen_response.json()['archived_at'] is None

    active_list = client.get('/api/projects', params={'status': 'active'})
    assert active_list.status_code == 200
    assert len(active_list.json()) == 1


def test_project_doc_upload_requires_valid_doc_type(client):
    project = create_project(client)

    response = upload_doc(client, project['id'], 'invalid.md', '合同模板', '# 合同')

    assert response.status_code == 400
    assert '资料类型' in response.json()['detail']


def test_project_doc_upload_and_list_include_doc_type_label_and_filter(client):
    project = create_project(client)

    prd_upload = upload_doc(client, project['id'], 'PRD_v0.1.md', 'PRD', '# PRD\n定义目标与范围。')
    assert prd_upload.status_code == 200
    assert prd_upload.json()['doc_type'] == 'prd'
    assert prd_upload.json()['doc_type_label'] == 'PRD'

    tech_upload = upload_doc(client, project['id'], '技术方案草案_v0.1.md', '技术方案', '# 技术方案\n描述实现方式与输入格式。')
    assert tech_upload.status_code == 200
    assert tech_upload.json()['doc_type'] == 'tech_spec'
    assert tech_upload.json()['doc_type_label'] == '技术方案'

    docs_response = client.get(f"/api/projects/{project['id']}/docs")
    assert docs_response.status_code == 200
    docs = docs_response.json()
    assert len(docs) == 2
    assert {item['doc_type_label'] for item in docs} == {'PRD', '技术方案'}

    filtered_response = client.get(f"/api/projects/{project['id']}/docs", params={'doc_type': 'tech_spec'})
    assert filtered_response.status_code == 200
    filtered_docs = filtered_response.json()
    assert len(filtered_docs) == 1
    assert filtered_docs[0]['doc_name'] == '技术方案草案_v0.1.md'
    assert filtered_docs[0]['doc_type_label'] == '技术方案'



def test_legacy_doc_type_mapping_is_compatible_in_list_response(client, db_session):
    project = create_project(client)

    legacy_doc = ProjectDoc(project_id=project['id'], doc_type='方案文档', doc_name='历史方案说明.md')
    db_session.add(legacy_doc)
    db_session.commit()

    docs_response = client.get(f"/api/projects/{project['id']}/docs")
    assert docs_response.status_code == 200
    docs = docs_response.json()
    assert len(docs) == 1
    assert docs[0]['doc_type'] == 'tech_spec'
    assert docs[0]['doc_type_label'] == '技术方案'



def test_doc_upload_returns_parse_status_and_generates_task_link_suggestion(client, db_session):
    project = create_project(client)
    task = Task(
        project_id=project['id'],
        title='输出结果面板字段定义',
        description='补齐结果面板字段定义并给研发确认',
        owner='Eric',
        status='in_progress',
    )
    db_session.add(task)
    db_session.commit()

    upload_response = upload_doc(
        client,
        project['id'],
        'result_fields.md',
        '字段定义',
        '# 结果面板字段定义\n需要补齐结果面板字段定义，并给研发确认状态口径。',
        title='结果面板字段定义_v0.1',
    )
    assert upload_response.status_code == 200
    upload_body = upload_response.json()
    assert upload_body['title'] == '结果面板字段定义_v0.1'
    assert upload_body['parse_status'] == 'completed'
    assert upload_body['parse_status_label'] == '已完成'
    assert upload_body['qa_enabled'] is True

    docs_response = client.get(f"/api/projects/{project['id']}/docs")
    assert docs_response.status_code == 200
    doc_item = docs_response.json()[0]
    assert doc_item['has_task_link_suggestion'] is True
    assert doc_item['task_link_suggestion_count'] == 1

    suggestions_response = client.get(f"/api/projects/{project['id']}/docs/{upload_body['doc_id']}/task-link-suggestions")
    assert suggestions_response.status_code == 200
    suggestion = suggestions_response.json()[0]
    assert suggestion['task_title'] == '输出结果面板字段定义'
    assert suggestion['current_status'] == 'in_progress'
    assert suggestion['current_status_label'] == '进行中'
    assert suggestion['suggested_status'] == 'pending_confirmation'
    assert suggestion['suggested_status_label'] == '待确认'



def test_confirm_task_link_updates_task_status_and_clears_pending_hint(client, db_session):
    project = create_project(client)
    task = Task(
        project_id=project['id'],
        title='输出结果面板字段定义',
        description='补齐结果面板字段定义并给研发确认',
        owner='Eric',
        status='in_progress',
    )
    db_session.add(task)
    db_session.commit()

    upload_response = upload_doc(
        client,
        project['id'],
        'result_fields.md',
        '字段定义',
        '# 结果面板字段定义\n需要补齐结果面板字段定义，并给研发确认状态口径。',
        title='结果面板字段定义_v0.1',
    )
    doc_id = upload_response.json()['doc_id']
    suggestion = client.get(f"/api/projects/{project['id']}/docs/{doc_id}/task-link-suggestions").json()[0]

    confirm_response = client.post(
        f"/api/projects/{project['id']}/docs/{doc_id}/task-link-suggestions/{suggestion['suggestion_id']}/confirm",
        json={'update_task_status': '待确认'},
    )
    assert confirm_response.status_code == 200
    confirm_body = confirm_response.json()
    assert confirm_body['suggestion_status'] == 'confirmed'
    assert confirm_body['suggestion_status_label'] == '已确认'
    assert confirm_body['task_status'] == 'pending_confirmation'
    assert confirm_body['task_status_label'] == '待确认'

    docs_response = client.get(f"/api/projects/{project['id']}/docs")
    assert docs_response.status_code == 200
    assert docs_response.json()[0]['has_task_link_suggestion'] is False
    assert docs_response.json()[0]['task_link_suggestion_count'] == 0

    tasks_response = client.get(f"/api/projects/{project['id']}/tasks")
    assert tasks_response.status_code == 200
    assert tasks_response.json()[0]['status'] == 'pending_confirmation'
    assert tasks_response.json()[0]['status_label'] == '待确认'



def test_ignore_task_link_hides_pending_hint(client, db_session):
    project = create_project(client)
    task = Task(
        project_id=project['id'],
        title='输出结果面板字段定义',
        description='补齐结果面板字段定义并给研发确认',
        owner='Eric',
        status='new',
    )
    db_session.add(task)
    db_session.commit()

    upload_response = upload_doc(
        client,
        project['id'],
        'result_fields.md',
        '字段定义',
        '# 结果面板字段定义\n需要补齐结果面板字段定义，并给研发确认状态口径。',
        title='结果面板字段定义_v0.1',
    )
    doc_id = upload_response.json()['doc_id']
    suggestion = client.get(f"/api/projects/{project['id']}/docs/{doc_id}/task-link-suggestions").json()[0]

    ignore_response = client.post(f"/api/projects/{project['id']}/docs/{doc_id}/task-link-suggestions/{suggestion['suggestion_id']}/ignore")
    assert ignore_response.status_code == 200
    ignore_body = ignore_response.json()
    assert ignore_body['suggestion_status'] == 'ignored'
    assert ignore_body['suggestion_status_label'] == '已忽略'

    docs_response = client.get(f"/api/projects/{project['id']}/docs")
    assert docs_response.status_code == 200
    assert docs_response.json()[0]['has_task_link_suggestion'] is False
    assert docs_response.json()[0]['task_link_suggestion_count'] == 0

    suggestions_response = client.get(f"/api/projects/{project['id']}/docs/{doc_id}/task-link-suggestions")
    assert suggestions_response.status_code == 200
    assert suggestions_response.json() == []



def test_meeting_upload_updates_tasks_and_docs_and_supports_export_and_qa(client):
    project = create_project(client)
    doc_upload = upload_doc(client, project['id'], 'prd.md', 'PRD', '# PRD\n当前需求范围是推荐模块海外发布。')
    assert doc_upload.status_code == 200
    doc_id = doc_upload.json()['doc_id']

    meeting_payload = {
        'title': '第 3 次需求对齐会',
        'meeting_date': '2026-04-04 16:00:00',
        'participants': ['Luna', 'Eric'],
        'utterances': [
            {'speaker': 'Luna', 'text': '今天决定 4 月下旬上线海外发布窗口。'},
            {'speaker': 'Eric', 'text': '我负责确认供应商回调字段，负责人Eric，截止 2026-04-10。'},
            {'speaker': 'Luna', 'text': '当前最大风险是法务条款尚未确认，存在延期风险。'},
            {'speaker': 'Eric', 'text': '这个需求范围有变化，需要同步更新 PRD。'},
        ],
    }
    upload_response = client.post(
        f"/api/projects/{project['id']}/meetings/upload",
        files={'file': ('meeting.json', json.dumps(meeting_payload, ensure_ascii=False).encode('utf-8'), 'application/json')},
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body['summary']
    assert len(body['decisions']) >= 1
    assert len(body['tasks']) >= 1
    assert len(body['risks']) >= 1
    assert len(body['updated_doc_versions']) >= 1
    assert body['updated_doc_versions'][0]['doc_type_label'] == 'PRD'

    meetings_response = client.get(f"/api/projects/{project['id']}/meetings")
    assert meetings_response.status_code == 200
    assert meetings_response.json()[0]['decision_count'] >= 1

    detail_response = client.get(f"/api/meetings/{body['meeting_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()['title'] == '第 3 次需求对齐会'

    tasks_response = client.get(f"/api/projects/{project['id']}/tasks")
    assert tasks_response.status_code == 200
    assert len(tasks_response.json()) >= 1

    task_summary = client.get(f"/api/projects/{project['id']}/tasks/summary")
    assert task_summary.status_code == 200
    assert task_summary.json()['total'] >= 1

    qa_response = client.post(f"/api/projects/{project['id']}/qa", json={'question': '这个需求目标和范围是什么？'})
    assert qa_response.status_code == 200
    qa_body = qa_response.json()
    assert qa_body['answer']
    assert len(qa_body['citations']) >= 1
    assert any(item.get('doc_type_label') == 'PRD' for item in qa_body['citations'])
    assert any('PRD /' in item['label'] for item in qa_body['citations'])

    qa_history = client.get(f"/api/projects/{project['id']}/qa/history")
    assert qa_history.status_code == 200
    assert len(qa_history.json()) == 1
    assert any(item.get('doc_type_label') == 'PRD' for item in qa_history.json()[0]['citations'])

    export_response = client.get(f"/api/projects/{project['id']}/export-summary")
    assert export_response.status_code == 200
    assert '第 3 次需求对齐会' in export_response.json()['content']

    version_list = client.get(f'/api/docs/{doc_id}/versions')
    assert version_list.status_code == 200
    assert len(version_list.json()) == 2


def test_meeting_upload_creates_new_tasks_as_in_progress(client):
    project = create_project(client, name='会议执行工作台 V1')
    meeting_payload = {
        'title': '范围对齐会',
        'meeting_date': '2026-04-04 10:00:00',
        'participants': ['Ava', 'Luna', 'Eric'],
        'utterances': [
            {'speaker': 'Ava', 'text': '今天先把 V1 范围收住。'},
            {'speaker': 'Luna', 'text': 'Luna 负责更新需求文档并准备字段草案。'},
            {'speaker': 'Eric', 'text': 'Eric 负责输出工作台页面框架。'},
        ],
    }
    upload_response = client.post(
        f"/api/projects/{project['id']}/meetings/upload",
        files={'file': ('meeting.json', json.dumps(meeting_payload, ensure_ascii=False).encode('utf-8'), 'application/json')},
    )
    assert upload_response.status_code == 200

    tasks_response = client.get(f"/api/projects/{project['id']}/tasks")
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    assert tasks
    assert all(item['status'] == 'in_progress' for item in tasks)
    assert all(item['status_label'] == '进行中' for item in tasks)




def test_later_meeting_updates_existing_task_without_relisting_it_in_current_meeting(client):
    project = create_project(client, name='会议执行工作台 V1')
    first_meeting_payload = {
        'title': '第一次范围对齐会',
        'meeting_date': '2026-04-01 10:00:00',
        'participants': ['Ava', 'Luna', 'Eric'],
        'utterances': [
            {'speaker': 'Luna', 'text': '我负责更新需求文档并准备字段草案。'},
            {'speaker': 'Eric', 'text': '我负责输出工作台页面框架。'},
        ],
    }
    first_upload = client.post(
        f"/api/projects/{project['id']}/meetings/upload",
        files={'file': ('meeting1.json', json.dumps(first_meeting_payload, ensure_ascii=False).encode('utf-8'), 'application/json')},
    )
    assert first_upload.status_code == 200
    first_body = first_upload.json()
    assert len(first_body['tasks']) >= 1

    tasks_response = client.get(f"/api/projects/{project['id']}/tasks")
    assert tasks_response.status_code == 200
    existing_task = tasks_response.json()[0]
    task_title = existing_task['title']

    second_meeting_payload = {
        'title': '第二次执行推进会',
        'meeting_date': '2026-04-03 16:00:00',
        'participants': ['Ava', 'Luna', 'Eric'],
        'utterances': [
            {'speaker': 'Ava', 'text': f'{task_title}这项工作继续推进，目前已在落实。'},
            {'speaker': 'Luna', 'text': f'{task_title}后续由我跟进，本周内同步最新进展。'},
        ],
    }
    second_upload = client.post(
        f"/api/projects/{project['id']}/meetings/upload",
        files={'file': ('meeting2.json', json.dumps(second_meeting_payload, ensure_ascii=False).encode('utf-8'), 'application/json')},
    )
    assert second_upload.status_code == 200
    second_body = second_upload.json()
    assert second_body['tasks'] == []

    second_detail = client.get(f"/api/meetings/{second_body['meeting_id']}")
    assert second_detail.status_code == 200
    assert second_detail.json()['tasks'] == []

    first_detail = client.get(f"/api/meetings/{first_body['meeting_id']}")
    assert first_detail.status_code == 200
    first_tasks = first_detail.json()['tasks']
    assert first_tasks
    assert any(item['title'] == task_title for item in first_tasks)

    refreshed_tasks = client.get(f"/api/projects/{project['id']}/tasks")
    assert refreshed_tasks.status_code == 200
    assert any(item['title'] == task_title and item['latest_update_meeting_title'] == '第二次执行推进会' for item in refreshed_tasks.json())

def test_doc_upload_matches_document_delivery_task_and_shows_pending_hint(client, db_session):
    project = create_project(client, name='会议执行工作台 V1')
    task = Task(
        project_id=project['id'],
        title='整理结果面板字段定义文档',
        description='请整理结果面板字段定义文档并上传到项目资料区',
        owner='Luna',
        status='in_progress',
    )
    db_session.add(task)
    db_session.commit()

    upload_response = upload_doc(
        client,
        project['id'],
        'result_fields_v0.1.md',
        '字段定义',
        '# 结果面板字段定义\n补齐结果面板字段定义，明确状态口径与展示字段。',
        title='结果面板字段定义_v0.1',
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body['has_task_link_suggestion'] is True
    assert body['task_link_suggestion_count'] == 1

    docs_response = client.get(f"/api/projects/{project['id']}/docs")
    assert docs_response.status_code == 200
    assert docs_response.json()[0]['has_task_link_suggestion'] is True

    suggestions_response = client.get(f"/api/projects/{project['id']}/docs/{body['doc_id']}/task-link-suggestions")
    assert suggestions_response.status_code == 200
    suggestions = suggestions_response.json()
    assert len(suggestions) == 1
    assert suggestions[0]['task_title'] == '整理结果面板字段定义文档'
    assert suggestions[0]['suggested_status'] == 'pending_confirmation'


def test_meeting_detail_only_shows_tasks_created_in_that_meeting(client):
    project = create_project(client, name='会议执行工作台 V1')

    first_meeting = {
        'title': '第一次范围对齐会',
        'meeting_date': '2026-04-01 10:00:00',
        'participants': ['Ava', 'Luna'],
        'utterances': [
            {'speaker': 'Luna', 'text': '我负责更新需求文档并准备字段草案。'},
        ],
    }
    first_response = client.post(
        f"/api/projects/{project['id']}/meetings/upload",
        files={'file': ('meeting-1.json', json.dumps(first_meeting, ensure_ascii=False).encode('utf-8'), 'application/json')},
    )
    assert first_response.status_code == 200
    first_meeting_id = first_response.json()['meeting_id']
    first_task_titles = [item['title'] for item in first_response.json()['tasks']]
    assert first_task_titles
    tracked_title = first_task_titles[0]

    second_meeting = {
        'title': '第二次执行推进会',
        'meeting_date': '2026-04-02 10:00:00',
        'participants': ['Ava', 'Luna'],
        'utterances': [
            {'speaker': 'Luna', 'text': f'{tracked_title}这项工作继续推进，我来跟进当前阶段进度。'},
            {'speaker': 'Ava', 'text': '原定方向不变，按当前排期继续推进。'},
        ],
    }
    second_response = client.post(
        f"/api/projects/{project['id']}/meetings/upload",
        files={'file': ('meeting-2.json', json.dumps(second_meeting, ensure_ascii=False).encode('utf-8'), 'application/json')},
    )
    assert second_response.status_code == 200
    second_task_titles = {item['title'] for item in second_response.json()['tasks']}
    assert tracked_title not in second_task_titles

    second_detail = client.get(f"/api/meetings/{second_response.json()['meeting_id']}")
    assert second_detail.status_code == 200
    second_detail_titles = {item['title'] for item in second_detail.json()['tasks']}
    assert tracked_title not in second_detail_titles

    first_detail = client.get(f"/api/meetings/{first_meeting_id}")
    assert first_detail.status_code == 200
    first_detail_titles = {item['title'] for item in first_detail.json()['tasks']}
    assert tracked_title in first_detail_titles
