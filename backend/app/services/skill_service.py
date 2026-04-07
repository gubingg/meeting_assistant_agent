from __future__ import annotations

import json
from pathlib import Path


class SkillRegistry:
    PRIORITY = [
        'meeting_summary',
        'action_items',
        'decisions',
        'cross_meeting_memory',
        'project_doc_qa',
        'feishu_sync',
    ]

    def __init__(self, skills_root: str | None = None) -> None:
        default_root = Path(__file__).resolve().parents[2] / 'skills'
        self.skills_root = Path(skills_root) if skills_root is not None else default_root
        self._metadata_cache = self._load_metadata()

    def _load_metadata(self) -> dict[str, dict]:
        metadata: dict[str, dict] = {}
        if not self.skills_root.exists():
            return metadata
        for meta_path in self.skills_root.glob('*/meta.json'):
            payload = json.loads(meta_path.read_text(encoding='utf-8-sig'))
            metadata[payload['name']] = payload
        return metadata

    def list_metadata(self) -> dict[str, dict]:
        return self._metadata_cache

    def load_skill_content(self, skill_name: str) -> str:
        if skill_name == 'project_doc_qa':
            skill_name = 'cross_meeting_memory'
        return (self.skills_root / skill_name / 'SKILL.md').read_text(encoding='utf-8-sig')

    def classify_message(self, message: str) -> tuple[str, list[str]]:
        lowered = message.lower()
        matched: list[str] = []
        rules = {
            'meeting_summary': ['纪要', '总结', '整理', 'summary'],
            'action_items': ['待办', '行动项', '任务', 'todo', 'action'],
            'decisions': ['决策', '结论', '拍板', '分歧'],
            'cross_meeting_memory': ['上周', '以前', '历史', '冲突', '追溯'],
            'project_doc_qa': ['文档', 'prd', '方案', '周报', '需求'],
            'feishu_sync': ['飞书', '同步', '文档里', '表格'],
        }
        for intent, keywords in rules.items():
            if any(keyword in lowered for keyword in keywords):
                matched.append(intent)
        if not matched:
            matched = ['meeting_summary']
        ordered = [intent for intent in self.PRIORITY if intent in matched]
        if len(ordered) == 1:
            return ordered[0], ordered
        return 'mixed', ordered
