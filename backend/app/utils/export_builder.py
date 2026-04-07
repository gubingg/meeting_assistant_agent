from __future__ import annotations

from datetime import datetime

from app.models import Meeting, Project


def build_project_summary_markdown(project: Project, meetings: list[Meeting]) -> str:
    lines = [
        f'# {project.name} 项目会议总结',
        '',
        f'- 导出时间：{datetime.utcnow().isoformat(timespec="seconds")}',
        f'- 项目负责人：{project.owner}',
        f'- 项目状态：{"已归档" if project.status == "archived" else "进行中"}',
        '',
    ]
    for meeting in meetings:
        lines.extend([
            f'## {meeting.title}',
            f'- 会议时间：{meeting.meeting_time.isoformat(sep=" ", timespec="minutes") if meeting.meeting_time else "未知"}',
            f'- 会议摘要：{meeting.summary or "无"}',
            '',
            '### 决策点',
        ])
        decisions = meeting.decisions_json or []
        if decisions:
            lines.extend(f"- {item.get('text', '')}" for item in decisions)
        else:
            lines.append('- 无')
        lines.extend(['', '### 待办项'])
        tasks = meeting.project.tasks if meeting.project else []
        meeting_tasks = [item for item in tasks if item.latest_update_meeting_id == meeting.id or item.source_meeting_id == meeting.id]
        if meeting_tasks:
            lines.extend(f"- {item.title} | 负责人：{item.owner or '未分配'} | 状态：{item.status}" for item in meeting_tasks)
        else:
            lines.append('- 无')
        lines.extend(['', '### 风险项'])
        risks = meeting.risks_json or []
        if risks:
            lines.extend(f"- {item.get('text', '')}" for item in risks)
        else:
            lines.append('- 无')
        lines.append('')
    return '\n'.join(lines).strip() + '\n'
