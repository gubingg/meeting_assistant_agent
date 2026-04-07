from __future__ import annotations

from pathlib import Path

_PROMPT_FILE = Path(__file__).resolve().parents[2] / 'prompt_sections_dump.txt'
_PROMPT_TEXT = _PROMPT_FILE.read_text(encoding='utf-8')


def _extract_section(heading: str) -> str:
    lines = _PROMPT_TEXT.splitlines(keepends=True)
    markers: list[tuple[str, int]] = []
    position = 0
    for line in lines:
        stripped = line.rstrip('\r\n')
        if stripped.startswith('##') or stripped.startswith('###'):
            markers.append((stripped, position))
        position += len(line)

    current_position = next(pos for title, pos in markers if title == heading)
    start = current_position + len(heading)
    later_positions = [pos for _, pos in markers if pos > current_position]
    end = min(later_positions) if later_positions else len(_PROMPT_TEXT)
    return _PROMPT_TEXT[start:end].strip()


MEETING_PLANNER_SYSTEM_PROMPT = _extract_section('### 1.1 System Prompt')
MEETING_PLANNER_USER_PROMPT_TEMPLATE = _extract_section('### 1.2 User Prompt')
MEETING_ANALYST_SYSTEM_PROMPT = _extract_section('### 2.1 System Prompt')
MEETING_ANALYST_USER_PROMPT_TEMPLATE = _extract_section('### 2.2 User Prompt')
TASK_CONTINUITY_SYSTEM_PROMPT = _extract_section('### 3.1 System Prompt')
TASK_CONTINUITY_USER_PROMPT_TEMPLATE = _extract_section('### 3.2 User Prompt')
PROJECT_DOC_UPDATE_SYSTEM_PROMPT = _extract_section('### 4.1 System Prompt')
PROJECT_DOC_UPDATE_USER_PROMPT_TEMPLATE = _extract_section('### 4.2 User Prompt 模板')
PROJECT_QA_SYSTEM_PROMPT = _extract_section('### 5.1 System Prompt')
PROJECT_QA_USER_PROMPT_TEMPLATE = _extract_section('### 5.2 User Prompt ')
