from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser as date_parser


@dataclass
class UtterancePayload:
    speaker: str
    text: str
    turn_index: int
    start_time_sec: int | None = None
    end_time_sec: int | None = None


@dataclass
class ParsedTranscript:
    title: str
    meeting_date: datetime | None
    participants: list[str]
    utterances: list[UtterancePayload]


@dataclass
class ParsedDocument:
    title: str
    paragraphs: list[str]


TIME_RE = re.compile(r'^(?:(\d{2}):)?(\d{2}):(\d{2})$')
LINE_RE = re.compile(r'^\[(?P<speaker>[^\]]+)\]\s*(?P<text>.+)$')


def parse_time_to_seconds(raw: str | None) -> int | None:
    if not raw:
        return None
    match = TIME_RE.match(raw.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def _safe_parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return date_parser.parse(raw)
    except (ValueError, TypeError):
        return None


def _parse_standard_utterances(payload: dict[str, Any]) -> list[UtterancePayload]:
    utterances: list[UtterancePayload] = []
    for index, item in enumerate(payload.get('utterances', [])):
        utterances.append(
            UtterancePayload(
                speaker=item.get('speaker') or f'Speaker_{index + 1}',
                text=(item.get('text') or '').strip(),
                turn_index=index,
                start_time_sec=parse_time_to_seconds(item.get('start_time')),
                end_time_sec=parse_time_to_seconds(item.get('end_time')),
            )
        )
    return [item for item in utterances if item.text]


def _parse_context_speaker_payload(payload: dict[str, Any]) -> list[UtterancePayload]:
    utterances: list[UtterancePayload] = []
    groups = payload.get('context') or []
    speakers = payload.get('speaker') or []
    turn_index = 0
    for group_index, group in enumerate(groups):
        speaker_id = speakers[group_index] if group_index < len(speakers) else group_index + 1
        speaker = f'Speaker_{speaker_id}'
        if not isinstance(group, list):
            continue
        for item in group:
            text = str(item).strip()
            if not text:
                continue
            utterances.append(UtterancePayload(speaker=speaker, text=text, turn_index=turn_index))
            turn_index += 1
    return utterances


def _parse_json_payload(payload: dict[str, Any], fallback_title: str) -> ParsedTranscript:
    if payload.get('utterances'):
        utterances = _parse_standard_utterances(payload)
    elif payload.get('context') and payload.get('speaker'):
        utterances = _parse_context_speaker_payload(payload)
    else:
        utterances = []
    participants = list(payload.get('participants') or [])
    if not participants:
        participants = list(dict.fromkeys(item.speaker for item in utterances))
    return ParsedTranscript(
        title=payload.get('title') or fallback_title,
        meeting_date=_safe_parse_date(payload.get('meeting_date')),
        participants=participants,
        utterances=utterances,
    )


def _parse_text_lines(text: str, fallback_title: str) -> ParsedTranscript:
    utterances: list[UtterancePayload] = []
    anonymous_index = 1
    for turn_index, raw_line in enumerate(line for line in text.splitlines() if line.strip()):
        match = LINE_RE.match(raw_line.strip())
        if match:
            speaker = match.group('speaker').strip()
            content = match.group('text').strip()
        else:
            speaker = f'Speaker_{anonymous_index}'
            content = raw_line.strip()
            anonymous_index += 1
        utterances.append(UtterancePayload(speaker=speaker, text=content, turn_index=turn_index))
    return ParsedTranscript(title=fallback_title, meeting_date=None, participants=[], utterances=utterances)


def parse_transcript(file_name: str, content: bytes, title_override: str | None = None, meeting_date_override: str | None = None) -> ParsedTranscript:
    suffix = Path(file_name).suffix.lower()
    fallback_title = title_override or Path(file_name).stem or '未命名会议'
    raw_text = content.decode('utf-8', errors='ignore')

    if suffix == '.json':
        parsed = _parse_json_payload(json.loads(raw_text), fallback_title)
    else:
        parsed = _parse_text_lines(raw_text, fallback_title)

    if title_override:
        parsed.title = title_override
    if meeting_date_override:
        parsed.meeting_date = _safe_parse_date(meeting_date_override)
    return parsed


def parse_reference_document(file_name: str, content: bytes) -> ParsedDocument:
    suffix = Path(file_name).suffix.lower()
    raw_text = content.decode('utf-8', errors='ignore')
    if suffix == '.json':
        payload = json.loads(raw_text)
        if 'utterances' in payload or ('context' in payload and 'speaker' in payload):
            transcript = _parse_json_payload(payload, Path(file_name).stem)
            paragraphs = [f'[{item.speaker}] {item.text}' for item in transcript.utterances]
            return ParsedDocument(title=transcript.title, paragraphs=paragraphs)
    paragraphs = [part.strip() for part in re.split(r'\n\s*\n', raw_text) if part.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return ParsedDocument(title=Path(file_name).stem, paragraphs=paragraphs)
