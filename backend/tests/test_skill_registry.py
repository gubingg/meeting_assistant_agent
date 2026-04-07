from app.services.skill_service import SkillRegistry


def test_skill_registry_classifies_mixed_without_forcing_feishu():
    registry = SkillRegistry('backend/skills')
    intent, sub_intents = registry.classify_message('帮我整理纪要并提取待办，再看看和上周有没有冲突')
    assert intent == 'mixed'
    assert sub_intents == ['meeting_summary', 'action_items', 'cross_meeting_memory']
    assert 'feishu_sync' not in sub_intents


def test_skill_registry_project_doc_qa_is_detected():
    registry = SkillRegistry('backend/skills')
    intent, sub_intents = registry.classify_message('查一下 PRD 里怎么说')
    assert intent in {'project_doc_qa', 'mixed'}
    assert 'project_doc_qa' in sub_intents

